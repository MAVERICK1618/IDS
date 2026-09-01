"""
SSH Brute-Force Detection
=========================
Output:
  - processed/ssh-brute-force-predictions.csv  → one row per malicious SSH flow
  - alerts/ssh-brute-force-alert.json          → single alert file (one entry per pair)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "data" /"live-traffic.csv"          # change path if needed

PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"

for d in (PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

SSH_PORT = 22
MIN_ATTEMPTS_FLOOR = 5
MAX_AVG_FLOW_DURATION_SEC = 10.0
OUTLIER_IQR_MULTIPLIER = 1.5

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_data(csv_file: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()
    return df

# ---------------------------------------------------------------------------
# Adaptive threshold
# ---------------------------------------------------------------------------
def compute_adaptive_threshold(attempt_counts: pd.Series) -> float:
    if len(attempt_counts) < 4:
        return float(MIN_ATTEMPTS_FLOOR)
    q1 = attempt_counts.quantile(0.25)
    q3 = attempt_counts.quantile(0.75)
    iqr = q3 - q1
    statistical_cutoff = q3 + OUTLIER_IQR_MULTIPLIER * iqr
    return max(float(MIN_ATTEMPTS_FLOOR), statistical_cutoff)

def classify_severity(attempts: int, threshold: float) -> str:
    ratio = attempts / threshold if threshold else attempts
    if ratio >= 3:
        return "HIGH"
    elif ratio >= 1.5:
        return "MEDIUM"
    return "LOW"

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def detect_ssh_bruteforce(df: pd.DataFrame, ssh_port: int):
    ssh_traffic = df[df["Destination Port"] == ssh_port].copy()
    if ssh_traffic.empty:
        return [], MIN_ATTEMPTS_FLOOR, pd.DataFrame()

    grouped = (
        ssh_traffic
        .groupby(["Source IP", "Destination IP"])
        .agg(
            Connection_Attempts=("Destination Port", "count"),
            Avg_Flow_Duration_sec=("Flow Duration", "mean"),
            Total_Fwd_Packets=("Total Fwd Packets", "sum"),
            Distinct_Source_Ports=("Source Port", "nunique"),
        )
        .reset_index()
    )

    threshold = compute_adaptive_threshold(grouped["Connection_Attempts"])

    flagged = grouped[
        (grouped["Connection_Attempts"] >= threshold) &
        (grouped["Avg_Flow_Duration_sec"] <= MAX_AVG_FLOW_DURATION_SEC)
    ]

    # Keep only the individual flows that belong to flagged pairs
    if flagged.empty:
        malicious_flows = pd.DataFrame()
    else:
        keys = set(zip(flagged["Source IP"], flagged["Destination IP"]))
        mask = ssh_traffic.apply(
            lambda r: (r["Source IP"], r["Destination IP"]) in keys, axis=1
        )
        malicious_flows = ssh_traffic[mask].copy()

    alerts = []
    for _, row in flagged.iterrows():
        attempts = int(row["Connection_Attempts"])
        alerts.append({
            "attacker": str(row["Source IP"]),
            "target": str(row["Destination IP"]),
            "attempts": attempts,
            "avg_duration": float(row["Avg_Flow_Duration_sec"]),
            "distinct_source_ports": int(row["Distinct_Source_Ports"]),
            "severity": classify_severity(attempts, threshold),
            "port": ssh_port,
        })

    alerts.sort(key=lambda a: a["attempts"], reverse=True)
    return alerts, threshold, malicious_flows

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(" SSH BRUTE-FORCE DETECTION")
    print("=" * 60)

    df = load_data(CSV_FILE)
    print(f"[+] Loaded {len(df):,} flows from {CSV_FILE}")

    raw_alerts, threshold, malicious_flows = detect_ssh_bruteforce(df, SSH_PORT)
    print(f"[+] Adaptive threshold used: {threshold:.1f} attempts")

    now = datetime.now(timezone.utc).isoformat()
    alerts = []
    pred_rows = []

    if not raw_alerts:
        print("[+] No SSH brute-force activity detected.")
    else:
        print(f"\n[+] Detected {len(raw_alerts)} SSH brute-force pair(s):\n")
        for a in raw_alerts:
            alert_text = (
                f"ALERT [ssh-bruteforce] attacker_ip: [{a['attacker']}] "
                f"host_compromised: [{a['target']}]"
            )
            print(alert_text)
            print(f"  Attempts: {a['attempts']} | "
                  f"Avg Duration: {a['avg_duration']:.3f}s | "
                  f"Severity: {a['severity']}")
            print()

            alerts.append({
                "timestamp": now,
                "alert_type": "SSH_BRUTEFORCE",
                "message": alert_text,
                "attacker_ip": a["attacker"],
                "host_compromised": a["target"],
            })

        # One prediction row for EVERY individual malicious SSH flow
        for _, row in malicious_flows.iterrows():
            pred_rows.append({
                "timestamp": now,
                "src_ip": str(row["Source IP"]),
                "dst_ip": str(row["Destination IP"]),
                "port": int(row["Destination Port"]),
                "label": "SSH_BRUTEFORCE",
            })

    # ---------- predictions.csv (one row per malicious flow) ----------
    pred_path = PROCESSED_DIR / "ssh-brute-force-predictions.csv"
    if pred_rows:
        pd.DataFrame(pred_rows).to_csv(pred_path, index=False)
        print(f"[+] Saved predictions (SSH_BRUTEFORCE only): {pred_path}  ({len(pred_rows)} rows)")
    else:
        pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"]).to_csv(
            pred_path, index=False
        )
        print(f"[+] Empty ssh-brute-force-predictions.csv written")

    # ---------- single alert JSON ----------
    alert_path = ALERTS_DIR / "ssh-brute-force-alert.json"
    with open(alert_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)
    print(f"[+] Saved single alert file: {alert_path}  ({len(alerts)} alert(s))")

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f"  Total flows              : {len(df):,}")
    print(f"  SSH brute-force alerts   : {len(alerts)}")
    print(f"  Prediction rows          : {len(pred_rows)}")
    print(f"  predictions.csv          : {pred_path}")
    print(f"  Alert file               : {alert_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()