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
CSV_FILE = BASE_DIR / "data" / "live-traffic.csv"

PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"
SSH_THRESHOLDS_FILE = BASE_DIR / "models" / "ssh_thresholds.json"

for d in (PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

SSH_PORT = 22
OUTLIER_IQR_MULTIPLIER = 1.5

# ---------------------------------------------------------------------------
# Load thresholds from JSON (written by feedback_controller after retraining)
# ---------------------------------------------------------------------------
def load_thresholds() -> tuple:
    """
    Reads ssh_thresholds.json written by feedback_controller.py after retraining.
    Falls back to safe defaults if the file doesn't exist yet.
    """
    defaults = {"MIN_ATTEMPTS_FLOOR": 5, "MAX_AVG_FLOW_DURATION_SEC": 10.0}
    if SSH_THRESHOLDS_FILE.is_file():
        try:
            with open(SSH_THRESHOLDS_FILE, "r") as f:
                data = json.load(f)
            min_floor = data.get("MIN_ATTEMPTS_FLOOR", defaults["MIN_ATTEMPTS_FLOOR"])
            max_duration = data.get("MAX_AVG_FLOW_DURATION_SEC", defaults["MAX_AVG_FLOW_DURATION_SEC"])
            print(f"[+] Loaded retrained thresholds from {SSH_THRESHOLDS_FILE.name}:")
            print(f"    MIN_ATTEMPTS_FLOOR       = {min_floor}")
            print(f"    MAX_AVG_FLOW_DURATION_SEC = {max_duration}")
            return min_floor, max_duration
        except Exception as e:
            print(f"[!] Could not read ssh_thresholds.json ({e}), using defaults.")
    else:
        print("[+] No ssh_thresholds.json found. Using default thresholds.")
    return defaults["MIN_ATTEMPTS_FLOOR"], defaults["MAX_AVG_FLOW_DURATION_SEC"]

# Load thresholds at startup — picks up any retraining done by feedback_controller
MIN_ATTEMPTS_FLOOR, MAX_AVG_FLOW_DURATION_SEC = load_thresholds()

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_data(csv_file: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()
    return df

# ---------------------------------------------------------------------------
# Threshold — uses the retrained value from ssh_thresholds.json directly
# ---------------------------------------------------------------------------
def compute_adaptive_threshold(attempt_counts: pd.Series) -> float:
    """
    Use MIN_ATTEMPTS_FLOOR directly from ssh_thresholds.json.
    The old IQR formula was computing 292 while attackers only had 145 attempts,
    making detection impossible. The floor from retraining IS the correct threshold.
    """
    return float(MIN_ATTEMPTS_FLOOR)

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