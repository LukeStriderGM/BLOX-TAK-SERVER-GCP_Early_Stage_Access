#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === REMOTE GDRIVE DOWNLOADER (v2.0 - Centralized Variables) ===
# === SKRYPT ZDALNEGO POBIERANIA Z GDRIVE (v2.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys
import re

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'

# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def run_ssh_command(host_ip, user, command):
    """
    English: Runs a command on a remote machine using standard ssh.
    Polski:  Uruchamia polecenie na zdalnej maszynie używając standardowego ssh.
    """
    full_command = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        f'{user}@{host_ip}',
        command
    ]
    print(f"\n🔄 Executing remote command on '{host_ip}'...")
    print(f"🔄 Wykonywanie zdalnego polecenia na '{host_ip}'...")
    print(f"    COMMAND: {command}")

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
                print(f"    [{host_ip}] > {output.strip()}")

        returncode = process.poll()
        if returncode != 0:
            print(f"❌ Error executing SSH command (exit code: {returncode}).")
            print(f"❌ Błąd wykonania polecenia SSH (kod wyjścia: {returncode}).")
        return returncode
    except FileNotFoundError:
        print("❌ ERROR: Command 'ssh' not found.")
        print("❌ BŁĄD: Polecenie 'ssh' nie zostało znalezione.")
        return 1
    except Exception as e:
        print(f"❌ An unexpected error occurred during SSH: {e}")
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
    print("=== GCP REMOTE FILE DOWNLOADER SCRIPT (v2.0) ===")
    print("=== SKRYPT ZDALNEGO POBIERANIA PLIKÓW NA MASZYNĘ GCP (v2.0) ===")
    print("=" * 60)

    config = load_config()
    if not config:
        return

    # --- Krok 1: Wczytaj ustawienia globalne ---
    global_settings = config.get('GLOBAL_SETTINGS', {})
    tak_files = global_settings.get('tak_server_files', {})
    vm_settings = global_settings.get('vm', {})

    if not all([tak_files, vm_settings]):
        print("\n❌ ERROR: Section 'GLOBAL_SETTINGS.tak_server_files' or 'GLOBAL_SETTINGS.vm' not found in config.yaml.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS.tak_server_files' lub 'GLOBAL_SETTINGS.vm' nie została znaleziona w pliku config.yaml.")
        return

    # Użyj zmiennych z konfiguracji
    TAK_SERVER_FOLDER_ID = tak_files.get('folder_id')
    TAK_ZIP_FILE_ID = tak_files.get('zip_id')
    TAK_ZIP_FILENAME = tak_files.get('zip_filename')
    TAK_SERVER_DIRNAME = "tak-server" # Można też przenieść do configu, jeśli potrzeba
    ADMIN_USER = vm_settings.get('admin_user', 'blox_tak_server_admin')

    # --- Krok 2: Wybierz serwer docelowy ---
    servers = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not servers:
        print(f"\n❌ No server configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji serwerów w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable servers:")
    print("Dostępne serwery:")
    for key, data in servers.items():
        print(f"  - {key}: {data['name']}")

    server_key = input(
        "\nSelect the server to download files to:\nWybierz serwer, na którym mają być pobrane pliki:\n> ").strip().upper()
    if server_key not in servers:
        print(f"\n❌ ERROR: Key '{server_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = servers[server_key]
    instance_name = server_data.get('name')
    ssh_host_ip = server_data.get('internal_ip')

    if not all([instance_name, ssh_host_ip]):
        print(f"\n❌ ERROR: Configuration for '{server_key}' is incomplete. Missing 'name' or 'internal_ip'.")
        print(f"❌ BŁĄD: Konfiguracja dla '{server_key}' jest niekompletna. Brakuje 'name' lub 'internal_ip'.")
        return

    # --- Krok 3: Wykonaj zdalne polecenia ---
    print(f"\n🚀 Preparing machine '{instance_name}' and downloading files...")
    print(f"🚀 Przygotowywanie maszyny '{instance_name}' i pobieranie plików...")

    remote_commands = [
        "sudo apt-get update -y",
        "sudo apt-get install -y python3-pip unzip",
        "sudo python3 -m pip install gdown",
        f"python3 -m gdown --folder {TAK_SERVER_FOLDER_ID}",
        f"python3 -m gdown --id {TAK_ZIP_FILE_ID} -O {TAK_ZIP_FILENAME}",
        f"mv {TAK_ZIP_FILENAME} {TAK_SERVER_DIRNAME}/",
        "echo '--- Folder contents / Zawartość folderu ---'",
        f"ls -l {TAK_SERVER_DIRNAME}"
    ]

    full_remote_command = " && ".join(remote_commands)
    return_code = run_ssh_command(ssh_host_ip, ADMIN_USER, full_remote_command)

    # --- Krok 4: Pokaż wynik ---
    print("\n" + "=" * 60)
    if return_code == 0:
        print("✨ FINISHED SUCCESSFULLY!")
        print("✨ ZAKOŃCZONO POMYŚLNIE!")
        print(f"✅ Files have been downloaded and prepared on machine '{instance_name}'.")
        print(f"✅ Pliki zostały pobrane i przygotowane na maszynie '{instance_name}'.")
    else:
        print("❌ OPERATION FAILED.")
        print("❌ OPERACJA ZAKOŃCZONA BŁĘDEM.")
        print("❌ Check the messages above to diagnose the issue.")
        print("❌ Sprawdź powyższe komunikaty, aby zdiagnozować problem.")
    print("=" * 60)


if __name__ == '__main__':
    main()