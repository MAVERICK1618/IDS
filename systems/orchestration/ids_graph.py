"""
IDS Full Pipeline Orchestration (LangGraph)
===========================================
No start-lab.sh / stop-lab.sh.

  python3 orchestration/ids_graph.py --hosts 5
  python3 orchestration/ids_graph.py --stop
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from shutil import which
from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ORCH_DIR = Path(__file__).resolve().parent
IDS_DIR = ORCH_DIR.parent
EMULATOR = IDS_DIR / "emulator"
ML_DIR = IDS_DIR / "ML"
RED_TEAM = IDS_DIR / "Red-Team"
STOP_FILE = ORCH_DIR / "STOP"
PID_FILE = ORCH_DIR / "orchestration.pid"
LOG_DIR = ORCH_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

PYTHON = sys.executable
DEFAULT_HOSTS = 5
LAB_YML = EMULATOR / "lab.clab.yml"
DEPLOY_TIMEOUT = 900

_child_pids: List[int] = []


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class IDSState(TypedDict, total=False):
    hosts: int
    lab_up: bool
    capture_pid: Optional[int]
    attack_ok: bool
    detectors_ok: bool
    validation_ok: bool
    messages: List[str]
    error: Optional[str]
    stopped: bool


def log(state: IDSState, msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    state.setdefault("messages", []).append(line)


def checkpoint(state: IDSState, name: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    msg = f"CHECKPOINT [{name}] → {status}"
    if detail:
        msg += f" | {detail}"
    log(state, msg)


def should_stop(state: IDSState) -> bool:
    if state.get("stopped"):
        return True
    if STOP_FILE.exists():
        state["stopped"] = True
        return True
    return False


def venv_python() -> str:
    py = IDS_DIR / "venv" / "bin" / "python3"
    return str(py) if py.is_file() else PYTHON


def track_pid(pid: int) -> None:
    _child_pids.append(pid)


def kill_tracked() -> None:
    for pid in list(_child_pids):
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    _child_pids.clear()
    for pat in (
        "live-traffic-montior.py",
        "live-traffic-monitor.py",
        "attack_orchestrator.py",
        "Bonet-Detection.py",
        "C-2-Detection.py",
        "Portscan-Detection.py",
        "Ssh-Bruteforce-Detector.py",
        "Lateral-Movenment.py",
        "Data-Exfilration-Detection.py",
    ):
        try:
            subprocess.run(["pkill", "-f", pat], capture_output=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def node_ask_hosts(state: IDSState) -> IDSState:
    if should_stop(state):
        checkpoint(state, "ask_hosts", False, "stopped")
        return state

    hosts = state.get("hosts") or DEFAULT_HOSTS
    if sys.stdin.isatty() and "hosts" not in state:
        try:
            raw = input(f"How many hosts to deploy? [{DEFAULT_HOSTS}]: ").strip()
            if raw:
                hosts = max(1, int(raw))
        except Exception:
            hosts = DEFAULT_HOSTS

    state["hosts"] = hosts
    log(state, f"HostPlanner → deploy {hosts} host(s)")
    checkpoint(state, "ask_hosts", True, f"hosts={hosts}")
    return state


def node_deploy_lab(state: IDSState) -> IDSState:
    """blueprint.py HOSTS + containerlab deploy (no start-lab.sh)."""
    if should_stop(state):
        checkpoint(state, "deploy_lab", False, "stopped")
        return state

    hosts = state.get("hosts", DEFAULT_HOSTS)
    log(state, f"LabDeployer → blueprint + containerlab ({hosts} hosts)")

    blueprint = EMULATOR / "blueprint.py"
    if not blueprint.is_file():
        state["error"] = f"blueprint.py not found: {blueprint}"
        state["lab_up"] = False
        checkpoint(state, "deploy_lab", False, state["error"])
        return state

    r = subprocess.run(
        [PYTHON, str(blueprint), str(hosts)],
        cwd=str(EMULATOR),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        state["error"] = f"blueprint failed: {r.stderr or r.stdout}"
        state["lab_up"] = False
        checkpoint(state, "blueprint", False, state["error"])
        return state
    log(state, (r.stdout or "").strip() or "blueprint ok")
    checkpoint(state, "blueprint", True, f"hosts={hosts}")

    if not LAB_YML.is_file():
        state["error"] = f"lab.clab.yml missing: {LAB_YML}"
        state["lab_up"] = False
        checkpoint(state, "deploy_lab", False, state["error"])
        return state

    clab = which("containerlab") or which("clab")
    if not clab:
        state["error"] = "containerlab not found in PATH"
        state["lab_up"] = False
        checkpoint(state, "deploy_lab", False, state["error"])
        return state

    log(state, f"LabDeployer → {clab} deploy -t lab.clab.yml")
    try:
        r = subprocess.run(
            [clab, "deploy", "-t", str(LAB_YML)],
            cwd=str(EMULATOR),
            timeout=DEPLOY_TIMEOUT,
        )
        ok = r.returncode == 0
        state["lab_up"] = ok
        if not ok:
            state["error"] = f"containerlab deploy exit {r.returncode}"
            checkpoint(state, "deploy_lab", False, state["error"])
            log(state, "Continuing pipeline anyway")
        else:
            checkpoint(state, "deploy_lab", True, "lab running")
            time.sleep(5)
    except subprocess.TimeoutExpired:
        state["lab_up"] = False
        state["error"] = "containerlab deploy timed out"
        checkpoint(state, "deploy_lab", False, state["error"])

    return state


def node_start_capture(state: IDSState) -> IDSState:
    if should_stop(state):
        checkpoint(state, "capture", False, "stopped")
        return state

    monitor = IDS_DIR / "live-traffic-montior.py"
    if not monitor.is_file():
        monitor = IDS_DIR / "live-traffic-monitor.py"
    if not monitor.is_file():
        state["error"] = "live-traffic monitor not found"
        checkpoint(state, "capture", False, state["error"])
        return state

    py = venv_python()
    log(state, f"TrafficCapture → sudo {py} {monitor.name}")

    proc = subprocess.Popen(
        ["sudo", "-n", py, str(monitor)],
        cwd=str(IDS_DIR),
        stdout=open(LOG_DIR / "capture.log", "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    track_pid(proc.pid)
    time.sleep(2)

    if proc.poll() is not None:
        log(state, "sudo -n failed — retrying sudo")
        proc = subprocess.Popen(
            ["sudo", py, str(monitor)],
            cwd=str(IDS_DIR),
            stdout=open(LOG_DIR / "capture.log", "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        track_pid(proc.pid)
        time.sleep(2)

    alive = proc.poll() is None
    state["capture_pid"] = proc.pid
    checkpoint(
        state,
        "capture",
        alive,
        f"pid={proc.pid} python={py} log={LOG_DIR / 'capture.log'}",
    )
    time.sleep(5)
    return state


def node_parallel_attack_and_ml(state: IDSState) -> IDSState:
    if should_stop(state):
        checkpoint(state, "parallel", False, "stopped before start")
        return state

    log(state, "AttackRunner + DetectionRunner → start")
    py = venv_python()
    live_csv = ML_DIR / "data" / "live-traffic.csv"

    # Checkpoint: live CSV
    if live_csv.is_file():
        try:
            with open(live_csv) as f:
                n = max(sum(1 for _ in f) - 1, 0)
        except Exception:
            n = -1
        checkpoint(state, "live_csv", n > 0, f"rows={n} path={live_csv}")
    else:
        checkpoint(state, "live_csv", False, f"missing {live_csv}")

    attack_ok = False
    det_ok = True

    # --- Attack ---
    orch = RED_TEAM / "attack_orchestrator.py"
    if not orch.is_file():
        checkpoint(state, "attack", False, "attack_orchestrator.py missing")
    else:
        log(state, "  → attack_orchestrator.py --once --subnet 10.10.10.0/24")
        log_path = LOG_DIR / "attack.log"
        try:
            p = subprocess.Popen(
                [py, str(orch), "--once", "--subnet", "10.10.10.0/24"],
                cwd=str(RED_TEAM),
                stdout=open(log_path, "w"),
                stderr=subprocess.STDOUT,
            )
            track_pid(p.pid)
            t0 = time.time()
            while p.poll() is None:
                if should_stop(state):
                    p.kill()
                    checkpoint(state, "attack", False, "stopped by user")
                    break
                elapsed = int(time.time() - t0)
                if elapsed > 1200:
                    p.kill()
                    checkpoint(state, "attack", False, f"timeout 1200s log={log_path}")
                    break
                if elapsed > 0 and elapsed % 30 == 0:
                    log(state, f"  … attack still running ({elapsed}s)")
                time.sleep(2)
            else:
                attack_ok = p.returncode == 0
                checkpoint(
                    state,
                    "attack",
                    attack_ok,
                    f"exit={p.returncode} log={log_path}",
                )
        except Exception as e:
            checkpoint(state, "attack", False, str(e))

    state["attack_ok"] = attack_ok

    if should_stop(state):
        state["detectors_ok"] = False
        checkpoint(state, "parallel", False, "stopped after attack")
        return state

    # --- Detectors ---
    detectors = [
        "Bonet-Detection.py",
        "C-2-Detection.py",
        "Data-Exfilration-Detection.py",
        "Lateral-Movenment.py",
        "Portscan-Detection.py",
        "Ssh-Bruteforce-Detector.py",
    ]
    procs = []
    for name in detectors:
        path = ML_DIR / name
        if not path.is_file():
            checkpoint(state, f"detector:{name}", False, "file missing")
            det_ok = False
            continue
        cmd = [py, str(path)]
        if live_csv.is_file():
            cmd.append(str(live_csv))
        log(state, f"  → {name}")
        lp = LOG_DIR / f"{name}.log"
        p = subprocess.Popen(
            cmd,
            cwd=str(ML_DIR),
            stdout=open(lp, "w"),
            stderr=subprocess.STDOUT,
        )
        track_pid(p.pid)
        procs.append((name, p, lp))

    for name, p, lp in procs:
        try:
            rc = p.wait(timeout=180)
            ok = rc == 0
            if not ok:
                det_ok = False
            detail = f"exit={rc} log={lp}"
            if not ok and lp.is_file():
                try:
                    tail = lp.read_text(errors="ignore").strip().splitlines()[-3:]
                    detail += " | " + " / ".join(tail)
                except Exception:
                    pass
            checkpoint(state, f"detector:{name}", ok, detail)
        except subprocess.TimeoutExpired:
            p.kill()
            det_ok = False
            checkpoint(state, f"detector:{name}", False, "timeout 180s")

    state["detectors_ok"] = det_ok
    checkpoint(
        state,
        "parallel",
        attack_ok and det_ok,
        f"attack={attack_ok} detectors={det_ok}",
    )
    return state


def node_ground_truth(state: IDSState) -> IDSState:
    gt = ML_DIR / "ground-truth.py"
    if not gt.is_file():
        gt = ML_DIR / "validate_ground_truth.py"
    if not gt.is_file():
        checkpoint(state, "ground_truth", False, "script missing")
        state["validation_ok"] = False
        return state

    (ML_DIR / "outputs").mkdir(parents=True, exist_ok=True)
    py = venv_python()
    log(state, "Validator → ground-truth comparison")
    try:
        r = subprocess.run(
            [py, str(gt)],
            cwd=str(ML_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )
        ok = r.returncode == 0
        state["validation_ok"] = ok
        detail = "OK" if ok else (r.stderr or r.stdout or f"exit={r.returncode}")[:400]
        checkpoint(state, "ground_truth", ok, detail)
    except Exception as e:
        state["validation_ok"] = False
        checkpoint(state, "ground_truth", False, str(e))
    return state


def node_feedback(state: IDSState) -> IDSState:
    log(state, "Feedback → error detection / retraining / model validation")
    py = venv_python()
    
    # Run feedback controller
    print("\n============================================================")
    print("CHECKPOINT [feedback]")
    print("============================================================")
    r = subprocess.run([py, str(ML_DIR / "feedback_controller.py")], cwd=str(ML_DIR), capture_output=False)
    ok = r.returncode == 0
    checkpoint(state, "feedback_node", ok)
    
    # Update state for final summary
    state["feedback_status"] = "RETRAINED" if ok else "ERROR"
    return state

def node_finalize(state: IDSState) -> IDSState:
    log(state, "Coordinator → pipeline finished")
    log(state, f"  hosts={state.get('hosts')} lab_up={state.get('lab_up')}")
    log(state, f"  capture_pid={state.get('capture_pid')}")
    log(state, f"  attack_ok={state.get('attack_ok')} detectors_ok={state.get('detectors_ok')}")
    log(state, f"  validation_ok={state.get('validation_ok')}")
    if state.get("error"):
        log(state, f"  error={state['error']}")

    msg_path = ORCH_DIR / "agent_messages.log"
    with open(msg_path, "w", encoding="utf-8") as f:
        for m in state.get("messages", []):
            f.write(m + "\n")
    checkpoint(state, "finalize", True, f"messages → {msg_path}")
    return state


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
def build_graph():
    g = StateGraph(IDSState)
    g.add_node("ask_hosts", node_ask_hosts)
    g.add_node("deploy_lab", node_deploy_lab)
    g.add_node("start_capture", node_start_capture)
    g.add_node("parallel_attack_ml", node_parallel_attack_and_ml)
    g.add_node("ground_truth", node_ground_truth)
    g.add_node("feedback_node", node_feedback)
    g.add_node("finalize", node_finalize)

    g.set_entry_point("ask_hosts")
    g.add_edge("ask_hosts", "deploy_lab")
    g.add_edge("deploy_lab", "start_capture")
    g.add_edge("start_capture", "parallel_attack_ml")
    g.add_edge("parallel_attack_ml", "ground_truth")
    g.add_edge("ground_truth", "feedback_node")
    g.add_edge("feedback_node", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


# ---------------------------------------------------------------------------
# Start / Stop
# ---------------------------------------------------------------------------
def destroy_lab() -> None:
    clab = which("containerlab") or which("clab")
    if not clab:
        print("[stop] containerlab not found")
        return
    if not LAB_YML.is_file():
        print(f"[stop] No topology: {LAB_YML}")
        return
    print(f"[stop] {clab} destroy -t {LAB_YML}")
    subprocess.run(
        [clab, "destroy", "-t", str(LAB_YML), "--cleanup"],
        cwd=str(EMULATOR),
    )
    print("[stop] Lab destroyed")


def stop_orchestration() -> None:
    STOP_FILE.write_text("1")
    print(f"[stop] Wrote {STOP_FILE}")
    kill_tracked()

    if PID_FILE.is_file():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"[stop] SIGTERM orchestration pid={pid}")
        except Exception as e:
            print(f"[stop] orchestration pid: {e}")

    destroy_lab()
    print(f"[stop] Done. rm -f {STOP_FILE} before next start")


def start_orchestration(hosts: Optional[int] = None):
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    PID_FILE.write_text(str(os.getpid()))

    def _sig(signum, frame):
        print("\n[!] Signal — killing children and exiting", flush=True)
        STOP_FILE.write_text("1")
        kill_tracked()
        os._exit(1)

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    app = build_graph()
    init: IDSState = {"messages": [], "stopped": False}
    if hosts is not None:
        init["hosts"] = hosts

    print("=" * 60)
    print(" IDS LANGGRAPH ORCHESTRATION — START")
    print("=" * 60)
    final = app.invoke(init)
    print("=" * 60)
    print(" IDS LANGGRAPH ORCHESTRATION — END")
    print("=" * 60)
    return final


def main():
    parser = argparse.ArgumentParser(description="IDS LangGraph orchestration")
    parser.add_argument("--stop", action="store_true", help="Destroy lab + stop processes")
    parser.add_argument("--hosts", type=int, default=None, help="Victim host count")
    args = parser.parse_args()

    if args.stop:
        stop_orchestration()
        return

    start_orchestration(hosts=args.hosts)


if __name__ == "__main__":
    main()
