#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === REMOTE CLEANUP SCRIPT (v4.0 - Centralized Variables) ===
# === SKRYPT ZDALNEGO CZYSZCZENIA INSTALACJI (v4.0 - Zmienne Scentralizowane) ===
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

def run_ssh_command(host_ip, user, command, interactive=False):
    """
    English: Runs a command on a remote machine over VPN.
    Polski:  Uruchamia polecenie na zdalnej maszynie przez VPN.
    """
    tty_flag = ['-t'] if interactive else []
    full_command = ['ssh', *tty_flag, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'{user}@{host_ip}',
                    command]

    if interactive:
        print(f"\n🔄 Connecting to '{host_ip}' to run the cleanup script...")
        print(f"🔄 Łączenie z '{host_ip}' w celu uruchomienia skryptu czyszczącego...")
        print(f"   COMMAND: {command}")
        print("-" * 60)
        print(">>> Starting SSH session. All output below is from the server. <<<")
        print(">>> Rozpoczynanie sesji SSH. Wszystkie poniższe dane pochodzą z serwera. <<<")
        print("-" * 60)
    else:
        print(f"\n🔄 Executing command on '{host_ip}': {command}")
        print(f"🔄 Wykonywanie polecenia na '{host_ip}': {command}")

    try:
        process = subprocess.run(full_command, check=False)
        return process.returncode
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during SSH: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas SSH: {e}")
        return 1


def load_config():
    """
    English: Loads the main configuration file.
    Polski:  Wczytuje główny plik konfiguracyjny.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Configuration file '{CONFIG_FILE}' not found.")
        print(f"❌ Plik konfiguracyjny '{CONFIG_FILE}' nie został znaleziony.")
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error loading configuration file '{CONFIG_FILE}': {e}")
        print(f"❌ Błąd ładowania pliku konfiguracyjnego '{CONFIG_FILE}': {e}")
        return None


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== TAK SERVER VM CLEANUP SCRIPT (v4.0) ===")
    print("=== SKRYPT CZYSZCZENIA INSTALACJI TAK SERVER NA VM (v4.0) ===")
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

    # --- Krok 2: Wybierz serwer do wyczyszczenia ---
    servers = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not servers:
        print(f"\n❌ No server configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji serwerów w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable servers to clean up:")
    print("Dostępne serwery do wyczyszczenia:")
    for key, data in servers.items():
        print(f"  - {key}: {data['name']}")

    server_key = input("\nSelect the server to clean up:\nWybierz serwer, który chcesz wyczyścić:\n> ").strip().upper()
    if server_key not in servers:
        print(f"\n❌ ERROR: Key '{server_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = servers[server_key]
    ssh_host_ip = server_data.get('internal_ip')

    if not ssh_host_ip:
        print(f"\n❌ ERROR: Missing 'internal_ip' for VM '{server_key}'. A VPN connection is required.")
        print(f"❌ BŁĄD: Brak 'internal_ip' dla maszyny '{server_key}'. Wymagane jest połączenie VPN.")
        return

    # --- Krok 3: Uruchom polecenie czyszczące ---
    cleanup_command = f"sudo bash -c 'cd /home/{ADMIN_USER}/tak-server && chmod +x scripts/cleanup.sh && ./scripts/cleanup.sh'"
    return_code = run_ssh_command(ssh_host_ip, ADMIN_USER, cleanup_command, interactive=True)

    print("\n" + "=" * 60)
    if return_code == 0:
        print("✨ CLEANUP FINISHED SUCCESSFULLY!")
        print("✨ CZYSZCZENIE ZAKOŃCZONE POMYŚLNIE!")
    else:
        print("❌ CLEANUP FINISHED WITH AN ERROR.")
        print("❌ CZYSZCZENIE ZAKOŃCZONE BŁĘDEM.")
        print("❌ Check the messages above to diagnose the issue.")
        print("❌ Sprawdź powyższe komunikaty, aby zdiagnozować problem.")
    print("=" * 60)


if __name__ == '__main__':
    main()