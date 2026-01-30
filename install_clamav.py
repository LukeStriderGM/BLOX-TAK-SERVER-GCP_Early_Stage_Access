#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import yaml
import sys
import time

# --- CONFIGURATION ---
CONFIG_FILE = 'config.yaml'

def load_config():
    if not os.path.exists(CONFIG_FILE): return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return yaml.safe_load(f)

def run_ssh_command(host_ip, user, command):
    # English: Execute a command via SSH
    # Polski: Wykonaj polecenie przez SSH
    full_command = ['ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{host_ip}', command]
    print(f"\n🔄 Connecting to {host_ip}...")
    try:
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None: break
            if output:
                line = output.strip()
                if "perl: warning" not in line and "LC_" not in line and line:
                    print(f"   [{host_ip}] {line}")
        return process.poll()
    except Exception as e:
        print(f"❌ SSH ERROR: {e}")
        return 1

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== CLAMAV INSTALLER (STABLE) ===")
    print("=== INSTALATOR CLAMAV (STABILNY) ===")
    print("=" * 60)

    config = load_config()
    if not config: return

    vms = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    print("\nAvailable Servers / Dostępne Serwery:")
    for k, v in vms.items(): print(f" [{k}] {v['name']}")
    
    key = input("\nSelect VM Key / Wybierz Klucz VM:\n> ").strip().upper()
    if key not in vms: return
    vm = vms[key]
    
    # English: Commands for Clean Install
    # Polski: Komendy Czystej Instalacji
    cmds = [
        "export LC_ALL=C",
        "sudo apt-get update -qq",
        "sudo apt-get install clamav clamav-daemon -y",
        "sudo systemctl stop clamav-freshclam",
        "sudo freshclam",
        "sudo systemctl start clamav-freshclam",
        "sudo systemctl enable clamav-daemon",
        "sudo systemctl restart clamav-daemon",
        "echo '⏳ Waiting for DB load (15s)...'",
        "sleep 15",
        "sudo systemctl status clamav-daemon --no-pager | grep 'Active:'"
    ]

    full_cmd = " && ".join(cmds)
    if run_ssh_command(vm['internal_ip'], vm.get('admin_user', 'blox_tak_server_admin'), full_cmd) == 0:
        print("\n✅ ClamAV Installed Successfully.")
        print("✅ ClamAV Zainstalowany Pomyślnie.")
    else:
        print("\n❌ Installation Failed.")

if __name__ == "__main__":
    main()
