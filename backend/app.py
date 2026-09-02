"""
IDS Backend API Server
======================
Exposes all orchestration data, agent communications, ML results,
attack logs, and pipeline status via REST HTTP endpoints.

Run:
    source ~/IDS/venv/bin/activate
    pip install flask flask-cors python-dotenv
    python3 ~/IDS/backend/app.py
"""

from flask import Flask, jsonify, send_file, abort, make_response, request
from pathlib import Path
import json
import csv
import os
import re
import subprocess
from datetime import datetime
from typing import Optional, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# Load environment variables
FLASK_ENV = os.getenv("FLASK_ENV", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]

# CORS configuration
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "*")
    if "*" in ALLOWED_ORIGINS or origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin if origin != "*" else "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    return response

# ─────────────────────────────────────────────────────────────
# BASE PATHS
# ─────────────────────────────────────────────────────────────
IDS_DIR          = Path("/home/test/IDS")
ML_DIR           = IDS_DIR / "ML"
RED_TEAM_DIR     = IDS_DIR / "Red-Team"
ORCH_DIR         = IDS_DIR / "orchestration"
EMULATOR_DIR     = IDS_DIR / "emulator"

ALERTS_DIR       = ML_DIR / "alerts"
PROCESSED_DIR    = ML_DIR / "processed"
OUTPUTS_DIR      = ML_DIR / "outputs"
GROUND_DIR       = RED_TEAM_DIR / "ground"
LOGS_DIR         = ORCH_DIR / "logs"
MODELS_DIR       = ML_DIR / "models"
DATA_DIR         = ML_DIR / "data"


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def read_json(path: Path):
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def read_csv_rows(path: Path, limit: int = 500) -> list:
    if not path.is_file():
        return []
    try:
        rows = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(dict(row))
        return rows
    except Exception:
        return []


def count_csv_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except Exception:
        return 0


def read_log_tail(path: Path, lines: int = 100) -> list:
    if not path.is_file():
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:]]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# GROUP 1 — PIPELINE STATUS
# ─────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def pipeline_status():
    stop_file = ORCH_DIR / "STOP"
    pid_file  = ORCH_DIR / "orchestration.pid"
    lab_yml   = EMULATOR_DIR / "lab.clab.yml"
    live_csv  = DATA_DIR / "live-traffic.csv"
    agent_log = ORCH_DIR / "agent_messages.log"

    orchestration_running = False
    orchestration_pid     = None
    if pid_file.is_file():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            orchestration_running = True
            orchestration_pid     = pid
        except (ProcessLookupError, ValueError):
            pass

    capture_running = False
    try:
        result = subprocess.run(["pgrep", "-f", "live-traffic-montior.py"], capture_output=True, text=True)
        capture_running = result.returncode == 0
    except Exception:
        pass

    lab_running = False
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=clab-cyberlab", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        lab_running = bool(result.stdout.strip())
    except Exception:
        lab_running = lab_yml.is_file()

    return jsonify({
        "orchestration_running":   orchestration_running,
        "orchestration_pid":       orchestration_pid,
        "lab_deployed":            lab_running,
        "traffic_capture_active":  capture_running,
        "stop_signal_present":     stop_file.exists(),
        "live_csv_rows":           count_csv_rows(live_csv),
        "agent_log_exists":        agent_log.is_file(),
        "timestamp":               datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/pipeline/checkpoints", methods=["GET"])
def pipeline_checkpoints():
    agent_log = ORCH_DIR / "agent_messages.log"
    lines     = read_log_tail(agent_log, lines=500)
    checkpoints = []
    pattern = re.compile(r"\[(\d{2}:\d{2}:\d{2})\] CHECKPOINT \[(.+?)\] → (OK|FAIL)(?: \| (.+))?")
    for line in lines:
        m = pattern.match(line)
        if m:
            checkpoints.append({
                "time":   m.group(1),
                "name":   m.group(2),
                "status": m.group(3),
                "detail": m.group(4) or ""
            })
    return jsonify({
        "total":       len(checkpoints),
        "ok_count":    sum(1 for c in checkpoints if c["status"] == "OK"),
        "fail_count":  sum(1 for c in checkpoints if c["status"] == "FAIL"),
        "checkpoints": checkpoints
    })


# ─────────────────────────────────────────────────────────────
# GROUP 2 — AGENTIC COMMUNICATION
# ─────────────────────────────────────────────────────────────

@app.route("/api/agent/messages", methods=["GET"])
def agent_messages():
    agent_log = ORCH_DIR / "agent_messages.log"
    lines     = read_log_tail(agent_log, lines=1000)
    messages  = []
    time_pattern = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] (.+)$")
    for line in lines:
        m = time_pattern.match(line)
        if m:
            text = m.group(2)
            if "CHECKPOINT" in text:
                msg_type = "checkpoint"
                status   = "ok" if "→ OK" in text else "fail"
            elif "→" in text:
                msg_type = "node_transition"
                status   = "info"
            elif "error" in text.lower():
                msg_type = "error"
                status   = "error"
            else:
                msg_type = "log"
                status   = "info"
            messages.append({"time": m.group(1), "text": text, "type": msg_type, "status": status})
    return jsonify({"total": len(messages), "messages": messages})


@app.route("/api/agent/nodes", methods=["GET"])
def agent_nodes():
    agent_log = ORCH_DIR / "agent_messages.log"
    lines     = read_log_tail(agent_log, lines=500)
    nodes = [
        {"id": "ask_hosts",          "label": "Host Planner",        "description": "Determines how many hosts to deploy", "order": 1},
        {"id": "deploy_lab",         "label": "Lab Deployer",        "description": "Runs blueprint.py + containerlab",    "order": 2},
        {"id": "start_capture",      "label": "Traffic Capture",     "description": "Starts live-traffic-montior.py",      "order": 3},
        {"id": "parallel_attack_ml", "label": "Attack + ML Runner",  "description": "Red-Team attacks + ML detectors",     "order": 4},
        {"id": "ground_truth",       "label": "Validator",           "description": "Compares GT vs Predictions",          "order": 5},
        {"id": "feedback_node",      "label": "Feedback Controller", "description": "Detects misses, triggers retraining", "order": 6},
        {"id": "finalize",           "label": "Coordinator",         "description": "Writes final agent log",              "order": 7},
    ]
    cp_pattern = re.compile(r"CHECKPOINT \[(.+?)\] → (OK|FAIL)")
    statuses   = {}
    for line in lines:
        m = cp_pattern.search(line)
        if m:
            statuses[m.group(1)] = m.group(2)
    checkpoint_map = {
        "ask_hosts":          ["ask_hosts"],
        "deploy_lab":         ["blueprint", "deploy_lab"],
        "start_capture":      ["capture"],
        "parallel_attack_ml": ["attack", "parallel"],
        "ground_truth":       ["ground_truth"],
        "feedback_node":      ["feedback_node"],
        "finalize":           ["finalize"],
    }
    for node in nodes:
        keys    = checkpoint_map.get(node["id"], [])
        results = [statuses.get(k) for k in keys if k in statuses]
        if not results:
            node["status"] = "pending"
        elif all(r == "OK" for r in results):
            node["status"] = "ok"
        elif any(r == "FAIL" for r in results):
            node["status"] = "fail"
        else:
            node["status"] = "pending"
    return jsonify({"nodes": nodes})


# ─────────────────────────────────────────────────────────────
# GROUP 3 — ALERTS
# ─────────────────────────────────────────────────────────────

@app.route("/api/alerts", methods=["GET"])
def all_alerts():
    alert_files = sorted(ALERTS_DIR.glob("*.json"))
    all_items   = []
    for f in alert_files:
        data = read_json(f)
        if data is None:
            continue
        if isinstance(data, list):
            for item in data:
                item["_source_file"] = f.name
                all_items.append(item)
        elif isinstance(data, dict):
            data["_source_file"] = f.name
            all_items.append(data)
    all_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"total": len(all_items), "alerts": all_items})


@app.route("/api/alerts/<detector_name>", methods=["GET"])
def alerts_by_detector(detector_name):
    alert_file = ALERTS_DIR / f"{detector_name}-alert.json"
    data = read_json(alert_file)
    if data is None:
        return jsonify({"error": f"No alert file for: {detector_name}", "alerts": []}), 404
    if isinstance(data, list):
        return jsonify({"total": len(data), "detector": detector_name, "alerts": data})
    return jsonify({"total": 1, "detector": detector_name, "alerts": [data]})


# ─────────────────────────────────────────────────────────────
# GROUP 4 — ML PREDICTIONS
# ─────────────────────────────────────────────────────────────

@app.route("/api/predictions", methods=["GET"])
def all_predictions():
    pred_files = sorted(PROCESSED_DIR.glob("*-predictions.csv"))
    result     = []
    for f in pred_files:
        rows  = read_csv_rows(f, limit=5)
        count = count_csv_rows(f)
        result.append({"detector": f.stem.replace("-predictions", ""), "file": f.name, "total_rows": count, "samples": rows})
    return jsonify({"detectors": result})


@app.route("/api/predictions/<detector_name>", methods=["GET"])
def predictions_by_detector(detector_name):
    pred_file = PROCESSED_DIR / f"{detector_name}-predictions.csv"
    if not pred_file.is_file():
        return jsonify({"error": f"No predictions for: {detector_name}", "rows": []}), 404
    rows  = read_csv_rows(pred_file, limit=500)
    count = count_csv_rows(pred_file)
    return jsonify({"detector": detector_name, "total_rows": count, "showing": len(rows), "rows": rows})


# ─────────────────────────────────────────────────────────────
# GROUP 5 — GROUND TRUTH
# ─────────────────────────────────────────────────────────────

@app.route("/api/ground-truth", methods=["GET"])
def ground_truth_summary():
    gt_files = sorted(GROUND_DIR.glob("*.csv"))
    result   = []
    for f in gt_files:
        count = count_csv_rows(f)
        rows  = read_csv_rows(f, limit=3)
        result.append({"attack_type": f.stem, "file": f.name, "total_rows": count, "samples": rows})
    return jsonify({"total_attack_types": len(result), "attacks": result})


@app.route("/api/ground-truth/<attack_type>", methods=["GET"])
def ground_truth_by_type(attack_type):
    gt_file = GROUND_DIR / f"{attack_type}.csv"
    if not gt_file.is_file():
        return jsonify({"error": f"No ground truth for: {attack_type}", "rows": []}), 404
    rows  = read_csv_rows(gt_file, limit=500)
    count = count_csv_rows(gt_file)
    return jsonify({"attack_type": attack_type, "total_rows": count, "showing": len(rows), "rows": rows})


# ─────────────────────────────────────────────────────────────
# GROUP 6 — METRICS / VALIDATION
# ─────────────────────────────────────────────────────────────

@app.route("/api/metrics", methods=["GET"])
def metrics():
    report = read_json(PROCESSED_DIR / "evaluation_report.json")
    if report is None:
        return jsonify({"error": "Evaluation report not found. Run the pipeline first."}), 404
    results = report.get("results", [])
    if results:
        avg_p  = round(sum(r["precision"] for r in results) / len(results), 4)
        avg_r  = round(sum(r["recall"]    for r in results) / len(results), 4)
        avg_f1 = round(sum(r["f1"]        for r in results) / len(results), 4)
        total_tp = sum(r["tp"] for r in results)
        total_fp = sum(r["fp"] for r in results)
        total_fn = sum(r["fn"] for r in results)
    else:
        avg_p = avg_r = avg_f1 = 0.0
        total_tp = total_fp = total_fn = 0
    return jsonify({
        "timestamp":   report.get("timestamp"),
        "overall":     {"avg_precision": avg_p, "avg_recall": avg_r, "avg_f1": avg_f1,
                        "total_tp": total_tp, "total_fp": total_fp, "total_fn": total_fn},
        "per_detector": results
    })


@app.route("/api/metrics/chart/<chart_name>", methods=["GET"])
def metrics_chart(chart_name):
    chart_file = OUTPUTS_DIR / f"eval_{chart_name}.png"
    if not chart_file.is_file():
        abort(404)
    return send_file(str(chart_file), mimetype="image/png")


# ─────────────────────────────────────────────────────────────
# GROUP 7 — LIVE TRAFFIC
# ─────────────────────────────────────────────────────────────

@app.route("/api/traffic/summary", methods=["GET"])
def traffic_summary():
    live_csv = DATA_DIR / "live-traffic.csv"
    if not live_csv.is_file():
        return jsonify({"error": "live-traffic.csv not found", "rows": 0}), 404
    rows     = read_csv_rows(live_csv, limit=10000)
    count    = count_csv_rows(live_csv)
    mod_time = datetime.utcfromtimestamp(live_csv.stat().st_mtime).isoformat() + "Z"
    size_kb  = round(live_csv.stat().st_size / 1024, 1)
    src_ips  = set()
    dst_ips  = set()
    ports    = {}
    for row in rows:
        src_ips.add(row.get("Source IP", row.get("src_ip", "")))
        dst_ips.add(row.get("Destination IP", row.get("dst_ip", "")))
        port = row.get("Destination Port", row.get("port", ""))
        if port:
            ports[port] = ports.get(port, 0) + 1
    top_ports = sorted(ports.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({
        "total_rows": count, "file_size_kb": size_kb, "last_modified": mod_time,
        "unique_src_ips": len(src_ips), "unique_dst_ips": len(dst_ips),
        "top_ports": [{"port": p, "count": c} for p, c in top_ports]
    })


@app.route("/api/traffic/live", methods=["GET"])
def traffic_live():
    live_csv = DATA_DIR / "live-traffic.csv"
    if not live_csv.is_file():
        return jsonify({"rows": [], "total": 0}), 404
    all_rows = read_csv_rows(live_csv, limit=99999)
    last_100 = all_rows[-100:] if len(all_rows) > 100 else all_rows
    return jsonify({"total": count_csv_rows(live_csv), "showing": len(last_100), "rows": last_100})


# ─────────────────────────────────────────────────────────────
# GROUP 8 — LOGS
# ─────────────────────────────────────────────────────────────

@app.route("/api/logs", methods=["GET"])
def list_logs():
    log_files = []
    for f in sorted(LOGS_DIR.glob("*.log")):
        log_files.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1),
                           "modified": datetime.utcfromtimestamp(f.stat().st_mtime).isoformat() + "Z"})
    agent_log = ORCH_DIR / "agent_messages.log"
    if agent_log.is_file():
        log_files.insert(0, {"name": "agent_messages.log",
                              "size_kb": round(agent_log.stat().st_size / 1024, 1),
                              "modified": datetime.utcfromtimestamp(agent_log.stat().st_mtime).isoformat() + "Z"})
    return jsonify({"logs": log_files})


@app.route("/api/logs/<log_name>", methods=["GET"])
def get_log(log_name):
    safe_name = Path(log_name).name
    log_file  = LOGS_DIR / safe_name
    if not log_file.is_file():
        log_file = ORCH_DIR / safe_name
    if not log_file.is_file():
        return jsonify({"error": f"Log not found: {safe_name}", "lines": []}), 404
    lines = read_log_tail(log_file, lines=200)
    return jsonify({"log_name": safe_name, "total_lines_shown": len(lines), "lines": lines})


# ─────────────────────────────────────────────────────────────
# GROUP 9 — FEEDBACK / RETRAINING
# ─────────────────────────────────────────────────────────────

@app.route("/api/feedback/status", methods=["GET"])
def feedback_status():
    missed_csv         = DATA_DIR / "missed_attacks.csv"
    ssh_threshold_file = MODELS_DIR / "ssh_thresholds.json"
    missed_count       = count_csv_rows(missed_csv)
    ssh_thresh         = read_json(ssh_threshold_file)
    agent_log          = ORCH_DIR / "agent_messages.log"
    lines              = read_log_tail(agent_log, lines=500)
    retrained          = [l for l in lines if "[RETRAIN]" in l or "RETRAINED" in l]
    return jsonify({
        "missed_attacks_count":   missed_count,
        "retraining_triggered":   missed_count > 0,
        "ssh_thresholds":         ssh_thresh or {"MIN_ATTEMPTS_FLOOR": 5, "MAX_AVG_FLOW_DURATION_SEC": 10.0},
        "retrain_log_lines":      retrained[-10:],
        "missed_attacks_file":    str(missed_csv) if missed_csv.is_file() else None
    })


@app.route("/api/feedback/missed-attacks", methods=["GET"])
def missed_attacks():
    missed_csv = DATA_DIR / "missed_attacks.csv"
    rows       = read_csv_rows(missed_csv, limit=500)
    count      = count_csv_rows(missed_csv)
    return jsonify({"total_missed": count, "showing": len(rows), "rows": rows})


# ─────────────────────────────────────────────────────────────
# GROUP 10 — LAB / EMULATOR
# ─────────────────────────────────────────────────────────────

@app.route("/api/lab/hosts", methods=["GET"])
def lab_hosts():
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=clab-cyberlab", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True, text=True, timeout=5
        )
        hosts = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                hosts.append({"name": parts[0], "status": parts[1], "image": parts[2] if len(parts) > 2 else ""})
        return jsonify({"hosts": hosts, "count": len(hosts)})
    except Exception as e:
        return jsonify({"hosts": [], "count": 0, "error": str(e)})


@app.route("/api/lab/topology", methods=["GET"])
def lab_topology():
    lab_yml       = EMULATOR_DIR / "lab.clab.yml"
    hosts_content = ""
    try:
        with open("/etc/hosts", "r") as f:
            content = f.read()
        if "CLAB-cyberlab-START" in content:
            start         = content.find("###### CLAB-cyberlab-START ######")
            end           = content.find("###### CLAB-cyberlab-END ######") + len("###### CLAB-cyberlab-END ######")
            hosts_content = content[start:end]
    except Exception:
        pass
    lab_hosts_list = []
    for line in hosts_content.splitlines():
        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                lab_hosts_list.append({"ip": parts[0], "hostname": parts[1]})
    return jsonify({
        "topology_file": str(lab_yml) if lab_yml.is_file() else None,
        "topology_yaml": lab_yml.read_text() if lab_yml.is_file() else "",
        "hosts_entries": lab_hosts_list
    })


# ─────────────────────────────────────────────────────────────
# GROUP 11 — DASHBOARD (Single Master Endpoint)
# ─────────────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    alert_counts = {}
    for f in ALERTS_DIR.glob("*.json"):
        data = read_json(f)
        if isinstance(data, list):
            alert_counts[f.stem.replace("-alert", "")] = len(data)
        elif isinstance(data, dict) and data:
            alert_counts[f.stem.replace("-alert", "")] = 1

    pred_counts = {f.stem.replace("-predictions", ""): count_csv_rows(f) for f in PROCESSED_DIR.glob("*-predictions.csv")}
    gt_counts   = {f.stem: count_csv_rows(f) for f in GROUND_DIR.glob("*.csv")}
    missed_count = count_csv_rows(DATA_DIR / "missed_attacks.csv")
    last_msgs    = read_log_tail(ORCH_DIR / "agent_messages.log", lines=10)
    report       = read_json(PROCESSED_DIR / "evaluation_report.json")
    metrics_summary = {}
    if report:
        for r in report.get("results", []):
            metrics_summary[r["name"]] = {"precision": r["precision"], "recall": r["recall"],
                                           "f1": r["f1"], "tp": r["tp"], "fp": r["fp"], "fn": r["fn"]}
    return jsonify({
        "timestamp":              datetime.utcnow().isoformat() + "Z",
        "alert_counts":           alert_counts,
        "prediction_rows":        pred_counts,
        "ground_truth_rows":      gt_counts,
        "missed_attacks":         missed_count,
        "metrics":                metrics_summary,
        "recent_agent_messages":  last_msgs,
        "live_traffic_rows":      count_csv_rows(DATA_DIR / "live-traffic.csv"),
    })


# ─────────────────────────────────────────────────────────────
# ROOT — API INDEX
# ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "IDS Backend API",
        "version": "1.0",
        "endpoints": {
            "Pipeline Status":     ["GET /api/status", "GET /api/pipeline/checkpoints"],
            "Agent Communication": ["GET /api/agent/messages", "GET /api/agent/nodes"],
            "Alerts":              ["GET /api/alerts", "GET /api/alerts/<detector>"],
            "ML Predictions":      ["GET /api/predictions", "GET /api/predictions/<detector>"],
            "Ground Truth":        ["GET /api/ground-truth", "GET /api/ground-truth/<attack>"],
            "Metrics":             ["GET /api/metrics", "GET /api/metrics/chart/<name>"],
            "Live Traffic":        ["GET /api/traffic/summary", "GET /api/traffic/live"],
            "Logs":                ["GET /api/logs", "GET /api/logs/<log_name>"],
            "Feedback/Retrain":    ["GET /api/feedback/status", "GET /api/feedback/missed-attacks"],
            "Lab/Emulator":        ["GET /api/lab/hosts", "GET /api/lab/topology"],
            "Dashboard":           ["GET /api/dashboard"],
        }
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  IDS BACKEND API SERVER")
    print(f"  Environment: {FLASK_ENV}")
    print(f"  CORS Origins: {', '.join(ALLOWED_ORIGINS)}")
    print("=" * 60)
    print("  Development URL   : http://localhost:8000")
    print("  API Index         : http://localhost:8000/")
    print("=" * 60)
    
    # Development: debug mode enabled
    # Production: use gunicorn or similar app server
    debug_mode = FLASK_ENV == "development"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode)