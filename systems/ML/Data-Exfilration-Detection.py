"""
3-Stage Attack Chain Detector (Data Exfiltration focused)
=========================================================
Stage 1: SSH / auth recon-probe
Stage 2: Brute-Force
Stage 3: Data Exfiltration

Uses resolved client/server roles (port-based) instead of raw Source/Destination.

Output:
  - processed/predictions.csv      → only detected rows
  - alerts/data-exfil-alert.json   → single alert file
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = BASE_DIR / "processed"
ALERTS_DIR = BASE_DIR / "alerts"

for d in (DATA_DIR, PROCESSED_DIR, ALERTS_DIR):
    d.mkdir(exist_ok=True)

AUTH_PORTS = {22, 23, 3389, 21, 445, 5900, 3306, 1433}  # SSH, Telnet, RDP, FTP, SMB, VNC, MySQL, MSSQL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_private(ip):
    try:
        p = [int(x) for x in str(ip).split(".")]
    except Exception:
        return False
    return (
        p[0] == 10
        or (p[0] == 172 and 16 <= p[1] <= 31)
        or (p[0] == 192 and p[1] == 168)
    )

def resolve_roles(df):
    """Decide client/server by port role, not CSV Source/Destination labels."""
    sp, dp = df["Source Port"], df["Destination Port"]
    src_is_server = (sp < 1024) & (dp >= 1024)
    dst_is_server = (dp < 1024) & (sp >= 1024)

    df["client_ip"] = np.where(
        src_is_server, df["Destination IP"],
        np.where(dst_is_server, df["Source IP"], df["Source IP"])
    )
    df["client_port"] = np.where(
        src_is_server, dp,
        np.where(dst_is_server, sp, sp)
    )
    df["server_ip"] = np.where(
        src_is_server, df["Source IP"],
        np.where(dst_is_server, df["Destination IP"], df["Destination IP"])
    )
    df["server_port"] = np.where(
        src_is_server, sp,
        np.where(dst_is_server, dp, dp)
    )
    return df

def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df = df.reset_index().rename(columns={"index": "flow_id"})
    return resolve_roles(df)

# ---------------------------------------------------------------------------
# Stage 1 – Recon / Probe
# ---------------------------------------------------------------------------
def detect_recon_probe(df, min_attempts=3, max_pkts=2, max_duration=0.05, auth_only=True):
    tiny = df[
        (df["Total Fwd Packets"] <= max_pkts) &
        (df["Flow Duration"] < max_duration)
    ]
    if auth_only:
        tiny = tiny[tiny["server_port"].isin(AUTH_PORTS)]

    g = tiny.groupby(["client_ip", "server_ip"]).agg(
        distinct_server_ports=("server_port", "nunique"),
        n_probes=("server_port", "count"),
        ports=("server_port", lambda x: sorted(x.unique().tolist())),
    ).reset_index()
    return g[g["n_probes"] >= min_attempts].sort_values("n_probes", ascending=False)

# ---------------------------------------------------------------------------
# Stage 2 – Brute-Force
# ---------------------------------------------------------------------------
def detect_brute_force(df, min_attempts=8, internal_only=True, auth_only=True):
    base = df[df["server_port"].isin(AUTH_PORTS)] if auth_only else df
    g = base.groupby(["client_ip", "server_ip", "server_port"]).agg(
        attempts=("flow_id", "count"),
        distinct_client_ports=("client_port", "nunique"),
        avg_duration=("Flow Duration", "mean"),
    ).reset_index()

    mask = g["attempts"] >= min_attempts
    if internal_only:
        mask &= g["client_ip"].apply(is_private) & g["server_ip"].apply(is_private)
    return g[mask].sort_values("attempts", ascending=False)

# ---------------------------------------------------------------------------
# Stage 3 – Data Exfiltration
# ---------------------------------------------------------------------------
def detect_exfiltration(df, contamination=0.05, min_bytes=100_000, max_duration=15):
    feat = df.select_dtypes(include=[np.number]).drop(columns=["flow_id"], errors="ignore").copy()
    feat = feat.replace([np.inf, -np.inf], np.nan).fillna(0)
    feat["fwd_bwd_ratio"] = (df["Total Length of Fwd Packets"] + 1) / (df["Total Length of Bwd Packets"] + 1)
    feat["dst_external"] = (~df["Destination IP"].apply(is_private)).astype(int)

    X = StandardScaler().fit_transform(feat)
    iso = IsolationForest(n_estimators=300, contamination=contamination, random_state=42)
    pred = iso.fit_predict(X)
    score = -iso.score_samples(X)

    out = df.copy()
    out["iso_flag"] = pred == -1
    out["iso_score"] = score

    return out[
        (out["iso_flag"]) &
        (out["Total Length of Fwd Packets"] > min_bytes) &
        (out["Flow Duration"] < max_duration)
    ].sort_values("iso_score", ascending=False)

# ---------------------------------------------------------------------------
# Cross-stage correlation + alerts + predictions
# ---------------------------------------------------------------------------
def validate_and_alert(scan_df, bf_df, exfil_df):
    alerts = []
    pred_rows = []
    now = datetime.now(timezone.utc).isoformat()
    seen = set()

    actors = set(scan_df["client_ip"]) | set(bf_df["client_ip"])

    print("\n" + "=" * 70)
    print(" CROSS-STAGE VALIDATION")
    print("=" * 70)

    for actor in actors:
        scan_hit = scan_df[scan_df["client_ip"] == actor]
        bf_hit = bf_df[bf_df["client_ip"] == actor]
        exfil_from_actor = exfil_df[exfil_df["client_ip"] == actor]
        exfil_to_actor = exfil_df[exfil_df["server_ip"] == actor]

        has_recon = len(scan_hit) > 0
        has_bf = len(bf_hit) > 0
        has_exfil = len(exfil_from_actor) > 0 or len(exfil_to_actor) > 0

        status = "CONFIRMED" if (has_bf or has_exfil) else "RECON ONLY"

        print(
            f"Actor {actor}: "
            f"Stage1={'YES' if has_recon else 'no'} | "
            f"Stage2={'YES' if has_bf else 'no'} | "
            f"Stage3={'YES' if has_exfil else 'no'}  => {status}"
        )

        if status != "CONFIRMED":
            continue

        # Prefer victim = the internal host being attacked / exfiltrating
        if len(exfil_to_actor):
            # victim pushed data TO the actor
            for _, row in exfil_to_actor.iterrows():
                victim = str(row["client_ip"])
                key = (str(actor), victim)
                if key in seen:
                    continue
                seen.add(key)

                alert_text = (
                    f"ALERT [Exfil] attacker_ip: [{actor}] "
                    f"host_compromised: [{victim}]"
                )
                print(alert_text)

                alerts.append({
                    "timestamp": now,
                    "alert_type": "DATA_EXFILTRATION",
                    "message": alert_text,
                    "attacker_ip": str(actor),
                    "host_compromised": victim,
                })

                pred_rows.append({
                    "timestamp": now,
                    "src_ip": str(actor),
                    "dst_ip": victim,
                    "port": int(row.get("server_port", 0)),
                    "label": "DATA_EXFIL",
                })

        elif len(bf_hit):
            # Brute-force confirmed → treat server as compromised host
            for _, row in bf_hit.iterrows():
                victim = str(row["server_ip"])
                key = (str(actor), victim)
                if key in seen:
                    continue
                seen.add(key)

                alert_text = (
                    f"ALERT [Exfil] attacker_ip: [{actor}] "
                    f"host_compromised: [{victim}]"
                )
                print(alert_text)

                alerts.append({
                    "timestamp": now,
                    "alert_type": "DATA_EXFILTRATION",
                    "message": alert_text,
                    "attacker_ip": str(actor),
                    "host_compromised": victim,
                })

                pred_rows.append({
                    "timestamp": now,
                    "src_ip": str(actor),
                    "dst_ip": victim,
                    "port": int(row.get("server_port", 0)),
                    "label": "DATA_EXFIL",
                })

    # ---------- predictions.csv (only detected rows) ----------
    pred_path = PROCESSED_DIR / "data-exfil-predictions.csv"
    if pred_rows:
        pd.DataFrame(pred_rows).to_csv(pred_path, index=False)
        print(f"\n[+] Saved predictions: {pred_path}  ({len(pred_rows)} rows)")
    else:
        pd.DataFrame(columns=["timestamp", "src_ip", "dst_ip", "port", "label"]).to_csv(
            pred_path, index=False
        )
        print(f"\n[+] No confirmed detections — empty predictions.csv written")

    # ---------- single alert file ----------
    alert_path = ALERTS_DIR / "data-exfil-alert.json"
    with open(alert_path, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)
    print(f"[+] Saved single alert file: {alert_path}  ({len(alerts)} alert(s))")

    return alerts

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(path):
    print("=" * 70)
    print(" 3-STAGE ATTACK CHAIN / DATA EXFILTRATION DETECTOR")
    print("=" * 70)

    df = load(path)
    print(f"[+] Loaded {len(df)} flows from {path}")

    scan = detect_recon_probe(df)
    bf = detect_brute_force(df)
    exfil = detect_exfiltration(df)

    print(f"[+] Recon/probe candidates : {len(scan)}")
    print(f"[+] Brute-force candidates : {len(bf)}")
    print(f"[+] Exfiltration candidates: {len(exfil)}")

    alerts = validate_and_alert(scan, bf, exfil)

    print("\n" + "=" * 70)
    print(" SUMMARY")
    print("=" * 70)
    print(f"  Total flows          : {len(df)}")
    print(f"  Confirmed alerts     : {len(alerts)}")
    print(f"  data-exfil-predictions.csv      : {PROCESSED_DIR / 'data-exfil-predictions.csv'}")
    print(f"  Alert file           : {ALERTS_DIR / 'data-exfil-alert.json'}")
    print("=" * 70)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "live-traffic.csv"
    main(path)