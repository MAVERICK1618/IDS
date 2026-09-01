"""
Ground-Truth Validation → Dashboard PNGs
========================================
Ground truth : IDS/Red-Team/ground/
Predictions  : IDS/ML/processed/
Outputs PNG  : IDS/ML/outputs/
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths (relative — works when script is inside IDS/ML/)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent          # .../IDS/ML
IDS_DIR = BASE_DIR.parent                           # .../IDS

GROUND_DIR = IDS_DIR / "Red-Team" / "ground"        # .../IDS/Red-Team/ground
PROCESSED_DIR = BASE_DIR / "processed"              # .../IDS/ML/processed
OUTPUTS_DIR = BASE_DIR / "outputs"                  # .../IDS/ML/outputs

PROCESSED_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Ground-truth file → prediction file candidates
GT_TO_PRED = {
    "botnet.csv":   ["botnet-predictions.csv"],
    "c2.csv":       ["c2-predictions.csv"],
    "lateral.csv":  ["lateral-movement-predictions.csv"],
    "portscan.csv": ["port-scan-predictions.csv"],
    "ssh.csv":      ["ssh-brute-force-predictions.csv"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    rename = {
        "source ip": "src_ip",
        "destination ip": "dst_ip",
        "destination port": "port",
        "srcip": "src_ip",
        "dstip": "dst_ip",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    for col in ("src_ip", "dst_ip", "label"):
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.strip().str.lower()
                .str.replace("-", "_").str.replace(" ", "_")
            )

    if "port" in df.columns:
        df["port"] = pd.to_numeric(df["port"], errors="coerce").fillna(-1).astype(int)
    else:
        df["port"] = -1

    return df


def load_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, on_bad_lines="skip")
        return normalize_df(df)
    except Exception as e:
        print(f"[!] Failed to read {path}: {e}")
        return pd.DataFrame()


def make_key(row) -> tuple:
    """Match on src_ip + dst_ip + label (port ignored — GT is inconsistent)."""
    return (
        str(row.get("src_ip", "")).lower(),
        str(row.get("dst_ip", "")).lower(),
        str(row.get("label", "")).lower(),
    )


def evaluate(pred_df: pd.DataFrame, gt_df: pd.DataFrame, name: str) -> dict:
    pred_keys = set(pred_df.apply(make_key, axis=1)) if not pred_df.empty else set()
    gt_keys = set(gt_df.apply(make_key, axis=1)) if not gt_df.empty else set()

    tp = len(pred_keys & gt_keys)
    fp = len(pred_keys - gt_keys)
    fn = len(gt_keys - pred_keys)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "name": name,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pred_count": len(pred_keys),
        "gt_count": len(gt_keys),
    }


def plot_one_attack(res: dict, out_path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    metrics = [res["precision"], res["recall"], res["f1"]]
    axes[0].bar(["Precision", "Recall", "F1"], metrics,
                color=["#2ecc71", "#3498db", "#e74c3c"])
    axes[0].set_ylim(0, 1.15)
    axes[0].set_title(f"{res['name'].upper()} — Scores")
    for i, v in enumerate(metrics):
        axes[0].text(i, v + 0.03, f"{v:.2f}", ha="center", fontweight="bold")

    counts = [res["tp"], res["fp"], res["fn"]]
    axes[1].bar(["TP", "FP", "FN"], counts,
                color=["#27ae60", "#e67e22", "#c0392b"])
    axes[1].set_title(f"{res['name'].upper()} — Counts")
    ymax = max(counts) if max(counts) > 0 else 1
    axes[1].set_ylim(0, ymax * 1.2)
    for i, v in enumerate(counts):
        axes[1].text(i, v + ymax * 0.03, str(v), ha="center", fontweight="bold")

    plt.suptitle(f"Validation: {res['name'].upper()}", fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {out_path}")


def plot_overall(results: list, out_path: Path):
    names = [r["name"] for r in results]
    precision = [r["precision"] for r in results]
    recall = [r["recall"] for r in results]
    f1 = [r["f1"] for r in results]
    tp = [r["tp"] for r in results]
    fp = [r["fp"] for r in results]
    fn = [r["fn"] for r in results]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    x = np.arange(len(names))
    w = 0.25

    axes[0].bar(x - w, precision, w, label="Precision", color="#2ecc71")
    axes[0].bar(x, recall, w, label="Recall", color="#3498db")
    axes[0].bar(x + w, f1, w, label="F1", color="#e74c3c")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([n.upper() for n in names], rotation=15)
    axes[0].set_ylim(0, 1.15)
    axes[0].set_ylabel("Score")
    axes[0].set_title("Precision / Recall / F1")
    axes[0].legend()
    axes[0].axhline(0.8, color="gray", ls="--", alpha=0.4)

    axes[1].bar(x - w, tp, w, label="TP", color="#27ae60")
    axes[1].bar(x, fp, w, label="FP", color="#e67e22")
    axes[1].bar(x + w, fn, w, label="FN", color="#c0392b")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([n.upper() for n in names], rotation=15)
    axes[1].set_ylabel("Count")
    axes[1].set_title("True / False Positives & Negatives")
    axes[1].legend()

    plt.suptitle("Detector Validation vs Ground Truth (Overall)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print(" GROUND-TRUTH VALIDATION")
    print("=" * 70)
    print(f"[+] Script dir   : {BASE_DIR}")
    print(f"[+] IDS dir      : {IDS_DIR}")
    print(f"[+] Ground dir   : {GROUND_DIR}")
    print(f"[+] Predictions  : {PROCESSED_DIR}")
    print(f"[+] Outputs PNG  : {OUTPUTS_DIR}")

    if not GROUND_DIR.is_dir():
        print(f"\n[!] Ground folder not found: {GROUND_DIR}")
        print("    Expected files: botnet.csv c2.csv lateral.csv portscan.csv ssh.csv")
        return

    if not PROCESSED_DIR.is_dir():
        print(f"\n[!] Predictions folder not found: {PROCESSED_DIR}")
        return

    results = []

    for gt_name, pred_cands in GT_TO_PRED.items():
        gt_path = GROUND_DIR / gt_name
        gt_df = load_csv(gt_path)

        pred_df = pd.DataFrame()
        used_pred = None
        for cand in pred_cands:
            p = PROCESSED_DIR / cand
            if p.is_file():
                pred_df = load_csv(p)
                used_pred = cand
                break

        name = gt_name.replace(".csv", "")
        res = evaluate(pred_df, gt_df, name)
        res["gt_file"] = gt_name if gt_path.is_file() else "NOT FOUND"
        res["pred_file"] = used_pred or "NOT FOUND"
        results.append(res)

        print(f"\n[{name.upper()}]")
        print(f"  GT   : {res['gt_file']} ({res['gt_count']} unique)")
        print(f"  Pred : {res['pred_file']} ({res['pred_count']} unique)")
        print(f"  TP={res['tp']}  FP={res['fp']}  FN={res['fn']}")
        print(f"  P={res['precision']:.3f}  R={res['recall']:.3f}  F1={res['f1']:.3f}")

        plot_one_attack(res, OUTPUTS_DIR / f"eval_{name}.png")

    if not results:
        print("\n[!] Nothing to evaluate.")
        return

    plot_overall(results, OUTPUTS_DIR / "eval_overall.png")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ground_dir": str(GROUND_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "results": results,
    }
    report_path = PROCESSED_DIR / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[+] Report: {report_path}")

    print("\n" + "=" * 70)
    print(" DONE — dashboard images:")
    print("=" * 70)
    for p in sorted(OUTPUTS_DIR.glob("eval_*.png")):
        print(f"  {p}")


if __name__ == "__main__":
    main()
