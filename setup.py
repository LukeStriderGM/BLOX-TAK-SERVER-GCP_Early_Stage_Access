#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === TAK SERVER REMOTE INSTALLER (v3.1 - Dependency Fix) ===
# === ZDALNY INSTALATOR TAK SERVER (v3.1 - Poprawka Zależności) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'
LOCAL_CERTS_BASE_PATH = 'gcp_tak_certs'


# =====================================================================================
# === HELPER FUNCTIONS ===
# =====================================================================================

def run_command_local(command):
    """
    English: Runs a command on the local machine.
    Polski:  Uruchamia polecenie na lokalnej maszynie.
    """
    print(f"\n🔄 Executing local command / Wykonywanie polecenia lokalnego: {' '.join(command)}")
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ Command executed successfully / Polecenie wykonane pomyślnie.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Command failed / BŁĄD: Polecenie zakończyło się błędem.")
        print(f"   Stderr: {e.stderr.strip()}")
        return False


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
        print(f"❌ ERROR: Could not load configuration file '{CONFIG_FILE}': {e}")
        print(f"❌ BŁĄD: Nie można wczytać pliku konfiguracyjnego '{CONFIG_FILE}': {e}")
        return None


def run_ssh_command(host_ip, user, command):
    """
    English: Runs a command in a non-interactive SSH session.
    Polski:  Uruchamia polecenie w sesji SSH (nieinteraktywnie).
    """
    ssh_command = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'{user}@{host_ip}', command]
    print(f"\n🔄 Executing command on '{host_ip}': {command}")
    print(f"🔄 Wykonywanie polecenia na '{host_ip}': {command}")
    try:
        # Use Popen to stream output in real-time
        process = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding='utf-8')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  [{host_ip}] > {output.strip()}")
        return process.poll()
    except Exception as e:
        print(f"❌ An unexpected error occurred during SSH: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas SSH: {e}")
        return 1


def run_ssh_interactive(host_ip, user, command):
    """
    English: Runs a command in an interactive SSH session.
    Polski:  Uruchamia polecenie w interaktywnej sesji SSH.
    """
    ssh_command = ['ssh', '-t', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'{user}@{host_ip}',
                   command]
    print(f"\n🔄 Connecting to '{host_ip}' as '{user}' to run the installation script...")
    print(f"🔄 Łączenie z '{host_ip}' jako '{user}' w celu uruchomienia skryptu instalacyjnego...")
    print(f"    COMMAND / POLECENIE: {command}")
    print("-" * 60)
    print(">>> Starting interactive SSH session. / Rozpoczynanie interaktywnej sesji SSH. <<<")
    print("-" * 60)
    try:
        process = subprocess.run(ssh_command, check=False)
        return process.returncode
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during SSH: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas SSH: {e}")
        return 1


# =====================================================================================
# === MAIN SCRIPT LOGIC ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== TAK SERVER REMOTE INSTALLER (v3.1) ===")
    print("=== ZDALNY INSTALATOR TAK SERVER (v3.1) ===")
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
    REMOTE_PROJECT_PATH = f'/home/{ADMIN_USER}/tak-server'

    # --- Krok 2: Wybierz serwer docelowy ---
    servers = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not servers:
        print(f"\n❌ No server configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji serwerów w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable servers for installation:")
    print("Dostępne serwery do instalacji:")
    for key, data in servers.items():
        print(f"  - {key}: {data['name']}")

    server_key = input(
        "\nSelect the server to run setup.sh on:\nWybierz serwer, na którym chcesz uruchomić setup.sh:\n> ").strip().upper()
    if server_key not in servers:
        print(f"\n❌ ERROR: Key '{server_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = servers[server_key]
    ssh_host_ip = server_data.get('internal_ip')
    if not ssh_host_ip:
        print(f"❌ ERROR: Missing 'internal_ip' for VM '{server_key}'. A VPN connection is required.")
        print(f"❌ BŁĄD: Brak 'internal_ip' dla maszyny '{server_key}'. Połączenie przez VPN jest wymagane.")
        return

    # --- Krok 3: Instalacja zależności na zdalnej maszynie (PRZYWRÓCONY) ---
    print("\n--- Step 3: Installing dependencies on the remote machine ---")
    print("--- Krok 3: Instalacja zależności na zdalnej maszynie ---")
    install_deps_command = "sudo apt-get update && sudo apt-get install -y net-tools zip"
    if run_ssh_command(ssh_host_ip, ADMIN_USER, install_deps_command) != 0:
        print("\n❌ Failed to install dependencies. Aborting.")
        print("❌ Nie udało się zainstalować zależności. Prerywam działanie.")
        return
    print("✅ Dependencies installed successfully. / Zależności zainstalowane pomyślnie.")

    # --- Krok 4: Uruchomienie skryptu setup.sh ---
    print("\n--- Step 4: Running remote TAK Server installation ---")
    print("--- Krok 4: Uruchomienie zdalnej instalacji TAK Server ---")
    remote_command = (f"sudo bash -c 'cd {REMOTE_PROJECT_PATH} && "
                      f"find scripts/ -type f -name \"*.sh\" -exec chmod +x {{}} \\; && "
                      f"./scripts/setup.sh'")
    return_code = run_ssh_interactive(ssh_host_ip, ADMIN_USER, remote_command)

    # --- Krok 5: Kopiowanie certyfikatów po udanej instalacji ---
    if return_code == 0:
        print("\n--- Step 5: Copying certificates to the local machine ---")
        print("--- Krok 5: Kopiowanie certyfikatów na maszynę lokalną ---")
        local_cert_path = os.path.join(LOCAL_CERTS_BASE_PATH, server_key)
        print(f"Creating local directory / Tworzenie lokalnego katalogu: {local_cert_path}")
        os.makedirs(local_cert_path, exist_ok=True)
        remote_cert_path = f"{REMOTE_PROJECT_PATH}/tak/certs/files/"
        scp_command = ["scp", "-r", f"{ADMIN_USER}@{ssh_host_ip}:{remote_cert_path}*", f"{local_cert_path}/"]
        run_command_local(scp_command)
    else:
        print("\n--- Step 5 skipped due to installation error. ---")
        print("--- Krok 5 pominięty z powodu błędu instalacji. ---")

    print("\n" + "=" * 60)
    if return_code == 0:
        print("✨ PROCESS FINISHED SUCCESSFULLY (Installation and Copying)!")
        print("✨ PROCES ZAKOŃCZONY POMYŚLNIE (Instalacja i Kopiowanie)!")
    else:
        print(f"❌ PROCESS FINISHED WITH AN ERROR (exit code: {return_code}).")
        print(f"❌ PROCES ZAKOŃCZONY BŁĘDEM (kod wyjścia: {return_code}).")
    print("=" * 60)


if __name__ == '__main__':
    main()