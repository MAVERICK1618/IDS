"""
Lateral movement GT simulator (lab only)
Fixes: IncompatiblePeer / no acceptable host key
"""

import csv
import logging
import socket
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import paramiko

logging.getLogger("paramiko").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# Lab: allow older host-key / kex (Metasploitable, old OpenSSH)
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

# ====== CONFIG ======
USERNAME = "test"          # e.g. msfadmin on Metasploitable
PASSWORD = "test"
WAIT_SECONDS = 60
GROUND_TRUTH = "./ground/lateral.csv"
LABEL = "lateral-movement"
# ====================


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def log_event(src_ip, dst_ip, port, label):
    path = Path(GROUND_TRUTH)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "src_ip", "dst_ip", "port", "label"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "port": port,
            "label": label,
        })


def run_ssh_session(target, username, password, src_ip):
    print(f"\n[*] Connecting to {target} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=target,
            port=22,
            username=username,
            password=password,
            timeout=20,
            banner_timeout=40,
            auth_timeout=25,
            look_for_keys=False,
            allow_agent=False,
        )
        print("[+] Login successful")

        for _ in range(5):
            log_event(src_ip, target, 22, LABEL)
            time.sleep(0.05)

        # Lighter discovery commands (nmap full scan is slow / may not exist)
        commands = [
            "whoami",
            "uname -a",
            "hostname",
            "ip addr || ifconfig",
            "arp -a || cat /proc/net/arp",
            "cat /etc/hosts",
        ]
        for cmd in commands:
            print(f"[*] Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            output = stdout.read().decode(errors="ignore").strip()
            error = stderr.read().decode(errors="ignore").strip()
            if output:
                print(output)
            if error:
                print("ERR:", error)
            log_event(src_ip, target, 22, LABEL)
            time.sleep(1)

        print("[+] Session finished – logging out")
        client.close()
        return True

    except paramiko.AuthenticationException:
        print("[!] Auth failed — wrong username/password")
        log_event(src_ip, target, 22, LABEL)
    except paramiko.ssh_exception.IncompatiblePeer as e:
        print(f"[!] Host-key/KEX incompatible: {e}")
        log_event(src_ip, target, 22, LABEL)
    except Exception as e:
        print(f"[!] Connection failed: {type(e).__name__}: {e}")
        log_event(src_ip, target, 22, LABEL)
    finally:
        try:
            client.close()
        except Exception:
            pass
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gt-lateral.py <IP>")
        print("Example: python3 gt-lateral.py 192.168.64.131")
        sys.exit(1)

    TARGET_IP = sys.argv[1].strip()
    src_ip = get_local_ip()

    print(f"[*] Source IP: {src_ip}")
    print(f"[*] Target: {TARGET_IP}")
    print(f"[*] User: {USERNAME}")
    print(f"[*] Ground-truth: {GROUND_TRUTH}")
    print("[!] Only use on systems you own\n")

    run_ssh_session(TARGET_IP, USERNAME, PASSWORD, src_ip)

    print(f"\n[*] Waiting {WAIT_SECONDS} seconds...")
    time.sleep(WAIT_SECONDS)

    run_ssh_session(TARGET_IP, USERNAME, PASSWORD, src_ip)

    print("\n[+] Done.")
