#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === DOCKER INSTALLATION SCRIPT (v5.0 - Centralized Variables) ===
# === SKRYPT INSTALACJI DOCKERA (v5.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'


# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def load_config():
    """
    English: Loads the main configuration file.
    Polski:  Wczytuje główny plik konfiguracyjny.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ ERROR: Configuration file '{CONFIG_FILE}' not found.")
        print(f"❌ BŁĄD: Plik konfiguracyjny '{CONFIG_FILE}' nie został znaleziony.")
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ ERROR: Error loading config file: {e}")
        print(f"❌ BŁĄD: Błąd ładowania pliku konfiguracyjnego: {e}")
        return None


def run_ssh_command(host_ip, user, command):
    """
    English: Runs a command on a remote machine via SSH and streams the output.
    Polski:  Uruchamia polecenie na zdalnej maszynie przez SSH i strumieniuje wyjście.
    """
    full_command = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'{user}@{host_ip}', command]
    print(f"\n🔄 Executing command on '{host_ip}'...")
    print(f"🔄 Wykonywanie polecenia na '{host_ip}'...")
    print("-" * 60)
    try:
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  [{host_ip}] > {output.strip()}")

        returncode = process.poll()
        if returncode != 0:
            print(f"❌ SSH command failed with exit code: {returncode}.")
            print(f"❌ Polecenie SSH zakończone błędem (kod: {returncode}).")
        return returncode
    except Exception as e:
        print(f"❌ An unexpected error occurred during SSH: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas SSH: {e}")
        return 1


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== DOCKER INSTALLATION SCRIPT (v5.0) ===")
    print("=== SKRYPT INSTALACJI DOCKERA (v5.0) ===")
    print("=" * 60)

    config = load_config()
    if not config: return

    # --- Krok 1: Wczytaj ustawienia ---
    global_settings = config.get('GLOBAL_SETTINGS', {})
    vm_settings = global_settings.get('vm', {})
    if not vm_settings:
        print("\n❌ ERROR: Section 'GLOBAL_SETTINGS.vm' not found in config.yaml.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS.vm' nie została znaleziona w pliku config.yaml.")
        return

    ADMIN_USER = vm_settings.get('admin_user', 'blox_tak_server_admin')

    # --- Krok 2: Wybierz maszynę docelową ---
    vms = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not vms:
        print(f"\n❌ ERROR: No VMs found in '{CONFIG_FILE}'.")
        print(f"❌ BŁĄD: Nie znaleziono maszyn w '{CONFIG_FILE}'.")
        return

    print("\nAvailable VMs / Dostępne maszyny wirtualne:")
    for key, data in vms.items():
        print(f"  - {key}: {data['name']}")

    server_key = input(
        "\nEnter the key of the VM to install Docker on:\nWprowadź klucz maszyny, na której zainstalować Dockera:\n> ").strip().upper()
    if server_key not in vms:
        print(f"\n❌ ERROR: Key '{server_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = vms[server_key]
    ssh_host_ip = server_data.get('internal_ip')

    if not ssh_host_ip:
        print(f"\n❌ ERROR: Missing 'internal_ip' for VM '{server_key}' in config.yaml.")
        print(f"   Run 'configure_peer.py' first to fetch and save the IP addresses.")
        print(f"\n❌ BŁĄD: Brak 'internal_ip' dla maszyny '{server_key}' w pliku config.yaml.")
        print("   Uruchom najpierw skrypt `configure_peer.py`, aby pobrać i zapisać adresy IP.")
        return

    print(f"\nℹ️  Connecting to VM via internal IP / Łączę z maszyną przez wewnętrzny adres IP: {ssh_host_ip}")

    # --- Krok 3: Przygotuj i uruchom skrypt instalacyjny ---
    docker_install_script = f"""
    set -e
    echo "--- Starting Docker installation ---"

    # 1. Update package index and install dependencies
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl

    # 2. Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # 3. Set up the repository
    echo \\
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \\
      $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \\
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 4. Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # 5. Add user to the 'docker' group
    sudo usermod -aG docker {ADMIN_USER}

    echo "✅ Docker installed successfully."
    """

    return_code = run_ssh_command(ssh_host_ip, ADMIN_USER, docker_install_script)

    print("\n" + "=" * 60)
    if return_code == 0:
        print("✨ DOCKER INSTALLATION FINISHED SUCCESSFULLY! ✨")
        print("✨ INSTALACJA DOCKERA ZAKOŃCZONA POMYŚLNIE! ✨")
    else:
        print("❌ DOCKER INSTALLATION FAILED. Check the output above.")
        print("❌ INSTALACJA DOCKERA NIE POWIODŁA SIĘ. Sprawdź powyższe komunikaty.")
    print("=" * 60)


if __name__ == '__main__':
    main()