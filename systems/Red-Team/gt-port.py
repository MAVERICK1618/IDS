import socket
import threading
import time
import sys
import csv
from datetime import datetime
from pathlib import Path

# ============== CONFIG ==============
CSV_PATH = Path("./ground/portscan.csv")   # <-- change this path if needed
THREADS = 100
TIMEOUT = 0.5
# ====================================

def get_local_ip():
    """Get the source IP of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def scan_port(target, port, src_ip, writer, lock):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((target, port))
        sock.close()

        # Log every attempt as ground truth (common for IDS datasets)
        timestamp = datetime.utcnow().isoformat() + "Z"
        with lock:
            writer.writerow({
                "timestamp": timestamp,
                "src_ip": src_ip,
                "dst_ip": target,
                "dst_port": port,
                "label": "portscan"
            })

        if result == 0:
            print(f"[+] Port {port} OPEN on {target}")
    except Exception:
        pass

def port_scan(target, start_port=1, end_port=1000, threads=THREADS):
    src_ip = get_local_ip()
    print(f"[*] Source IP detected: {src_ip}")
    print(f"[*] Starting port scan on {target} ({start_port}-{end_port})")
    print(f"[*] Ground-truth CSV will be written to: {CSV_PATH.resolve()}")

    # Create CSV and write header
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = CSV_PATH.exists()

    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        fieldnames = ["timestamp", "src_ip", "dst_ip", "dst_port", "label"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        lock = threading.Lock()
        thread_list = []

        for port in range(start_port, end_port + 1):
            t = threading.Thread(
                target=scan_port,
                args=(target, port, src_ip, writer, lock)
            )
            thread_list.append(t)
            t.start()

            # Limit concurrent threads
            if len(thread_list) >= threads:
                for t in thread_list:
                    t.join()
                thread_list = []
                time.sleep(0.05)   # small pause to avoid flooding

        # Wait for remaining threads
        for t in thread_list:
            t.join()

    print("[*] Port scan completed")
    print(f"[*] Ground-truth saved → {CSV_PATH.resolve()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python port_scan_sim.py <target_ip> [start_port] [end_port]")
        sys.exit(1)

    target = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end   = int(sys.argv[3]) if len(sys.argv) > 3 else 500

    port_scan(target, start_port=start, end_port=end)
