"""
Clear live traffic + all alerts + all predictions
=================================================
Removes:
  - data/live-traffic.csv
  - processed/*predictions*.csv
  - alerts/*.json
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent

TARGETS = [
    BASE / "data" / "live-traffic.csv",
    BASE / "processed",
    BASE / "alerts",
]

def clear():
    removed = 0

    # 1. live-traffic.csv
    live = BASE / "data" / "live-traffic.csv"
    if live.is_file():
        live.unlink()
        print(f"[+] Removed: {live}")
        removed += 1
    else:
        print(f"[-] Not found: {live}")

    # 2. all prediction CSVs
    processed = BASE / "processed"
    if processed.is_dir():
        for f in processed.glob("*"):
            if f.is_file() and (
                "predict" in f.name.lower()
                or f.suffix.lower() == ".csv"
                or f.suffix.lower() == ".json"
            ):
                f.unlink()
                print(f"[+] Removed: {f}")
                removed += 1
    else:
        print(f"[-] Folder not found: {processed}")

    # 3. all alert JSON files
    alerts = BASE / "alerts"
    if alerts.is_dir():
        for f in alerts.glob("*"):
            if f.is_file():
                f.unlink()
                print(f"[+] Removed: {f}")
                removed += 1
    else:
        print(f"[-] Folder not found: {alerts}")

    print()
    print(f"Done. Removed {removed} file(s).")

if __name__ == "__main__":
    print("=" * 50)
    print(" CLEAR LIVE TRAFFIC + ALERTS + PREDICTIONS")
    print("=" * 50)
    clear()
