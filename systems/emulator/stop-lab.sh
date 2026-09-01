#!/bin/bash

set -e

echo "======================================"
echo "      STOPPING CYBER RANGE LAB"
echo "======================================"
echo

sudo -n containerlab destroy -t lab.clab.yml

echo
echo "[+] Removing unused Docker resources..."
docker system prune -f >/dev/null 2>&1

echo
echo "[+] Lab destroyed successfully."
