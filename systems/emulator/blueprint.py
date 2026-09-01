import random
import sys

# ======================================================
# Number of victim hosts (CLI or interactive)
# ======================================================
if len(sys.argv) > 1:
    NUM_HOSTS = int(sys.argv[1])
else:
    NUM_HOSTS = int(input("How many victim hosts?: "))

# ======================================================
# Vulnerable services (Docker image names)
# ======================================================
services = [
    "vuln-ftp",
    "vuln-ssh",
    "vuln-web",
    "vuln-smbd",
]

# ======================================================
# Generate valid containerlab topology YAML
# ======================================================
lines = []
lines.append("name: cyberlab")
lines.append("")
lines.append("mgmt:")
lines.append("  network: cyberlab-mgmt")
lines.append("  ipv4-subnet: 10.10.10.0/24")
lines.append("")
lines.append("topology:")
lines.append("  kinds:")
lines.append("    linux:")
lines.append("      binds:")
lines.append("        - /lib/modules:/lib/modules:ro")
lines.append("")
lines.append("  nodes:")

for i in range(1, NUM_HOSTS + 1):
    service = random.choice(services)
    ip = f"10.10.10.{100 + i}"
    lines.append(f"    host{i}:")
    lines.append("      kind: linux")
    lines.append(f"      image: {service}")
    lines.append(f"      mgmt-ipv4: {ip}")
    lines.append("")

with open("lab.clab.yml", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"[+] Generated lab.clab.yml with {NUM_HOSTS} host(s).")
print(f"[+] File: lab.clab.yml")
