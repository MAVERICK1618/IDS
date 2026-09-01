"""
Lateral Movement Detection (live, no pickle required)
=====================================================
Trains Isolation Forest on the incoming traffic, then keeps only
SSH / internal lateral-movement style anomalies.

Output:
  - processed/lateral-movement-predictions.csv
  - alerts/lateral-movement-alert.json
"""

import sys
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

if len(sys.argv) > 1:
    DATA_PATH = Path(sys.argv[1])
else:
    DATA_PATH = BASE_DIR / "data" / "live-traffic.csv"

PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"
for d in (PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

CONTAMINATION = 0.05
N_ESTIMATORS = 150
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("=" * 60)
print(" LATERAL MOVEMENT DETECTION (live)")
print("=" * 60)

if not DATA_PATH.is_file():
    raise FileNotFoundError(f"Input CSV not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH, low_memory=False)
df.columns = df.columns.str.strip()

# Map common name variants from live-traffic CSV
rename_map = {
    "source ip": "Source IP",
    "destination ip": "Destination IP",
    "source port": "Source Port",
    "destination port": "Destination Port",
    "flow duration": "Flow Duration",
    "total fwd packets": "Total Fwd Packets",
    "total backward packets": "Total Backward Packets",
    "total length of fwd packets": "Total Length of Fwd Packets",
    "total length of bwd packets": "Total Length of Bwd Packets",
    "flow bytes/s": "Flow Bytes/s",
    "flow packets/s": "Flow Packets/s",
    "flow iat mean": "Flow IAT Mean",
    "flow iat std": "Flow IAT Std",
    "packet length mean": "Packet Length Mean",
    "syn flag count": "SYN Flag Count",
}
# only rename if lower-case version exists
lower_cols = {c.lower(): c for c in df.columns}
for low, canon in rename_map.items():
    if low in lower_cols and canon not in df.columns:
        df = df.rename(columns={lower_cols[low]: canon})

for col in ("Source IP", "Destination IP", "Destination Port"):
    if col not in df.columns:
        raise ValueError(f"Required column missing: {col}")

src_ips = df["Source IP"].astype(str)
dst_ips = df["Destination IP"].astype(str)
dst_ports = pd.to_numeric(df["Destination Port"], errors="coerce").fillna(0).astype(int)

num_df = df.select_dtypes(include=[np.number]).copy()
num_df = num_df.replace([np.inf, -np.inf], np.nan).fillna(0)

# Engineered features
iat_mean = num_df.get("Flow IAT Mean", pd.Series(0, index=num_df.index)).astype(float)
iat_std = num_df.get("Flow IAT Std", pd.Series(0, index=num_df.index)).astype(float)
fwd_bytes = num_df.get("Total Length of Fwd Packets", pd.Series(0, index=num_df.index)).astype(float)
bwd_bytes = num_df.get("Total Length of Bwd Packets", pd.Series(0, index=num_df.index)).astype(float)
flow_bytes_s = num_df.get("Flow Bytes/s", pd.Series(0, index=num_df.index)).astype(float)
flow_pkts_s = num_df.get("Flow Packets/s", pd.Series(0, index=num_df.index)).astype(float)
total_fwd = num_df.get("Total Fwd Packets", pd.Series(0, index=num_df.index)).astype(float)
syn_count = num_df.get("SYN Flag Count", pd.Series(0, index=num_df.index)).astype(float)
flow_duration = num_df.get("Flow Duration", pd.Series(0, index=num_df.index)).astype(float)
pkt_len_mean = num_df.get("Packet Length Mean", pd.Series(0, index=num_df.index)).astype(float)

num_df["jitter"] = iat_std / (iat_mean + 1e-9)
num_df["byte_ratio"] = fwd_bytes / (fwd_bytes + bwd_bytes + 1e-9)
num_df["packet_rate_ratio"] = flow_pkts_s / (flow_bytes_s + 1e-9)
num_df["is_ssh"] = (dst_ports == 22).astype(int)
num_df["syn_ratio"] = syn_count / (total_fwd + 1e-9)

num_df["Source IP"] = src_ips.values
num_df["Destination IP"] = dst_ips.values
num_df["Destination Port"] = dst_ports.values

print(f"[+] Data loaded: {len(df)} flows")

# ---------------------------------------------------------------------------
# Isolation Forest (train on the fly)
# ---------------------------------------------------------------------------
feature_cols = [
    "Flow Duration", "Flow IAT Mean", "Flow IAT Std",
    "Packet Length Mean", "Flow Bytes/s", "Flow Packets/s",
    "Total Fwd Packets", "Total Backward Packets",
    "jitter", "byte_ratio", "packet_rate_ratio",
    "is_ssh", "syn_ratio",
]
# keep only columns that exist
feature_cols = [c for c in feature_cols if c in num_df.columns]
if len(feature_cols) < 3:
    raise ValueError(f"Too few usable features: {feature_cols}")

X = num_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0).values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iso = IsolationForest(
    n_estimators=N_ESTIMATORS,
    contamination=CONTAMINATION,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
iso.fit(X_scaled)

preds = iso.predict(X_scaled)
scores = iso.score_samples(X_scaled)

num_df["anomaly"] = (preds == -1).astype(int)
num_df["anomaly_score"] = scores.round(6)

print(f"[+] Isolation Forest done — anomalies: {int(num_df['anomaly'].sum())}")

# ---------------------------------------------------------------------------
# Keep ONLY lateral-movement candidates
# ---------------------------------------------------------------------------
malicious = num_df[num_df["anomaly"] == 1].copy()

lateral = malicious[
    (malicious["Destination Port"] == 22) |
    (malicious["is_ssh"] == 1) |
    (malicious["syn_ratio"] > 0.5)
].copy()

print(f"[+] Lateral-movement candidates after filter: {len(lateral)}")

# ---------------------------------------------------------------------------
# Alerts (deduplicated by src → dst)
# ---------------------------------------------------------------------------
alert_dict = {}
for _, row in lateral.iterrows():
    src = str(row["Source IP"])
    dst = str(row["Destination IP"])
    port = int(row["Destination Port"])
    key = (src, dst)
    if key not in alert_dict:
        alert_dict[key] = {
            "count": 0,
            "score": float(row["anomaly_score"]),
            "port": port,
        }
    alert_dict[key]["count"] += 1
    alert_dict[key]["score"] = min(alert_dict[key]["score"], float(row["anomaly_score"]))

now = datetime.now(timezone.utc).isoformat()
alerts = []
pred_rows = []

print()
for (src, dst), info in sorted(
    alert_dict.items(), key=lambda x: x[1]["count"], reverse=True
):
    alert_text = (
        f"ALERT [lateral-movement] "
        f"attacker_ip: [{src}] "
        f"host_compromised: [{dst}]"
    )
    print(alert_text)
    print(f"  Suspicious flows: {info['count']} | Score: {info['score']:.4f}")
    print()

    alerts.append({
        "timestamp": now,
        "alert_type": "LATERAL_MOVEMENT",
        "message": alert_text,
        "attacker_ip": src,
        "host_compromised": dst,
    })
    pred_rows.append({
        "timestamp": now,
        "src_ip": src,
        "dst_ip": dst,
        "port": info["port"],
        "label": "LATERAL_MOVEMENT",
    })

if not alerts:
    print("[+] No lateral-movement activity detected in this capture!")

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------
pred_path = PROCESSED_DIR / "lateral-movement-predictions.csv"
if pred_rows:
    pd.DataFrame(pred_rows).to_csv(pred_path, index=False)
    print(f"[+] Saved predictions: {pred_path}  ({len(pred_rows)} rows)")
else:
    pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"]).to_csv(
        pred_path, index=False
    )
    print("[+] Empty predictions.csv written")

alert_path = ALERTS_DIR / "lateral-movement-alert.json"
with open(alert_path, "w", encoding="utf-8") as f:
    json.dump(alerts, f, indent=2)
print(f"[+] Saved single alert file: {alert_path}  ({len(alerts)} alert(s))")

print("\n" + "=" * 60)
print(" SUMMARY")
print("=" * 60)
print(f"  Total flows              : {len(df)}")
print(f"  Isolation anomalies      : {int(num_df['anomaly'].sum())}")
print(f"  Lateral-movement alerts  : {len(alerts)}")
print(f"  predictions.csv          : {pred_path}")
print(f"  Alert file               : {alert_path}")
print("=" * 60)