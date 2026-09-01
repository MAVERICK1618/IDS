"""
Botnet Detection on Live Traffic CSV
====================================
Input  : network flow CSV
Output :
  - processed/predictions.csv   -> ONLY BOTNET rows
                                  (timestamp, src_ip, dst_ip, port, label)
  - alerts/botnet-alert.json    -> single alert file
"""

import os
import json
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
ALERTS_DIR = os.path.join(BASE_DIR, "alerts")

for d in (DATA_DIR, PROCESSED_DIR, ALERTS_DIR):
    os.makedirs(d, exist_ok=True)

INPUT_CSV = os.path.join(DATA_DIR, "live-traffic.csv")

# Isolation Forest
CONTAMINATION = 0.02
N_ESTIMATORS = 200
RANDOM_STATE = 42

# Botnet rule thresholds (tune these)
JITTER_THRESHOLD = 1.0
BYTE_RATIO_LOW = 0.3
BYTE_RATIO_HIGH = 0.85
MIN_PACKETS = 15
BOTNET_PORTS = {80, 443, 8080, 8443}
MIN_SIGNALS = 3

HIGHLY_SUSPICIOUS = -0.15
MODERATELY_SUSPICIOUS = -0.10
SLIGHTLY_UNUSUAL = -0.05

def load_and_clean(csv_path: str) -> pd.DataFrame:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"Input CSV not found: {csv_path}\n"
            f"Place your live traffic file at: {INPUT_CSV}"
        )

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip().str.lower()

    rename_map = {
        "source ip": "src_ip",
        "destination ip": "dst_ip",
        "source port": "src_port",
        "destination port": "dst_port",
        "flow duration": "duration",
        "total fwd packets": "packet_count",
        "total length of fwd packets": "bytes_sent",
        "total length of bwd packets": "bytes_received",
        "flow bytes/s": "flow_bytes_s",
        "flow packets/s": "packets_per_second",
        "flow iat mean": "flow_iat_mean",
        "flow iat std": "flow_iat_std",
        "packet length mean": "packet_length_mean",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    for col in ("src_ip", "dst_ip", "dst_port"):
        if col not in df.columns:
            raise ValueError(f"Required column missing after rename: {col}")

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

    text_cols = df.select_dtypes(include=["object"]).columns
    df[text_cols] = df[text_cols].fillna("")

    print(f"[+] Loaded {len(df)} flows from {csv_path}")
    print(f"[+] Columns: {list(df.columns)[:12]} ...")
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    bytes_sent = df.get("bytes_sent", pd.Series(0.0, index=df.index)).astype(float)
    bytes_recv = df.get("bytes_received", pd.Series(0.0, index=df.index)).astype(float)

    if (bytes_sent + bytes_recv).sum() == 0 and "byte_count" in df.columns:
        total = df["byte_count"].astype(float)
        bytes_sent = total * 0.5
        bytes_recv = total * 0.5

    packet_count = df.get("packet_count", pd.Series(0.0, index=df.index)).astype(float)
    duration = df.get("duration", pd.Series(0.0, index=df.index)).astype(float)
    pps = df.get("packets_per_second", pd.Series(0.0, index=df.index)).astype(float)

    iat_mean = df.get("flow_iat_mean", duration / (packet_count + 1e-9)).astype(float)
    iat_std = df.get("flow_iat_std", pd.Series(0.0, index=df.index)).astype(float)

    approx_std = np.where(
        iat_std == 0,
        np.abs(iat_mean - duration / (packet_count + 1e-9)),
        iat_std,
    )

    df["jitter"] = approx_std / (iat_mean + 1e-9)
    df["byte_ratio"] = bytes_sent / (bytes_sent + bytes_recv + 1e-9)
    df["packet_rate_ratio"] = pps / (
        df.get("flow_bytes_s", bytes_sent + bytes_recv + 1e-9) + 1e-9
    )
    df["total_packets"] = packet_count

    df["flow_duration"] = duration
    df["flow_iat_mean"] = iat_mean
    df["flow_iat_std"] = approx_std
    df["flow_bytes_s"] = df.get(
        "flow_bytes_s", (bytes_sent + bytes_recv) / (duration + 1e-9)
    )
    df["flow_packets_s"] = pps
    df["packet_length_mean"] = df.get(
        "packet_length_mean",
        (bytes_sent + bytes_recv) / (packet_count + 1e-9),
    )

    print("[+] Engineered features: jitter, byte_ratio, packet_rate_ratio, total_packets")
    return df

def run_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [
        "flow_duration",
        "flow_iat_mean",
        "flow_iat_std",
        "packet_length_mean",
        "flow_bytes_s",
        "flow_packets_s",
        "jitter",
        "byte_ratio",
        "packet_rate_ratio",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    if len(feature_cols) < 3:
        raise ValueError(f"Too few usable features: {feature_cols}")

    X = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
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

    df["anomaly"] = (preds == -1).astype(int)
    df["anomaly_score"] = scores.round(6)

    def severity(score: float) -> str:
        if score < HIGHLY_SUSPICIOUS:
            return "HIGHLY_SUSPICIOUS"
        if score < MODERATELY_SUSPICIOUS:
            return "MODERATELY_SUSPICIOUS"
        if score < SLIGHTLY_UNUSUAL:
            return "SLIGHTLY_UNUSUAL"
        return "NORMAL"

    df["severity"] = df["anomaly_score"].apply(severity)

    n_anom = int(df["anomaly"].sum())
    print(f"[+] Isolation Forest done — anomalies: {n_anom} ({n_anom / len(df) * 100:.2f}%)")
    return df

def apply_botnet_rules(df: pd.DataFrame) -> pd.DataFrame:
    signals_list, reasons_list, is_botnet_list = [], [], []

    for _, row in df.iterrows():
        signals = 0
        reasons = []

        jitter = float(row.get("jitter", 999))
        if jitter < JITTER_THRESHOLD:
            signals += 1
            reasons.append(f"low_jitter({jitter:.3f})")

        br = float(row.get("byte_ratio", 0.5))
        if br < BYTE_RATIO_LOW or br > BYTE_RATIO_HIGH:
            signals += 1
            reasons.append(f"asymmetric_bytes({br:.3f})")

        total_pkts = float(row.get("total_packets", 0))
        if total_pkts >= MIN_PACKETS:
            signals += 1
            reasons.append(f"sustained({int(total_pkts)}pkts)")

        port = int(row.get("dst_port", 0))
        if port in BOTNET_PORTS:
            signals += 1
            reasons.append(f"botnet_port({port})")

        if int(row.get("anomaly", 0)) == 1:
            signals += 2
            reasons.append("isolation_forest")

        is_botnet = signals >= MIN_SIGNALS
        signals_list.append(signals)
        reasons_list.append(", ".join(reasons) if reasons else "none")
        is_botnet_list.append(is_botnet)

    df["botnet_signals"] = signals_list
    df["botnet_reasons"] = reasons_list
    df["is_botnet"] = is_botnet_list
    df["label"] = df["is_botnet"].map({True: "BOTNET", False: "BENIGN"})

    n_bot = int(df["is_botnet"].sum())
    print(f"[+] Botnet rules applied — BOTNET flows: {n_bot}")
    return df

def build_predictions_csv(df: pd.DataFrame) -> pd.DataFrame:
    """ONLY BOTNET rows → predictions.csv"""
    botnet = df[df["is_botnet"] == True].copy()

    if botnet.empty:
        print("[+] No BOTNET flows — predictions.csv will be empty (header only).")
        pred = pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"])
    else:
        if "timestamp" in botnet.columns and botnet["timestamp"].astype(str).str.len().gt(5).any():
            ts = botnet["timestamp"].astype(str)
        else:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        pred = pd.DataFrame({
            "timestamp": ts,
            "src_ip": botnet["src_ip"].astype(str),
            "dst_ip": botnet["dst_ip"].astype(str),
            "port": botnet["dst_port"].astype(int),
            "label": "BOTNET",
        })

    out_path = os.path.join(PROCESSED_DIR, "botnet-predictions.csv")
    pred.to_csv(out_path, index=False)
    print(f"[+] Saved predictions (BOTNET only): {out_path}  ({len(pred)} rows)")
    return pred

def generate_alerts(df: pd.DataFrame) -> list:
    bot_df = df[df["is_botnet"] == True].copy()
    if bot_df.empty:
        print("[+] No BOTNET flows — no alerts generated.")
        out_path = os.path.join(ALERTS_DIR, "botnet-alert.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return []

    alerts = []
    seen_pairs = set()

    for _, row in bot_df.sort_values("anomaly_score").iterrows():
        src = str(row["src_ip"])
        dst = str(row["dst_ip"])
        pair = tuple(sorted([src, dst]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        def is_private(ip: str) -> bool:
            return (
                ip.startswith("10.")
                or ip.startswith("192.168.")
                or ip.startswith("172.16.")
                or ip.startswith("172.17.")
                or ip.startswith("172.18.")
                or ip.startswith("172.19.")
                or ip.startswith("172.2")
                or ip.startswith("172.3")
            )

        if is_private(src) and not is_private(dst):
            attacker, compromised = dst, src
        elif is_private(dst) and not is_private(src):
            attacker, compromised = src, dst
        else:
            attacker, compromised = src, dst

        alert_text = (
            f"ALERT [Bonet] attacker_ip: [{attacker}] "
            f"host_compromised: [{compromised}]"
        )

        alert_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": "BOTNET",
            "message": alert_text,
            "attacker_ip": attacker,
            "host_compromised": compromised,
        }
        alerts.append(alert_obj)
        print(alert_text)

    # Single fixed-name file
    out_path = os.path.join(ALERTS_DIR, "botnet-alert.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    print(f"[+] Saved single alert file: {out_path}  ({len(alerts)} alert(s))")
    return alerts

def main(csv_path: str = INPUT_CSV) -> None:
    print("=" * 60)
    print(" BOTNET DETECTION — LIVE TRAFFIC CSV")
    print("=" * 60)

    df = load_and_clean(csv_path)
    df = engineer_features(df)
    df = run_isolation_forest(df)
    df = apply_botnet_rules(df)

    build_predictions_csv(df)
    alerts = generate_alerts(df)

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f"  Total flows         : {len(df)}")
    print(f"  Isolation anomalies : {int(df['anomaly'].sum())}")
    print(f"  BOTNET flows        : {int(df['is_botnet'].sum())}")
    print(f"  Alerts generated    : {len(alerts)}")
    print(f"  botnet-predictions.csv     : {os.path.join(PROCESSED_DIR, 'botnet-predictions.csv')}")
    print(f"  Alert file          : {os.path.join(ALERTS_DIR, 'botnet-alert.json')}")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else INPUT_CSV
    main(path)