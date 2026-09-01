"""
C2 / Reverse-Shell Detection (Isolation Forest + XGBoost)
=========================================================
Fixed: no more shape-mismatch crash in cross_val_predict.
Faster for live traffic.

Output:
  - processed/c2-predictions.csv  → one row per detected C2 flow
  - alerts/c2-alert.json          → single alert file
"""

from io import StringIO
from pathlib import Path
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"

for d in (DATA_DIR, PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

# Accept CSV from command line (live monitor passes it)
if len(sys.argv) > 1:
    SOURCE_FILE = Path(sys.argv[1])
else:
    SOURCE_FILE = DATA_DIR / "live-traffic.csv"

C2_PORT = 4444
SSH_PORT = 22
CONFIDENCE_THRESHOLD = 0.7

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_dataset(path=SOURCE_FILE):
    if not Path(path).is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    # Try normal read first; fall back to quoted-line cleaning
    try:
        df = pd.read_csv(path, low_memory=False)
        if len(df.columns) > 3:
            return df
    except Exception:
        pass

    lines = Path(path).read_text(encoding="utf-8-sig").splitlines(keepends=True)
    cleaned = []
    for line in lines:
        ending = "\n" if line.endswith("\n") else ""
        body = line[:-1] if ending else line
        if len(body) >= 2 and body.startswith('"') and body.endswith('"'):
            body = body[1:-1]
        cleaned.append(body + ending)
    return pd.read_csv(StringIO("".join(cleaned)))

# ---------------------------------------------------------------------------
# SSH features
# ---------------------------------------------------------------------------
def prepare_ssh_features(df):
    df.columns = df.columns.str.strip()
    ssh = df[
        (df["Destination Port"] == SSH_PORT) | (df["Source Port"] == SSH_PORT)
    ].copy()
    ssh = ssh.reset_index(drop=True)

    if ssh.empty:
        return ssh, pd.DataFrame()

    identifier_cols = [
        "Source IP", "Destination IP", "Source Port", "Destination Port", "Protocol"
    ]
    feature_cols = [c for c in ssh.columns if c not in identifier_cols]
    X = ssh[feature_cols].apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)
    return ssh, X

# ---------------------------------------------------------------------------
# Isolation Forest labels
# ---------------------------------------------------------------------------
def isolation_forest_labels(X):
    if X.empty or len(X) < 5:
        return np.zeros(len(X), dtype=int), np.zeros(len(X))

    scaled = StandardScaler().fit_transform(X)
    iso = IsolationForest(
        n_estimators=100,          # faster for live
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(scaled)

    raw_score = -iso.score_samples(scaled)
    median = np.median(raw_score)
    mad = np.median(np.abs(raw_score - median)) or 1e-6
    anomaly_score = 1 / (1 + np.exp(-(raw_score - median) / (2 * mad)))
    labels = np.where(anomaly_score > 0.5, 1, 0)
    return labels, anomaly_score

# ---------------------------------------------------------------------------
# XGBoost — FIXED (no cross_val_predict)
# ---------------------------------------------------------------------------
def train_xgboost(X, y):
    """
    Fit XGBoost on Isolation-Forest labels and return
    in-sample attack probabilities. Avoids the CV shape bug.
    """
    y = np.asarray(y).astype(int)

    # Not enough classes or samples → fall back to Isolation Forest scores
    if len(set(y)) < 2 or len(y) < 10:
        print("[!] Too few classes/samples for XGBoost — using Isolation Forest scores")
        return None, y.astype(float)

    model = XGBClassifier(
        n_estimators=80,           # lighter for live traffic
        max_depth=3,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=42,
        n_jobs=2,
        verbosity=0,
    )
    model.fit(X, y)

    # In-sample probabilities (class 1 = Attack)
    try:
        proba = model.predict_proba(X)[:, 1]
    except Exception:
        # Safety: if only one class somehow remains
        proba = y.astype(float)

    return model, proba

# ---------------------------------------------------------------------------
# Attackers
# ---------------------------------------------------------------------------
def find_attackers(ssh_df, confidence):
    ssh_df = ssh_df.copy()
    ssh_df["attack_confidence"] = confidence
    flagged = ssh_df[ssh_df["attack_confidence"] >= CONFIDENCE_THRESHOLD]
    attacker_ips = set(flagged["Source IP"].astype(str).unique())
    return attacker_ips, flagged

# ---------------------------------------------------------------------------
# C2 flows
# ---------------------------------------------------------------------------
def find_c2_flows(df):
    df.columns = df.columns.str.strip()
    return df[df["Destination Port"] == C2_PORT]

# ---------------------------------------------------------------------------
# Correlate + alerts + predictions
# ---------------------------------------------------------------------------
def correlate_and_alert(df, attacker_ips, flagged_ssh):
    c2_flows = find_c2_flows(df)
    alerts = []
    pred_rows = []
    seen = set()

    if not attacker_ips:
        print("[+] No SSH brute-force attackers detected.")
    if c2_flows.empty:
        print("[+] No C2/reverse-shell (port 4444) traffic detected.")

    now = datetime.now(timezone.utc).isoformat()

    for attacker_ip in attacker_ips:
        victims = flagged_ssh[
            flagged_ssh["Source IP"].astype(str) == str(attacker_ip)
        ]["Destination IP"].unique()

        for victim_ip in victims:
            # Reverse-shell: victim → attacker on C2 port
            reverse_shell = c2_flows[
                (c2_flows["Source IP"].astype(str) == str(victim_ip)) &
                (c2_flows["Destination IP"].astype(str) == str(attacker_ip))
            ]

            if reverse_shell.empty:
                continue

            key = (str(attacker_ip), str(victim_ip))
            if key not in seen:
                seen.add(key)
                alert_text = (
                    f"ALERT [C2] attacker_ip: [{attacker_ip}] "
                    f"host_compromised: [{victim_ip}]"
                )
                print(alert_text)
                alerts.append({
                    "timestamp": now,
                    "alert_type": "C2",
                    "message": alert_text,
                    "attacker_ip": str(attacker_ip),
                    "host_compromised": str(victim_ip),
                })

            for _, flow in reverse_shell.iterrows():
                pred_rows.append({
                    "timestamp": now,
                    "src_ip": str(flow["Source IP"]),
                    "dst_ip": str(flow["Destination IP"]),
                    "port": int(flow["Destination Port"]),
                    "label": "C2",
                })

    # predictions
    pred_path = PROCESSED_DIR / "c2-predictions.csv"
    if pred_rows:
        pd.DataFrame(pred_rows).to_csv(pred_path, index=False)
        print(f"[+] Saved predictions (C2 only): {pred_path}  ({len(pred_rows)} rows)")
    else:
        pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"]).to_csv(
            pred_path, index=False
        )
        print("[+] No C2 detections — empty predictions.csv written")

    # single alert file
    alert_path = ALERTS_DIR / "c2-alert.json"
    with open(alert_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)
    print(f"[+] Saved single alert file: {alert_path}  ({len(alerts)} alert(s))")

    return alerts

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(" C2 / REVERSE-SHELL DETECTION (Isolation Forest + XGBoost)")
    print("=" * 60)

    data = load_dataset()
    print(f"[+] Loaded {len(data)} flows from {SOURCE_FILE}")

    ssh_df, X = prepare_ssh_features(data)
    print(f"[+] SSH flows: {len(ssh_df)}")

    if ssh_df.empty or X.empty:
        print("[!] No SSH traffic found — skipping C2 correlation.")
        # still write empty outputs
        (PROCESSED_DIR / "c2-predictions.csv").write_text(
            "timestamp,src_ip,dst_ip,port,label\n"
        )
        (ALERTS_DIR / "c2-alert.json").write_text("[]\n")
        return

    iso_labels, iso_scores = isolation_forest_labels(X)
    print(f"[+] Isolation Forest — Attack: {int(iso_labels.sum())}, "
          f"Normal: {int((iso_labels == 0).sum())}")

    model, confidence = train_xgboost(X, iso_labels)
    attacker_ips, flagged_ssh = find_attackers(ssh_df, confidence)
    print(f"[+] High-confidence attacker IPs: {len(attacker_ips)}")

    alerts = correlate_and_alert(data, attacker_ips, flagged_ssh)

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f"  Total flows        : {len(data)}")
    print(f"  SSH flows          : {len(ssh_df)}")
    print(f"  Attacker IPs       : {len(attacker_ips)}")
    print(f"  C2 alerts          : {len(alerts)}")
    print(f"  c2-predictions.csv : {PROCESSED_DIR / 'c2-predictions.csv'}")
    print(f"  Alert file         : {ALERTS_DIR / 'c2-alert.json'}")
    print("=" * 60)

if __name__ == "__main__":
    main()