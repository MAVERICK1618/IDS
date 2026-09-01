"""
Port-Scan Detection Pipeline (Clean Victims Only)
=================================================
Works on live-traffic.csv even when heuristic finds 0 scans.
Falls back to Isolation Forest anomalies.

Output:
  - processed/port-scan-predictions.csv
  - alerts/port-scan-alert.json
"""

import sys
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.utils import resample
import joblib

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

if len(sys.argv) > 1:
    CSV_PATH = Path(sys.argv[1])
else:
    CSV_PATH = BASE_DIR / "data" / "live-traffic.csv"

MODEL_DIR = BASE_DIR / "models"
PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"

for d in (MODEL_DIR, PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.30
MEMORY_DECAY = 0.95

# Alert thresholds (tune if needed)
MIN_UNIQUE_PORTS = 15          # lowered for smaller captures
MIN_SCAN_FLOWS = 10
MAX_VICTIMS = 10
MIN_FLOWS_PER_VICTIM = 5

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("[+] Loading data...")
df = pd.read_csv(CSV_PATH, low_memory=False)
df.columns = df.columns.str.strip()

REQUIRED = [
    "Source IP", "Destination IP", "Source Port", "Destination Port",
    "Protocol", "Flow Duration",
    "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "SYN Flag Count", "ACK Flag Count", "FIN Flag Count", "RST Flag Count",
    "PSH Flag Count", "URG Flag Count",
    "Flow Bytes/s", "Flow Packets/s",
    "Fwd Packets/s", "Bwd Packets/s",
    "Packet Length Mean", "Packet Length Std",
    "Down/Up Ratio", "Average Packet Size",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward",
    "Active Mean", "Idle Mean",
]

missing = [c for c in REQUIRED if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(subset=REQUIRED, inplace=True)
df.reset_index(drop=True, inplace=True)
print(f"[+] Loaded {len(df):,} flows")

# ---------------------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------------------
print("[+] Engineering features...")
df["syn_ack_ratio"] = df["SYN Flag Count"] / (df["ACK Flag Count"] + 1)
df["fwd_bwd_pkt_ratio"] = df["Total Fwd Packets"] / (df["Total Backward Packets"] + 1)
df["fwd_bwd_byte_ratio"] = df["Total Length of Fwd Packets"] / (df["Total Length of Bwd Packets"] + 1)
df["packets_per_second"] = df["Flow Packets/s"]
df["bytes_per_second"] = df["Flow Bytes/s"]
df["is_syn_heavy"] = ((df["SYN Flag Count"] > 0) & (df["ACK Flag Count"] == 0)).astype(int)

# Live traffic duration is usually in seconds, not microseconds
dur = df["Flow Duration"]
df["short_flow"] = (dur < 1.0).astype(int)          # < 1 second
df["few_packets"] = ((df["Total Fwd Packets"] + df["Total Backward Packets"]) <= 3).astype(int)
df["small_payload"] = (
    (df["Total Length of Fwd Packets"] + df["Total Length of Bwd Packets"]) < 100
).astype(int)

FEATURE_COLS = [
    "Flow Duration",
    "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "SYN Flag Count", "ACK Flag Count", "FIN Flag Count", "RST Flag Count",
    "PSH Flag Count", "URG Flag Count",
    "Flow Bytes/s", "Flow Packets/s",
    "Fwd Packets/s", "Bwd Packets/s",
    "Packet Length Mean", "Packet Length Std",
    "Down/Up Ratio", "Average Packet Size",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward",
    "Active Mean", "Idle Mean",
    "syn_ack_ratio", "fwd_bwd_pkt_ratio", "fwd_bwd_byte_ratio",
    "packets_per_second", "bytes_per_second",
    "is_syn_heavy", "short_flow", "few_packets", "small_payload",
]

X = df[FEATURE_COLS].astype(np.float32)

# ---------------------------------------------------------------------------
# 3. Heuristic labeling (softer for live traffic)
# ---------------------------------------------------------------------------
def heuristic_label(row):
    score = 0
    if row["is_syn_heavy"] or (row["SYN Flag Count"] >= 1 and row["ACK Flag Count"] == 0):
        score += 2
    if row["short_flow"]:
        score += 1
    if row["few_packets"]:
        score += 1
    if row["small_payload"]:
        score += 1
    if row["Flow Packets/s"] > 20:          # lowered from 80
        score += 1
    if row["fwd_bwd_pkt_ratio"] > 4:        # lowered from 8
        score += 1
    return 1 if score >= 4 else 0           # lowered from 5

df["is_scan"] = df.apply(heuristic_label, axis=1)
y = df["is_scan"].values
print(f"[+] Heuristic labels → Scan: {int(y.sum()):,} | Benign: {int((y == 0).sum()):,}")

# ---------------------------------------------------------------------------
# 4. Scale
# ---------------------------------------------------------------------------
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

# ---------------------------------------------------------------------------
# 5. Isolation Forest
# ---------------------------------------------------------------------------
print("[+] Training Isolation Forest...")
# Train on all data if no benign, else on benign
if (y == 0).sum() > 10:
    X_train_iso = X_scaled[y == 0]
else:
    X_train_iso = X_scaled

iso = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
iso.fit(X_train_iso)

anomaly_score = -iso.decision_function(X_scaled)
ae_thr = np.percentile(anomaly_score, 95)
ae_flag = (anomaly_score > ae_thr).astype(int)
print(f"[+] Anomaly threshold: {ae_thr:.4f} | Flagged: {int(ae_flag.sum()):,}")

# If heuristic found nothing, use Isolation Forest flags as labels
if y.sum() == 0:
    print("[!] No heuristic scans — using Isolation Forest flags as labels")
    y = ae_flag.copy()
    df["is_scan"] = y

# ---------------------------------------------------------------------------
# 6. Long-term memory features
# ---------------------------------------------------------------------------
print("[+] Building long-term memory features...")
memory = defaultdict(lambda: {"acc_anom": 0.0, "unique_dports": set(), "scan_count": 0})
long_term = []

for i, row in df.iterrows():
    src = row["Source IP"]
    memory[src]["acc_anom"] *= MEMORY_DECAY
    if ae_flag[i]:
        memory[src]["acc_anom"] += anomaly_score[i]
        memory[src]["unique_dports"].add(row["Destination Port"])
        memory[src]["scan_count"] += 1
    long_term.append([
        ae_flag[i],
        memory[src]["acc_anom"],
        len(memory[src]["unique_dports"]),
        memory[src]["scan_count"],
    ])

X_stage2 = np.array(long_term, dtype=np.float32)

# ---------------------------------------------------------------------------
# 7. Train classifier (skip safely if still no positives)
# ---------------------------------------------------------------------------
use_clf = True
if y.sum() == 0:
    print("[!] Still no positive samples — using anomaly flags only")
    use_clf = False
    df["predicted_scan"] = ae_flag
else:
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X_stage2, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
        )
    except ValueError:
        # stratify fails if one class too small
        X_train, X_test, y_train, y_test = train_test_split(
            X_stage2, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
        )

    pos = X_train[y_train == 1]
    neg = X_train[y_train == 0]

    if len(pos) == 0:
        print("[!] No positive samples in train set — using anomaly flags only")
        use_clf = False
        df["predicted_scan"] = ae_flag
    else:
        n_neg = max(len(pos), 1)
        neg_up = resample(neg, replace=True, n_samples=n_neg, random_state=RANDOM_STATE)
        X_train_bal = np.vstack([pos, neg_up])
        y_train_bal = np.array([1] * len(pos) + [0] * len(neg_up))
        print(f"[+] Balanced train size: {len(X_train_bal)} (scan={len(pos)})")

        print("[+] Training RandomForest...")
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        clf.fit(X_train_bal, y_train_bal)

        # save model
        bundle = {
            "feature_cols": FEATURE_COLS,
            "scaler": scaler,
            "isolation_forest": iso,
            "ae_threshold": ae_thr,
            "classifier": clf,
            "memory_decay": MEMORY_DECAY,
        }
        model_path = MODEL_DIR / "port_scan_detector.pkl"
        joblib.dump(bundle, model_path)
        print(f"[+] Model saved → {model_path}")

        df["predicted_scan"] = clf.predict(X_stage2)

# ---------------------------------------------------------------------------
# 8. Alerts + predictions
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(" PORT SCAN ALERTS (High Confidence + Clean Victims)")
print("=" * 70)

scan_df = df[df["predicted_scan"] == 1].copy()
alerts = []
pred_rows = []
now = datetime.now(timezone.utc).isoformat()
seen_pairs = set()
seen_pred = set()

if len(scan_df) == 0:
    print("[+] No port-scan activity detected.")
else:
    high_conf_alerts = []

    for attacker_ip, group in scan_df.groupby("Source IP"):
        unique_ports = group["Destination Port"].nunique()
        total_flows = len(group)

        if unique_ports < MIN_UNIQUE_PORTS or total_flows < MIN_SCAN_FLOWS:
            continue

        victim_counts = group["Destination IP"].value_counts()
        real_victims = victim_counts[victim_counts >= MIN_FLOWS_PER_VICTIM].index.tolist()

        if len(real_victims) == 0 or len(real_victims) > MAX_VICTIMS:
            continue

        high_conf_alerts.append({
            "Attacker": attacker_ip,
            "Victims": sorted(real_victims),
            "Unique_Ports": unique_ports,
            "Scan_Flows": total_flows,
            "group": group,
        })

    if not high_conf_alerts:
        print("[+] No high-confidence port scans found.")
    else:
        high_conf_alerts = sorted(
            high_conf_alerts, key=lambda x: x["Unique_Ports"], reverse=True
        )
        print(f"\n[+] Detected {len(high_conf_alerts)} high-confidence attacker(s):\n")

        for alert in high_conf_alerts:
            attacker = str(alert["Attacker"])
            group = alert["group"]

            for victim in alert["Victims"]:
                pair_key = (attacker, str(victim))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    alert_text = (
                        f"ALERT [Port-Scan] attacker_ip: [{attacker}] "
                        f"host_compromised: [{victim}]"
                    )
                    print(alert_text)
                    alerts.append({
                        "timestamp": now,
                        "alert_type": "PORT_SCAN",
                        "message": alert_text,
                        "attacker_ip": attacker,
                        "host_compromised": str(victim),
                    })

                victim_flows = group[group["Destination IP"] == victim]
                for port in sorted(victim_flows["Destination Port"].unique()):
                    pred_key = (attacker, str(victim), int(port))
                    if pred_key in seen_pred:
                        continue
                    seen_pred.add(pred_key)
                    pred_rows.append({
                        "timestamp": now,
                        "src_ip": attacker,
                        "dst_ip": str(victim),
                        "port": int(port),
                        "label": "PORT_SCAN",
                    })

# ---------- predictions ----------
pred_path = PROCESSED_DIR / "port-scan-predictions.csv"
if pred_rows:
    pd.DataFrame(pred_rows).to_csv(pred_path, index=False)
    print(f"\n[+] Saved predictions: {pred_path}  ({len(pred_rows)} rows)")
else:
    pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"]).to_csv(
        pred_path, index=False
    )
    print("\n[+] Empty port-scan-predictions.csv written")

# ---------- alert JSON ----------
alert_path = ALERTS_DIR / "port-scan-alert.json"
with open(alert_path, "w", encoding="utf-8") as f:
    json.dump(alerts, f, indent=2)
print(f"[+] Saved single alert file: {alert_path}  ({len(alerts)} alert(s))")

print("\n" + "=" * 70)
print(" SUMMARY")
print("=" * 70)
print(f"  Total flows          : {len(df):,}")
print(f"  Predicted scan flows : {int(df['predicted_scan'].sum()):,}")
print(f"  Alerts generated     : {len(alerts)}")
print(f"  predictions rows     : {len(pred_rows)}")
print(f"  predictions file     : {pred_path}")
print(f"  Alert file           : {alert_path}")
print("=" * 70)
print("[+] Pipeline finished.")