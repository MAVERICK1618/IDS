import pandas as pd
import glob
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
GROUND_TRUTH_DIR = BASE_DIR.parent / "Red-Team" / "ground"
PREDICTIONS_DIR = BASE_DIR / "processed"
MISSED_ATTACKS_FILE = BASE_DIR / "data" / "missed_attacks.csv"

def load_csvs(pattern):
    files = glob.glob(str(pattern))
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df.columns = df.columns.str.strip()
            dfs.append(df)
        except Exception:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def main():
    print("=" * 60)
    print(" AUTO EVALUATOR (Finding Missed Attacks)")
    print("=" * 60)
    
    # 1. Load Ground Truth
    gt_df = load_csvs(GROUND_TRUTH_DIR / "*.csv")
    if gt_df.empty:
        print("[!] No ground truth data found.")
        return
        
    # 2. Load Predictions
    pred_df = load_csvs(PREDICTIONS_DIR / "*-predictions.csv")
    
    # Normalizing labels to uppercase for comparison
    gt_df["label"] = gt_df["label"].str.upper()
    if not pred_df.empty:
        pred_df["label"] = pred_df["label"].str.upper()
        # Create a unique key for matching: SourceIP_DestIP_Label
        pred_keys = set(zip(pred_df["src_ip"], pred_df["dst_ip"]))
    else:
        pred_keys = set()
        
    # 3. Find Missed Attacks (False Negatives)
    missed_rows = []
    for _, row in gt_df.iterrows():
        key = (row["src_ip"], row["dst_ip"])
        if key not in pred_keys:
            missed_rows.append(row)
            
    # 4. Save Missed Attacks
    missed_df = pd.DataFrame(missed_rows)
    MISSED_ATTACKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if not missed_df.empty:
        missed_df.to_csv(MISSED_ATTACKS_FILE, index=False)
        print(f"[!] Found {len(missed_df)} missed attacks (False Negatives)!")
        print(f"[+] Saved to: {MISSED_ATTACKS_FILE}")
    else:
        # Empty file to indicate no missed attacks
        pd.DataFrame(columns=gt_df.columns).to_csv(MISSED_ATTACKS_FILE, index=False)
        print("[+] Excellent! No missed attacks detected.")

if __name__ == "__main__":
    main()
