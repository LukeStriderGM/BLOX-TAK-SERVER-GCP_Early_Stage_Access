#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === REMOTE GITHUB DOWNLOADER & SETUP SCRIPT FOR GCP (v10.0) ===
# === SKRYPT ZDALNEGO POBIERANIA Z GITHUB I KONFIGURACJI NA GCP (v10.0) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys
import re

# --- CONFIGURATION ---
# --- KONFIGURACJA ---
CONFIG_FILE = 'config.yaml'

# --- GITHUB RESOURCES ---
# --- ZASOBY GITHUB ---
GITHUB_RELEASE_TAG = "v1.0.0.3"
TAK_ZIP_FILENAME = "tak-server.zip"
GITHUB_ASSET_URL = f"https://github.com/LukeStriderGM/BLOX-TAK-SERVER-GCP_Early_Stage_Access/releases/download/{GITHUB_RELEASE_TAG}/{TAK_ZIP_FILENAME}"
TAK_SERVER_DIRNAME = "tak-server"

# SHA-256 Checksum for security
# Suma kontrolna SHA-256 dla bezpieczeństwa
EXPECTED_SHA256 = "2ba3d95828ac4d727b2f2413ad344ec3dc63affcc26278fa7de68f9c6f223bd0"

# =====================================================================================
# === HELPER FUNCTIONS ===
# === FUNKCJE POMOCNICZE ===
# =====================================================================================

def run_ssh_command(host_ip, user, command):
    # Prepare SSH command with timeout and safety flags
    # Przygotuj komendę SSH z limitem czasu i flagami bezpieczeństwa
    full_command = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        f'{user}@{host_ip}',
        command
    ]
    
    # Print execution status
    # Drukuj status wykonania
    print(f"\n🔄 Executing remote command on '{host_ip}'...")
    print(f"🔄 Wykonywanie zdalnego polecenia na '{host_ip}'...")

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
    except Exception as e:
        print(f"❌ Unexpected SSH error: {e}")
        print(f"❌ Nieoczekiwany błąd SSH: {e}")
        return 1

def load_config():
    # Load the main configuration file from disk
    # Wczytaj główny plik konfiguracyjny z dysku
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Configuration file '{CONFIG_FILE}' not found.")
        print(f"❌ Plik konfiguracyjny '{CONFIG_FILE}' nie został znaleziony.")
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error loading config: {e}")
        print(f"❌ Błąd ładowania konfiguracji: {e}")
        return None

# =====================================================================================
# === MAIN SCRIPT LOGIC ===
# === GŁÓWNA LOGIKA SKRYPTU ===
# =====================================================================================

def main():
    # Clear terminal screen
    # Wyczyść ekran terminala
    os.system("clear || cls")
    
    # Print script header
    # Drukuj nagłówek skryptu
    print("=" * 60)
    print("=== GCP REMOTE DOWNLOADER - GITHUB VERSION (v10.0) ===")
    print("=== ZDALNE POBIERANIE GCP - WERSJA GITHUB (v10.0) ===")
    print("=" * 60)

    servers = load_config()
    if not servers:
        return

    # Display available servers from config
    # Wyświetl dostępne serwery z konfiguracji
    print("\nAvailable servers:")
    print("Dostępne serwery:")
    for key, data in servers.items():
        if isinstance(data, dict) and 'name' in data:
            print(f"  - {key}: {data['name']}")

    # Prompt user for server selection
    # Poproś użytkownika o wybór serwera
    print(f"\n💬 Select the server to download files to:")
    print(f"💬 Wybierz serwer, na którym mają być pobrane pliki:")
    server_key = input("> ").strip().upper()
    
    if server_key not in servers:
        print(f"❌ Error: Key '{server_key}' not found.")
        print(f"❌ Błąd: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = servers[server_key]
    instance_name = server_data['name']
    server_user = server_data.get('user', 'blox_tak_server_admin')

    # Establish SSH IP address
    # Ustal adres IP do połączenia SSH
    if server_data.get('internal_ip'):
        ssh_host_ip = server_data['internal_ip']
    else:
        vm_number_match = re.search(r'\d+', server_key)
        ssh_host_ip = f"10.200.0.{vm_number_match.group(0)}"

    # Start preparation process
    # Rozpocznij proces przygotowania
    print(f"\n🚀 Preparing machine '{instance_name}'...")
    print(f"🚀 Przygotowywanie maszyny '{instance_name}'...")

    # Remote command chain
    # Ciąg zdalnych komend
    remote_commands = [
        # 1. Update and install basic tools
        # 1. Aktualizacja i instalacja podstawowych narzędzi
        "sudo apt-get update -y && sudo apt-get install -y unzip curl",
        
        # 2. Download from GitHub and verify checksum (to HOME directory)
        # 2. Pobierz z GitHuba do katalogu domowego i sprawdź sumę kontrolną
        f"curl -L -o {TAK_ZIP_FILENAME} '{GITHUB_ASSET_URL}'",
        f"echo '{EXPECTED_SHA256}  {TAK_ZIP_FILENAME}' > check.sha256",
        f"sha256sum -c check.sha256",
        
        # 3. Unzip directly in HOME directory (Archive contains 'tak-server/' folder already)
        # 3. Rozpakuj bezpośrednio w katalogu domowym (Archiwum samo w sobie ma folder 'tak-server/')
        f"unzip -o {TAK_ZIP_FILENAME}",
        
        # 4. Straighten structure (just in case the zip unzips to tak-server/tak-server) & Set permissions
        # 4. Zabezpieczenie przed podwójnym folderem (jeśli wystąpi) i nadawanie uprawnień
        f"[ -d \"{TAK_SERVER_DIRNAME}/{TAK_SERVER_DIRNAME}\" ] && mv {TAK_SERVER_DIRNAME}/{TAK_SERVER_DIRNAME}/* {TAK_SERVER_DIRNAME}/ 2>/dev/null && rmdir {TAK_SERVER_DIRNAME}/{TAK_SERVER_DIRNAME} 2>/dev/null || true",
        f"chmod +x {TAK_SERVER_DIRNAME}/scripts/*.sh 2>/dev/null || true",
        
        # 5. Cleanup and verify
        # 5. Sprzątanie i weryfikacja
        f"rm -f check.sha256 {TAK_ZIP_FILENAME}",
        f"ls -F {TAK_SERVER_DIRNAME}"
    ]
    
    # Execute commands connected by logical AND
    # Wykonaj komendy połączone logicznym AND
    full_remote_command = " && ".join(remote_commands)
    return_code = run_ssh_command(ssh_host_ip, server_user, full_remote_command)

    # Print final status report
    # Drukuj końcowy raport statusu
    print("\n" + "=" * 60)
    if return_code == 0:
        print(f"✅ Finished successfully! Single '{TAK_SERVER_DIRNAME}' directory ready.")
        print(f"✅ Zakończono pomyślnie! Pojedynczy katalog '{TAK_SERVER_DIRNAME}' gotowy.")
    else:
        print(f"❌ Operation failed.")
        print(f"❌ Operacja zakończona błędem.")
    print("=" * 60)


if __name__ == '__main__':
    main()
