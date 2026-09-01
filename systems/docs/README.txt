IDS Project README
==================

Proof-of-concept Network Intrusion Detection System (IDS) with:
  - Containerlab network emulator (vulnerable hosts)
  - Live traffic capture (CICFlowMeter-style flows)
  - ML-based detectors (botnet, C2, port scan, SSH brute-force, lateral movement, data exfil)
  - Red-Team attack scripts + ground-truth CSVs
  - LangGraph orchestration (end-to-end start / stop)

Root structure
--------------
IDS/
├── install.txt                 # pip packages list
├── live-traffic-montior.py     # live capture + optional parallel ML trigger
├── README.txt                  # this file
│
├── orchestration/              # END-TO-END PIPELINE (LangGraph)
│   ├── ids_graph.py            # main controller: --hosts N / --stop
│   ├── logs/                   # attack.log, capture.log, detector logs
│   ├── agent_messages.log      # checkpoint / agent communication log
│   ├── STOP                    # created to signal stop
│   └── orchestration.pid
│
├── emulator/                   # NETWORK LAB
│   ├── blueprint.py            # generates lab.clab.yml (python3 blueprint.py 5)
│   ├── lab.clab.yml            # containerlab topology (auto-generated)
│   ├── ftp-host/  ssh-host/  web-host/  smbd-host/
│   └── (optional start-lab.sh / stop-lab.sh — not required if using orchestration)
│
├── ML/                         # DETECTION + VALIDATION
│   ├── Bonet-Detection.py
│   ├── C-2-Detection.py
│   ├── Data-Exfilration-Detection.py
│   ├── Lateral-Movenment.py
│   ├── Portscan-Detection.py
│   ├── Ssh-Bruteforce-Detector.py
│   ├── ground-truth.py         # predictions vs Red-Team/ground → metrics + PNG
│   ├── mitre_mapping.py        # optional MITRE ATT&CK enrichment
│   ├── data/
│   │   └── live-traffic.csv    # written by live-traffic-montior.py
│   ├── processed/              # *-predictions.csv (malicious rows only)
│   ├── alerts/                 # *-alert.json
│   ├── models/                 # saved model artifacts
│   └── outputs/                # eval_*.png, evaluation charts
│
├── Red-Team/                   # ATTACKS + GROUND TRUTH
│   ├── attack_orchestrator.py  # scan subnet + run gt-*.py by open ports
│   ├── gt-port.py
│   ├── gt-ssh.py
│   ├── gt-lateral.py
│   ├── gt-c2.py
│   ├── gt-bonet.py
│   ├── ground/                 # portscan.csv, ssh.csv, lateral.csv, c2.csv, botnet.csv
│   ├── user.txt / password.txt
│   └── mitre-out/              # optional MITRE JSON from ground truth
│
└── venv/                       # Python virtualenv (use this for all ML/capture)


Pipeline flow
-------------
1) Lab deploy
     orchestration OR manual:
       python3 emulator/blueprint.py <N>
       containerlab deploy -t emulator/lab.clab.yml
     Hosts appear on 10.10.10.0/24 (e.g. 10.10.10.101 …)

2) Live capture
     live-traffic-montior.py
       - auto-selects interface with 10.10.10.x (containerlab bridge)
       - writes ML/data/live-traffic.csv
       - every 30s can spawn ML detectors

3) Attacks (ground truth)
     Red-Team/attack_orchestrator.py --once --subnet 10.10.10.0/24
       - port scan all targets
       - if 22  → gt-ssh, gt-lateral, gt-c2
       - if 80/443 → gt-bonet
       - writes Red-Team/ground/*.csv

4) ML detection
     Each detector reads live-traffic.csv →
       ML/processed/*-predictions.csv
       ML/alerts/*-alert.json

5) Validation
     ML/ground-truth.py
       compares processed/ vs Red-Team/ground/
       writes ML/outputs/eval_*.png + metrics


How to use — FULL orchestration (recommended)
---------------------------------------------
# 0) Once: install + venv
cd ~/IDS
python3 -m venv venv
source venv/bin/activate
pip install -r install.txt          # or packages listed in install.txt
pip install langgraph langchain-core

# Passwordless capture (optional but recommended)
sudo visudo
# add line:
# test ALL=(root) NOPASSWD: /home/test/IDS/venv/bin/python3 /home/test/IDS/live-traffic-montior.py

# Fix output permissions if needed
sudo chown -R "$USER:$USER" ML/outputs ML/processed ML/alerts

# 1) Start full pipeline (hosts → lab → capture → attack → detect → validate)
rm -f orchestration/STOP
python3 orchestration/ids_graph.py --hosts 5

# 2) Stop lab + capture + child processes
python3 orchestration/ids_graph.py --stop


How to use — MANUAL steps (without LangGraph)
---------------------------------------------
# Lab
cd ~/IDS/emulator
python3 blueprint.py 5
containerlab deploy -t lab.clab.yml

# Capture (ALWAYS use venv python under sudo)
sudo /home/test/IDS/venv/bin/python3 /home/test/IDS/live-traffic-montior.py

# Attacks (other terminal)
cd ~/IDS/Red-Team
source ../venv/bin/activate
python3 attack_orchestrator.py --once --subnet 10.10.10.0/24

# Detectors
cd ~/IDS/ML
python3 Bonet-Detection.py data/live-traffic.csv
python3 Portscan-Detection.py data/live-traffic.csv
# ... other detectors

# Ground truth validation
python3 ground-truth.py
# charts → ML/outputs/


Important paths
---------------
Live CSV:        ML/data/live-traffic.csv
Predictions:     ML/processed/*-predictions.csv
Alerts:          ML/alerts/*-alert.json
Ground truth:    Red-Team/ground/*.csv
Validation PNG:  ML/outputs/eval_*.png
Orchestration:   orchestration/ids_graph.py
Agent log:       orchestration/agent_messages.log
Lab topology:    emulator/lab.clab.yml
Lab network:     10.10.10.0/24


Checkpoints (orchestration)
---------------------------
When running ids_graph.py you should see lines like:
  CHECKPOINT [ask_hosts]   → OK | hosts=5
  CHECKPOINT [blueprint]   → OK
  CHECKPOINT [deploy_lab]  → OK | lab running
  CHECKPOINT [capture]     → OK | pid=...
  CHECKPOINT [live_csv]    → OK | rows=...
  CHECKPOINT [attack]      → OK | exit=0
  CHECKPOINT [detector:…]  → OK/FAIL
  CHECKPOINT [ground_truth]→ OK
  CHECKPOINT [finalize]    → OK

If FAIL: open the matching file under orchestration/logs/


Common issues
-------------
1) ModuleNotFoundError: pandas
   Cause: used system python with sudo
   Fix:  sudo /home/test/IDS/venv/bin/python3 live-traffic-montior.py
         (NOT: sudo python3 …)

2) blueprint / start-lab asks "How many hosts?"
   Cause: interactive input still in script
   Fix:  python3 blueprint.py 5   # argv only; orchestration does this

3) Permission denied on ML/outputs/*.png
   Fix:  sudo chown -R $USER:$USER ML/outputs

4) Bridge name changes (br-xxxx)
   Fix:  live-traffic-montior.py auto-selects iface with 10.10.10.x

5) Ctrl+C does not die
   Fix:  python3 orchestration/ids_graph.py --stop
         pkill -f live-traffic-montior.py


Summary
-------
Manual pipeline:
  lab → capture CSV → detectors → alerts/predictions → ground-truth

Orchestrated pipeline (ids_graph.py --hosts N):
  HostPlanner → LabDeployer (blueprint + containerlab)
             → TrafficCapture (sudo venv monitor)
             → AttackRunner (Red-Team, 10.10.10.0/24)
             → DetectionRunner (all ML scripts)
             → Validator (ground-truth.py)
             → Coordinator (agent_messages.log)

Stop everything:
  python3 orchestration/ids_graph.py --stop