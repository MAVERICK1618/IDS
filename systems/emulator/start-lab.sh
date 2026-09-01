#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "======================================"
echo "      CYBER RANGE LAB STARTER"
echo "======================================"

# Hosts from CLI (orchestration) or default 5
HOSTS="${1:-5}"

# Generate topology non-interactively
python3 blueprint.py "$HOSTS"

echo "[+] Deploying lab..."
containerlab deploy -t lab.clab.yml

echo "[+] Waiting for containers..."
sleep 5

echo "======================================"
echo "     RUNNING CONTAINERS"
echo "======================================"
docker ps --filter "name=clab-cyberlab"

echo "======================================"
echo "      LAB INFORMATION"
echo "======================================"
echo "Victim Network : 10.10.10.0/24"
containerlab inspect -t lab.clab.yml 2>/dev/null || true
echo "[+] Lab started successfully."
