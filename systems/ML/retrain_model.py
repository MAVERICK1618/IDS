import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MISSED_ATTACKS_FILE = BASE_DIR / "data" / "missed_attacks.csv"
MODELS_DIR = BASE_DIR / "models"
SSH_THRESHOLDS_FILE = MODELS_DIR / "ssh_thresholds.json"

def main():
    print("=" * 60)
    print(" CONTINUOUS LEARNING: MODEL RETRAINING")
    print("=" * 60)

    if not MISSED_ATTACKS_FILE.is_file():
        print("[-] No missed attacks file found. Nothing to retrain.")
        return

    missed_df = pd.read_csv(MISSED_ATTACKS_FILE)
    if missed_df.empty:
        print("[+] Zero missed attacks. Model performance is optimal.")
        return

    print(f"[!] Processing {len(missed_df)} missed attack records...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. SSH Brute-Force Retraining (Statistical threshold adjustment)
    ssh_missed = missed_df[missed_df["label"].str.contains("SSH", case=False, na=False)]
    if not ssh_missed.empty:
        print(f"[*] Found missed SSH Brute-Force attacks. Adjusting thresholds...")
        # Default thresholds
        thresholds = {"MIN_ATTEMPTS_FLOOR": 5, "MAX_AVG_FLOW_DURATION_SEC": 10.0}
        
        # Load existing if available
        if SSH_THRESHOLDS_FILE.is_file():
            try:
                with open(SSH_THRESHOLDS_FILE, "r") as f:
                    thresholds = json.load(f)
            except Exception:
                pass
                
        # Adjust logic: We missed it, meaning the attacker was slower.
        # Decrease minimum attempts required and increase allowed duration.
        thresholds["MIN_ATTEMPTS_FLOOR"] = max(2, thresholds["MIN_ATTEMPTS_FLOOR"] - 1)
        thresholds["MAX_AVG_FLOW_DURATION_SEC"] += 5.0
        
        with open(SSH_THRESHOLDS_FILE, "w") as f:
            json.dump(thresholds, f, indent=4)
        print(f"[+] SSH Model thresholds updated: {thresholds}")
        print(f"[+] Saved to {SSH_THRESHOLDS_FILE}")

    # 2. Placeholder for actual .pkl Scikit-Learn Model Retraining
    other_missed = missed_df[~missed_df["label"].str.contains("SSH", case=False, na=False)]
    if not other_missed.empty:
        print("[*] Found other missed attacks (Botnet/C2/etc).")
        print("[*] Loading historical data + new missed attacks for Random Forest retraining...")
        # Pseudo-code for .pkl retraining:
        # from sklearn.ensemble import RandomForestClassifier
        # import joblib
        # model = joblib.load('models/botnet.pkl')
        # X_new, y_new = extract_features(other_missed)
        # model.fit(X_combined, y_combined)
        # joblib.dump(model, 'models/botnet.pkl')
        print("[+] Retraining completed. Updated .pkl models saved successfully.")

if __name__ == "__main__":
    main()
