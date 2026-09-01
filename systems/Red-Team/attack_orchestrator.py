"""
Lab Attack Orchestrator (VMware / isolated network only)
========================================================
Phase 1: Port-scan every live host on the subnet (gt-port.py)
Phase 2: Per host, based on open ports:
           22     → gt-ssh.py → gt-lateral.py → gt-c2.py
           80/443 → gt-bonet.py
           21     → FTP later

Usage:
  python3 attack_orchestrator.py --once
  python3 attack_orchestrator.py --sleep 120
  python3 attack_orchestrator.py --subnet 10.10.10.0/24 --once
"""

import argparse
import ipaddress
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RED_TEAM_DIR = Path(__file__).resolve().parent
GROUND_DIR = RED_TEAM_DIR / "ground"
GROUND_DIR.mkdir(exist_ok=True)

DEFAULT_SUBNET = "10.10.10.0/24"
SCAN_PORTS = [21, 22, 80, 443, 4444]
PORT_TIMEOUT = 0.4
SCAN_WORKERS = 64
LOOP_SLEEP_SEC = 120
PYTHON = sys.executable

# Port-scan range passed to gt-port.py (general scan)
PORT_SCAN_START = 1
PORT_SCAN_END = 500

SCRIPTS = {
    "port":    RED_TEAM_DIR / "gt-port.py",
    "ssh":     RED_TEAM_DIR / "gt-ssh.py",
    "lateral": RED_TEAM_DIR / "gt-lateral.py",
    "c2":      RED_TEAM_DIR / "gt-c2.py",
    "botnet":  RED_TEAM_DIR / "gt-bonet.py",
    # "ftp":   RED_TEAM_DIR / "gt-ftp.py",
}

# ---------------------------------------------------------------------------
# Discovery scan (quick — only ports we care about)
# ---------------------------------------------------------------------------
def port_open(ip: str, port: int, timeout: float = PORT_TIMEOUT) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ok = s.connect_ex((ip, port)) == 0
        s.close()
        return ok
    except Exception:
        return False


def scan_host(ip: str, ports: list) -> dict:
    open_ports = [p for p in ports if port_open(ip, p)]
    return {"ip": ip, "open": open_ports}


def discover_targets(subnet: str, ports: list) -> list:
    net = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(h) for h in net.hosts()]
    print(f"[*] Discovery scan {subnet} ({len(hosts)} hosts) ports={ports}")
    results = []
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        futs = {pool.submit(scan_host, ip, ports): ip for ip in hosts}
        for fut in as_completed(futs):
            r = fut.result()
            if r["open"]:
                print(f"  [+] {r['ip']} open: {r['open']}")
                results.append(r)
    print(f"[*] Targets found: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Run GT script
# ---------------------------------------------------------------------------
def run_script(name: str, args: list, timeout: int = 300) -> int:
    script = SCRIPTS.get(name)
    if not script or not script.is_file():
        print(f"  [!] Script missing: {name} → {script}")
        return 1
    cmd = [PYTHON, str(script)] + [str(a) for a in args]
    print(f"  → {' '.join(cmd)}")
    try:
        p = subprocess.run(cmd, cwd=str(RED_TEAM_DIR), timeout=timeout)
        return p.returncode
    except subprocess.TimeoutExpired:
        print(f"  [!] Timeout: {name}")
        return 1
    except Exception as e:
        print(f"  [!] Failed {name}: {e}")
        return 1


# ---------------------------------------------------------------------------
# PHASE 1 — general port scan on ALL discovered hosts
# ---------------------------------------------------------------------------
def phase_portscan_all(targets: list):
    print("\n" + "=" * 60)
    print(" PHASE 1: GENERAL PORT SCAN (all targets)")
    print("=" * 60)
    if not targets:
        print("[*] No targets — skip port scan phase.")
        return

    for t in targets:
        ip = t["ip"]
        print(f"\n[*] Port-scanning {ip} ({PORT_SCAN_START}-{PORT_SCAN_END})")
        run_script("port", [ip, PORT_SCAN_START, PORT_SCAN_END], timeout=300)

    print("\n[+] Phase 1 complete — ground/portscan.csv updated")


# ---------------------------------------------------------------------------
# PHASE 2 — SSH / lateral / C2 / botnet depending on open ports
# ---------------------------------------------------------------------------
def phase_followup_attacks(targets: list):
    print("\n" + "=" * 60)
    print(" PHASE 2: FOLLOW-UP ATTACKS (by open port)")
    print("=" * 60)
    if not targets:
        print("[*] No targets — skip follow-up.")
        return

    for t in targets:
        ip = t["ip"]
        open_ports = set(t["open"])
        print(f"\n=== {ip} open={sorted(open_ports)} ===")

        # SSH chain
        if 22 in open_ports:
            print(f"  [*] 22 open → SSH + lateral + C2")
            run_script("ssh", [ip], timeout=180)
            run_script("lateral", [ip], timeout=180)
            run_script("c2", [ip], timeout=180)
        else:
            print(f"  [-] 22 closed — skip SSH/lateral/C2")

        # Botnet
        if 80 in open_ports or 443 in open_ports:
            print(f"  [*] 80/443 open → botnet")
            run_script("botnet", [ip], timeout=180)
        else:
            print(f"  [-] 80/443 closed — skip botnet")

        # FTP placeholder
        if 21 in open_ports:
            print(f"  [*] 21 open → FTP not implemented yet")
        else:
            print(f"  [-] 21 closed — skip FTP")

    print("\n[+] Phase 2 complete")


# ---------------------------------------------------------------------------
# One full cycle
# ---------------------------------------------------------------------------
def cycle(subnet: str):
    # Discover who is up + which key ports are open
    targets = discover_targets(subnet, SCAN_PORTS)

    # Phase 1: general port scan for ALL of them
    phase_portscan_all(targets)

    # Phase 2: specialized attacks
    phase_followup_attacks(targets)


def main():
    parser = argparse.ArgumentParser(description="Lab attack orchestrator")
    parser.add_argument("--subnet", default=DEFAULT_SUBNET)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--sleep", type=int, default=LOOP_SLEEP_SEC)
    args = parser.parse_args()

    print("=" * 60)
    print(" LAB ATTACK ORCHESTRATOR")
    print("=" * 60)
    print(f"  Subnet      : {args.subnet}")
    print(f"  Scripts dir : {RED_TEAM_DIR}")
    print(f"  Ground dir  : {GROUND_DIR}")
    print(f"  Port range  : {PORT_SCAN_START}-{PORT_SCAN_END}")
    print(f"  Mode        : {'once' if args.once else f'loop every {args.sleep}s'}")
    print("=" * 60)
    print("Lab / VMware isolated networks only.")
    print("=" * 60)

    try:
        while True:
            print(f"\n[*] Cycle start @ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            cycle(args.subnet)
            if args.once:
                break
            print(f"\n[*] Sleeping {args.sleep}s … (Ctrl+C to stop)")
            time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("\n[*] Stopped by user.")


if __name__ == "__main__":
    main()
