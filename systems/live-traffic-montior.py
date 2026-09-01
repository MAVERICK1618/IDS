"""
Live Traffic Monitor → CICFlowMeter-style CSV + parallel ML detection
Interface : auto-detect (IP 10.10.10.x, e.g. containerlab bridge)
Output    : /home/test/IDS/ML/data/live-traffic.csv
"""

import os
import sys
import csv
import time
import signal
import threading
import collections
import subprocess
from pathlib import Path

import numpy as np
from scapy.all import sniff, IP, TCP, UDP

# ---------------------------------------------------------------------------
# Auto-detect interface by 10.10.10.x
# ---------------------------------------------------------------------------
def find_iface_by_ip_prefix(prefix: str = "10.10.10.") -> str:
    """Find iface that owns an IPv4 address starting with prefix."""
    try:
        import socket
        import psutil
        for name, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if getattr(a, "family", None) == socket.AF_INET:
                    if a.address and a.address.startswith(prefix):
                        return name
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["ip", "-o", "-4", "addr", "show"], text=True
        )
        for line in out.splitlines():
            parts = line.split()
            # 5: br-xxx    inet 10.10.10.1/24 ...
            if len(parts) >= 4 and parts[2] == "inet":
                ip = parts[3].split("/")[0]
                iface = parts[1].rstrip(":")
                if ip.startswith(prefix):
                    return iface
    except Exception as e:
        print(f"[!] iface auto-detect failed: {e}")

    return "ens33"


# ---------------------------------------------------------------------------
# Paths & interface
# ---------------------------------------------------------------------------
IFACE = find_iface_by_ip_prefix("10.10.10.")
DATA_DIR = Path("/home/test/IDS/ML/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_FILE = str(DATA_DIR / "live-traffic.csv")

ML_INTERVAL = 30

HEADERS = [
    "Source IP", "Destination IP", "Source Port", "Destination Port", "Protocol",
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Total", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Fwd PSH Flags", "Bwd PSH Flags", "Fwd URG Flags", "Bwd URG Flags",
    "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s",
    "Min Packet Length", "Max Packet Length", "Packet Length Mean", "Packet Length Std", "Packet Length Variance",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count", "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
    "CWE Flag Count", "ECE Flag Count", "Down/Up Ratio", "Average Packet Size",
    "Avg Fwd Segment Size", "Avg Bwd Segment Size", "Fwd Header Length.1",
    "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets", "Subflow Fwd Bytes", "Subflow Bwd Packets", "Subflow Bwd Bytes",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward", "act_data_pkt_fwd", "min_seg_size_forward",
    "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min",
]

IDLE_THRESHOLD = 5.0
FLOW_TIMEOUT = 120.0
BULK_IAT_THRESHOLD = 0.1
BULK_MIN_PACKETS = 4

_csv_lock = threading.Lock()
_flows_lock = threading.Lock()
_stop_event = threading.Event()
_last_ml_rows = 0
_child_procs = []
_child_lock = threading.Lock()
_shutdown_done = False

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as f:
        csv.writer(f).writerow(HEADERS)


def new_flow():
    return {
        "start_time": None, "last_time": None,
        "fwd_lengths": [], "bwd_lengths": [],
        "fwd_timestamps": [], "bwd_timestamps": [],
        "all_timestamps": [], "all_lengths": [],
        "fwd_flags": collections.defaultdict(int),
        "bwd_flags": collections.defaultdict(int),
        "fwd_header_len": 0, "bwd_header_len": 0,
        "init_win_fwd": 0, "init_win_bwd": 0,
        "init_win_fwd_set": False, "init_win_bwd_set": False,
        "act_data_pkt_fwd": 0,
        "min_seg_size_fwd": None,
        "last_activity_time": None,
        "active_periods": [], "idle_periods": [],
    }


flows = collections.defaultdict(new_flow)


def get_flag_counts(packet, direction, flow):
    if not packet.haslayer(TCP):
        return
    flag_str = str(packet[TCP].flags)
    flag_map = {
        "F": "FIN", "S": "SYN", "R": "RST", "P": "PSH",
        "A": "ACK", "U": "URG", "E": "ECE", "C": "CWE",
    }
    target = flow["fwd_flags"] if direction == "fwd" else flow["bwd_flags"]
    for char, name in flag_map.items():
        if char in flag_str:
            target[name] += 1


def tcp_header_length(tcp_layer):
    return tcp_layer.dataofs * 4 if tcp_layer.dataofs else 20


def process_packet(packet):
    if not packet.haslayer(IP):
        return
    ip_layer = packet[IP]
    proto = ip_layer.proto
    src_port, dst_port = 0, 0
    tcp_win = 0
    ip_header_len = ip_layer.ihl * 4 if ip_layer.ihl else 20

    if packet.haslayer(TCP):
        tcp_layer = packet[TCP]
        src_port, dst_port = tcp_layer.sport, tcp_layer.dport
        tcp_win = tcp_layer.window
        header_len = ip_header_len + tcp_header_length(tcp_layer)
    elif packet.haslayer(UDP):
        src_port, dst_port = packet[UDP].sport, packet[UDP].dport
        header_len = ip_header_len + 8
    else:
        return

    src_ip, dst_ip = ip_layer.src, ip_layer.dst
    pkt_len = len(packet)
    current_time = float(packet.time)

    flow_key = (src_ip, dst_ip, src_port, dst_port, proto)
    rev_flow_key = (dst_ip, src_ip, dst_port, src_port, proto)

    with _flows_lock:
        if flow_key in flows or rev_flow_key not in flows:
            direction = "fwd"
            current_key = flow_key
        else:
            direction = "bwd"
            current_key = rev_flow_key

        flow = flows[current_key]

        if flow["start_time"] is not None:
            time_diff = current_time - flow["last_activity_time"]
            if time_diff > IDLE_THRESHOLD:
                active_dur = flow["last_activity_time"] - flow["start_time"]
                if active_dur > 0:
                    flow["active_periods"].append(active_dur)
                flow["idle_periods"].append(time_diff)
                flow["start_time"] = current_time
        else:
            flow["start_time"] = current_time

        if packet.haslayer(TCP):
            if direction == "fwd" and not flow["init_win_fwd_set"]:
                flow["init_win_fwd"] = tcp_win
                flow["init_win_fwd_set"] = True
            elif direction == "bwd" and not flow["init_win_bwd_set"]:
                flow["init_win_bwd"] = tcp_win
                flow["init_win_bwd_set"] = True

        flow["last_activity_time"] = current_time
        flow["last_time"] = current_time
        flow["all_timestamps"].append(current_time)
        flow["all_lengths"].append(pkt_len)
        get_flag_counts(packet, direction, flow)

        payload_len = max(pkt_len - header_len, 0)
        if direction == "fwd":
            flow["fwd_lengths"].append(pkt_len)
            flow["fwd_timestamps"].append(current_time)
            flow["fwd_header_len"] += header_len
            if payload_len > 0:
                flow["act_data_pkt_fwd"] += 1
            if packet.haslayer(TCP):
                seg_size = tcp_header_length(packet[TCP])
                if flow["min_seg_size_fwd"] is None or seg_size < flow["min_seg_size_fwd"]:
                    flow["min_seg_size_fwd"] = seg_size
        else:
            flow["bwd_lengths"].append(pkt_len)
            flow["bwd_timestamps"].append(current_time)
            flow["bwd_header_len"] += header_len

        should_export = False
        if packet.haslayer(TCP):
            flags = packet[TCP].flags
            if flags.F or flags.R:
                should_export = True
        if len(flow["all_timestamps"]) >= 500:
            should_export = True

        if should_export:
            _export_flow_locked(current_key)


def calculate_stats(data_list):
    if not data_list:
        return 0.0, 0.0, 0.0, 0.0
    arr = np.array(data_list, dtype=float)
    return float(arr.max()), float(arr.min()), float(arr.mean()), float(arr.std())


def calculate_iat(timestamps):
    if len(timestamps) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    iats = np.diff(sorted(timestamps))
    return (
        float(np.sum(iats)),
        float(np.mean(iats)),
        float(np.std(iats)),
        float(np.max(iats)),
        float(np.min(iats)),
    )


def calculate_bulk_stats(lengths, timestamps):
    if len(timestamps) < 2:
        return 0.0, 0.0, 0.0
    paired = sorted(zip(timestamps, lengths))
    ts = [p[0] for p in paired]
    ln = [p[1] for p in paired]
    iats = np.diff(ts)
    bulks, current_bulk, current_times = [], [], []
    for i, iat in enumerate(iats):
        if iat < BULK_IAT_THRESHOLD:
            if not current_bulk:
                current_bulk.append(ln[i])
                current_times.append(ts[i])
            current_bulk.append(ln[i + 1])
            current_times.append(ts[i + 1])
        else:
            if len(current_bulk) >= BULK_MIN_PACKETS:
                bulks.append((current_bulk, current_times))
            current_bulk, current_times = [], []
    if len(current_bulk) >= BULK_MIN_PACKETS:
        bulks.append((current_bulk, current_times))
    if not bulks:
        return 0.0, 0.0, 0.0
    total_bytes = sum(sum(b[0]) for b in bulks)
    total_packets = sum(len(b[0]) for b in bulks)
    total_duration = sum(
        (b[1][-1] - b[1][0]) if len(b[1]) > 1 else 1e-6 for b in bulks
    )
    avg_bytes = total_bytes / len(bulks)
    avg_pkts = total_packets / len(bulks)
    rate = total_bytes / total_duration if total_duration > 0 else 0.0
    return avg_bytes, avg_pkts, rate


def _export_flow_locked(key):
    if key not in flows:
        return
    flow = flows.pop(key)
    if not flow["all_timestamps"]:
        return

    if flow["last_activity_time"] is not None and flow["start_time"] is not None:
        final_active = flow["last_activity_time"] - flow["start_time"]
        if final_active > 0:
            flow["active_periods"].append(final_active)

    duration = float(flow["last_time"] - flow["all_timestamps"][0])
    duration = max(duration, 1e-6)

    total_fwd_pkts = len(flow["fwd_lengths"])
    total_bwd_pkts = len(flow["bwd_lengths"])
    fwd_len_sum = sum(flow["fwd_lengths"])
    bwd_len_sum = sum(flow["bwd_lengths"])

    fwd_max, fwd_min, fwd_mean, fwd_std = calculate_stats(flow["fwd_lengths"])
    bwd_max, bwd_min, bwd_mean, bwd_std = calculate_stats(flow["bwd_lengths"])
    pkt_max, pkt_min, pkt_mean, pkt_std = calculate_stats(flow["all_lengths"])
    pkt_variance = float(np.var(flow["all_lengths"])) if flow["all_lengths"] else 0.0

    flow_bytes_s = (fwd_len_sum + bwd_len_sum) / duration
    flow_pkts_s = (total_fwd_pkts + total_bwd_pkts) / duration

    f_iat_tot, f_iat_avg, f_iat_std, f_iat_max, f_iat_min = calculate_iat(flow["all_timestamps"])
    fwd_iat_tot, fwd_iat_avg, fwd_iat_std, fwd_iat_max, fwd_iat_min = calculate_iat(flow["fwd_timestamps"])
    bwd_iat_tot, bwd_iat_avg, bwd_iat_std, bwd_iat_max, bwd_iat_min = calculate_iat(flow["bwd_timestamps"])

    down_up_ratio = total_bwd_pkts / total_fwd_pkts if total_fwd_pkts > 0 else 0.0
    total_pkts = total_fwd_pkts + total_bwd_pkts
    avg_pkt_size = (fwd_len_sum + bwd_len_sum) / total_pkts if total_pkts > 0 else 0.0

    fwd_b_bytes, fwd_b_pkts, fwd_b_rate = calculate_bulk_stats(flow["fwd_lengths"], flow["fwd_timestamps"])
    bwd_b_bytes, bwd_b_pkts, bwd_b_rate = calculate_bulk_stats(flow["bwd_lengths"], flow["bwd_timestamps"])

    act_max, act_min, act_mean, act_std = calculate_stats(flow["active_periods"])
    idl_max, idl_min, idl_mean, idl_std = calculate_stats(flow["idle_periods"])

    min_seg_size_fwd = flow["min_seg_size_fwd"] if flow["min_seg_size_fwd"] is not None else 0

    row = [
        key[0], key[1], key[2], key[3], key[4],
        duration, total_fwd_pkts, total_bwd_pkts, fwd_len_sum, bwd_len_sum,
        fwd_max, fwd_min, fwd_mean, fwd_std, bwd_max, bwd_min, bwd_mean, bwd_std,
        flow_bytes_s, flow_pkts_s, f_iat_avg, f_iat_std, f_iat_max, f_iat_min,
        fwd_iat_tot, fwd_iat_avg, fwd_iat_std, fwd_iat_max, fwd_iat_min,
        bwd_iat_tot, bwd_iat_avg, bwd_iat_std, bwd_iat_max, bwd_iat_min,
        flow["fwd_flags"]["PSH"], flow["bwd_flags"]["PSH"],
        flow["fwd_flags"]["URG"], flow["bwd_flags"]["URG"],
        flow["fwd_header_len"], flow["bwd_header_len"],
        total_fwd_pkts / duration, total_bwd_pkts / duration,
        pkt_min, pkt_max, pkt_mean, pkt_std, pkt_variance,
        flow["fwd_flags"]["FIN"] + flow["bwd_flags"]["FIN"],
        flow["fwd_flags"]["SYN"] + flow["bwd_flags"]["SYN"],
        flow["fwd_flags"]["RST"] + flow["bwd_flags"]["RST"],
        flow["fwd_flags"]["PSH"] + flow["bwd_flags"]["PSH"],
        flow["fwd_flags"]["ACK"] + flow["bwd_flags"]["ACK"],
        flow["fwd_flags"]["URG"] + flow["bwd_flags"]["URG"],
        flow["fwd_flags"]["CWE"] + flow["bwd_flags"]["CWE"],
        flow["fwd_flags"]["ECE"] + flow["bwd_flags"]["ECE"],
        down_up_ratio, avg_pkt_size, fwd_mean, bwd_mean, flow["fwd_header_len"],
        fwd_b_bytes, fwd_b_pkts, fwd_b_rate, bwd_b_bytes, bwd_b_pkts, bwd_b_rate,
        total_fwd_pkts, fwd_len_sum, total_bwd_pkts, bwd_len_sum,
        flow["init_win_fwd"], flow["init_win_bwd"], flow["act_data_pkt_fwd"], min_seg_size_fwd,
        act_mean, act_std, act_max, act_min,
        idl_mean, idl_std, idl_max, idl_min,
    ]

    with _csv_lock:
        with open(CSV_FILE, mode="a", newline="") as f:
            csv.writer(f).writerow(row)


def export_flow(key):
    with _flows_lock:
        _export_flow_locked(key)


def timeout_sweeper(interval=10.0):
    while not _stop_event.is_set():
        now = time.time()
        with _flows_lock:
            stale_keys = [
                k for k, f in flows.items()
                if f["last_activity_time"] is not None
                and (now - f["last_activity_time"]) > FLOW_TIMEOUT
            ]
            for k in stale_keys:
                _export_flow_locked(k)
        _stop_event.wait(interval)


def run_ml_detectors():
    global _last_ml_rows
    PYTHON = sys.executable
    ML_SCRIPTS = [
        [PYTHON, "/home/test/IDS/ML/Bonet-Detection.py", CSV_FILE],
        [PYTHON, "/home/test/IDS/ML/Portscan-Detection.py", CSV_FILE],
        [PYTHON, "/home/test/IDS/ML/Ssh-Bruteforce-Detector.py", CSV_FILE],
        [PYTHON, "/home/test/IDS/ML/C-2-Detection.py", CSV_FILE],
        [PYTHON, "/home/test/IDS/ML/Lateral-Movenment.py", CSV_FILE],
    ]
    while not _stop_event.is_set():
        try:
            with open(CSV_FILE, "r") as f:
                rows = sum(1 for _ in f) - 1
            if rows > _last_ml_rows and ML_SCRIPTS:
                print(f"[ML] New flows detected ({rows - _last_ml_rows}). Running detectors...")
                for cmd in ML_SCRIPTS:
                    if _stop_event.is_set():
                        break
                    p = None
                    try:
                        p = subprocess.Popen(cmd)
                        with _child_lock:
                            _child_procs.append(p)
                        p.wait(timeout=180)
                    except subprocess.TimeoutExpired:
                        if p:
                            p.kill()
                    except Exception as e:
                        print(f"[ML] Detector failed: {e}")
                    finally:
                        if p is not None:
                            with _child_lock:
                                if p in _child_procs:
                                    _child_procs.remove(p)
                _last_ml_rows = rows
        except Exception as e:
            print(f"[ML] Watcher error: {e}")
        _stop_event.wait(ML_INTERVAL)


def kill_all_children():
    with _child_lock:
        for p in list(_child_procs):
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        _child_procs.clear()


def flush_all_flows():
    with _flows_lock:
        for key in list(flows.keys()):
            _export_flow_locked(key)


def handle_shutdown(signum=None, frame=None):
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True
    print("\n[*] Stopping capture, killing detectors, flushing flows...")
    _stop_event.set()
    kill_all_children()
    flush_all_flows()
    print(f"[*] Done. Data written to '{CSV_FILE}'.")
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    threading.Thread(target=timeout_sweeper, daemon=True).start()
    threading.Thread(target=run_ml_detectors, daemon=True).start()

    print(f"[*] Interface          : {IFACE}")
    print(f"[*] (auto-selected by 10.10.10.x address)")
    print(f"[*] Output CSV         : {CSV_FILE}")
    print(f"[*] ML check interval  : {ML_INTERVAL}s")
    print(f"[*] Python used        : {sys.executable}")
    print(f"[*] Sniffing... Press Ctrl+C once to stop.")

    try:
        sniff(iface=IFACE, prn=process_packet, store=0)
    finally:
        handle_shutdown()
