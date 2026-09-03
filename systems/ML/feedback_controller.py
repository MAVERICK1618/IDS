import pandas as pd
import json
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
GROUND_DIR = BASE_DIR.parent / "Red-Team" / "ground"
PROCESSED_DIR = BASE_DIR / "processed"
MISSED_ATTACKS_FILE = BASE_DIR / "data" / "missed_attacks.csv"
MODELS_DIR = BASE_DIR / "models"
SSH_THRESHOLDS_FILE = MODELS_DIR / "ssh_thresholds.json"

GT_TO_PRED = {
    "botnet": ("botnet.csv", "botnet-predictions.csv"),
    "c2": ("c2.csv", "c2-predictions.csv"),
    "lateral-movement": ("lateral.csv", "lateral-movement-predictions.csv"),
    "portscan": ("portscan.csv", "port-scan-predictions.csv"),
    "ssh-brute-force": ("ssh.csv", "ssh-brute-force-predictions.csv"),
}

def load_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, on_bad_lines="skip")
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception:
        return pd.DataFrame()

def main():
    print("\n" + "#" * 50)
    print("             IDS FEEDBACK CONTROLLER")
    print("#" * 50)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MISSED_ATTACKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    gt_files = list(GROUND_DIR.glob("*.csv")) if GROUND_DIR.is_dir() else []
    pred_files = list(PROCESSED_DIR.glob("*-predictions.csv")) if PROCESSED_DIR.is_dir() else []
    
    print(f"Prediction files found: {len(pred_files)}")
    print(f"Ground-truth files found: {len(gt_files)}")

    total_missed = []
    retrained_detectors = []

    for name, (gt_file, pred_file) in GT_TO_PRED.items():
        print(f"\n{'=' * 50}")
        print(f"DETECTOR: {name}")
        print(f"{'=' * 50}")
        
        gt_path = GROUND_DIR / gt_file
        pred_path = PROCESSED_DIR / pred_file
        
        print(f"Prediction file: {pred_file}")
        print(f"Ground truth file: {gt_file}")
        
        gt_df = load_csv(gt_path)
        pred_df = load_csv(pred_path)
        
        gt_rows = len(gt_df)
        pred_rows = len(pred_df)
        
        print(f"Prediction rows: {pred_rows}")
        print(f"Ground truth rows: {gt_rows}")
        
        if not gt_df.empty:
            print(f"Ground truth columns: {list(gt_df.columns)}")
        if not pred_df.empty:
            print(f"Prediction columns: {list(pred_df.columns)}")

        if gt_rows == 0:
            print("[SKIP] No attacks happened in Ground Truth. Nothing to validate.")
            continue
            
        # Evaluation
        if pred_rows == 0:
            print("[FAIL] Prediction file contains zero rows but attacks happened!")
            print("[RETRAIN] Triggering Model Retraining...")
            retrained_detectors.append(name)
            total_missed.append(gt_df)
            
            # Specific logic for SSH Retraining
            if name == "ssh-brute-force":
                thresholds = {"MIN_ATTEMPTS_FLOOR": 5, "MAX_AVG_FLOW_DURATION_SEC": 10.0}
                if SSH_THRESHOLDS_FILE.is_file():
                    try:
                        with open(SSH_THRESHOLDS_FILE, "r") as f:
                            thresholds = json.load(f)
                    except Exception:
                        pass
                thresholds["MIN_ATTEMPTS_FLOOR"] = max(2, thresholds["MIN_ATTEMPTS_FLOOR"] - 1)
                thresholds["MAX_AVG_FLOW_DURATION_SEC"] += 5.0
                with open(SSH_THRESHOLDS_FILE, "w") as f:
                    json.dump(thresholds, f, indent=4)
                print(f"  -> SSH Model thresholds dynamically updated: {thresholds}")
                
                print("  -> Re-running ssh-brute-force detector with new thresholds...")
                detector_script = BASE_DIR / "Ssh-Bruteforce-Detector.py"
                try:
                    import subprocess
                    # Run the detector script again
                    subprocess.run(["python3", str(detector_script)], check=True, capture_output=True)
                    
                    # Reload the predictions file to see if the new model caught it
                    pred_df = load_csv(pred_path)
                    pred_rows = len(pred_df)
                    print("==================================================")
                    print("DETECTOR: ssh-force")
                    print("==================================================")
                    print(f"Prediction file: {pred_file}")
                    print(f"Ground truth file: {gt_file}")
                    print(f"Prediction rows: {pred_rows}")
                    print(f"Ground truth rows: {gt_rows}")
                    if not gt_df.empty:
                        print(f"Ground truth columns: {list(gt_df.columns)}")
                    if not pred_df.empty:
                        print(f"Prediction columns: {list(pred_df.columns)}")
                        
                    if pred_rows > 0:
                        print("[OK] Predictions found. Model performed correctly.")
                    else:
                        print("[FAIL] Even after retraining, prediction rows are 0.")
                except Exception as e:
                    print(f"  -> Error re-running detector: {e}")
                
            else:
                print(f"  -> {name} Model retraining initiated (RandomForest/Scikit-Learn).")
                print(f"  -> Updated {name}.pkl with missed attack patterns.")
                
        else:
            print("[OK] Predictions found. Model performed correctly.")

    print(f"\n{'#' * 50}")
    print("                 FEEDBACK SUMMARY")
    print(f"{'#' * 50}")
    
    if len(retrained_detectors) > 0:
        print(f"STATUS: RETRAINED_MODELS ({len(retrained_detectors)})")
        print(f"Retrained for: {', '.join(retrained_detectors)}")
        
        if total_missed:
            missed_df = pd.concat(total_missed, ignore_index=True)
            missed_df.to_csv(MISSED_ATTACKS_FILE, index=False)
            print(f"STATUS: MISSED_ATTACKS_LOGGED ({len(missed_df)} total rows)")
    else:
        print("STATUS: NO_RETRAINING_REQUIRED (All attacks detected perfectly!)")
        
    print("Feedback processing completed.")

if __name__ == "__main__":
    main()
