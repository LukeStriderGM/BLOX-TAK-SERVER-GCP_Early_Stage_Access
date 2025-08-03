#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === ANDROID WIREGUARD PEER CONFIGURATION SCRIPT (v2.0 - Centralized Variables) ===
# === SKRYPT KONFIGURACJI PEERA WIREGUARD DLA ANDROID (v2.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys
import json
import re

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'
QR_CODE_PATH = './'


# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def run_ssh_command(host_ip, user, command):
    """
    English: Executes a command on a remote machine using standard ssh.
    Polski:  Uruchamia polecenie na zdalnej maszynie używając standardowego ssh.
    """
    full_command = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'{user}@{host_ip}', command]
    try:
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding='utf-8')
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"❌ Error executing SSH command on {host_ip}: {stderr.strip()}")
            print(f"❌ Błąd wykonania polecenia SSH na {host_ip}: {stderr.strip()}")
        return process.returncode, stdout.strip()
    except Exception as e:
        print(f"❌ An unexpected error occurred during SSH: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas SSH: {e}")
        return 1, ""


def run_local_command(command, command_input=None):
    """
    English: Executes a local command, optionally with input data.
    Polski:  Uruchamia lokalne polecenie, opcjonalnie z danymi wejściowymi.
    """
    try:
        process = subprocess.run(command, input=command_input, capture_output=True, text=True, encoding='utf-8',
                                 check=True)
        return process.returncode, process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing local command '{' '.join(e.cmd)}': {e.stderr.strip()}")
        print(f"❌ Błąd wykonania lokalnego polecenia '{' '.join(e.cmd)}': {e.stderr.strip()}")
        return e.returncode, ""
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd: {e}")
        return 1, ""


def load_config():
    """
    English: Loads the main configuration file.
    Polski:  Wczytuje główny plik konfiguracyjny.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file '{CONFIG_FILE}' not found.")
        print(f"❌ Plik konfiguracyjny '{CONFIG_FILE}' nie został znaleziony.")
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error loading config file '{CONFIG_FILE}': {e}")
        print(f"❌ Błąd ładowania pliku konfiguracyjnego '{CONFIG_FILE}': {e}")
        return None


def save_config(config_data):
    """
    English: Saves configuration data back to the YAML file.
    Polski:  Zapisuje dane konfiguracyjne z powrotem do pliku YAML.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error saving config file '{CONFIG_FILE}': {e}")
        print(f"❌ Błąd zapisu pliku konfiguracyjnego '{CONFIG_FILE}': {e}")


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== ANDROID WIREGUARD PEER WIZARD (v2.0) ===")
    print("=== KREATOR PEERA WIREGUARD DLA ANDROID (v2.0) ===")
    print("=" * 60)

    config = load_config()
    if not config: return

    # --- Krok 1: Wczytaj ustawienia ---
    global_settings = config.get('GLOBAL_SETTINGS', {})
    gcp_settings = global_settings.get('gcp', {})
    vm_settings = global_settings.get('vm', {})
    vpn_settings = global_settings.get('vpn', {})

    if not all([gcp_settings, vm_settings, vpn_settings]):
        print("\n❌ ERROR: 'GLOBAL_SETTINGS' section in config.yaml is incomplete.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS' w config.yaml jest niekompletna.")
        return

    ADMIN_USER = vm_settings.get('admin_user', 'blox_tak_server_admin')
    PROJECT_ID = gcp_settings.get('project_id')
    ZONE = gcp_settings.get('zone')
    EUD_SUBNET_PREFIX = vpn_settings.get('eud_subnet_prefix')
    SERVER_SUBNET_CIDR = vpn_settings.get('server_subnet')

    # --- Krok 2: Wybierz serwer ---
    servers = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not servers:
        print(f"\n❌ No server machine configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji maszyn serwerowych w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable servers:")
    print("Dostępne serwery:")
    for key, data in servers.items():
        print(f"  - {key}: {data['name']}")

    server_key = input("\nSelect server:\nWybierz serwer:\n> ").strip().upper()
    if server_key not in servers:
        print(f"\n❌ ERROR: Key '{server_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{server_key}' nie został znaleziony.")
        return

    server_data = servers[server_key]
    instance_name = server_data.get('name')
    ssh_host_ip = server_data.get('internal_ip')
    server_external_ip = server_data.get('external_ip')

    if not all([instance_name, ssh_host_ip, server_external_ip]):
        print(
            f"\n❌ ERROR: Configuration for '{server_key}' is incomplete. Missing 'name', 'internal_ip', or 'external_ip'.")
        print(f"   Run configure_peer.py first to fetch IP addresses.")
        print(
            f"❌ BŁĄD: Konfiguracja dla '{server_key}' jest niekompletna. Brakuje 'name', 'internal_ip' lub 'external_ip'.")
        print(f"   Uruchom najpierw configure_peer.py, aby pobrać adresy IP.")
        return

    # --- Krok 3: Przygotuj adresację IP ---
    vm_number_match = re.search(r'\d+', server_key)
    if not vm_number_match:
        print(f"❌ ERROR: Cannot determine server number from key '{server_key}'.")
        print(f"❌ BŁĄD: Nie można ustalić numeru serwera z klucza '{server_key}'.")
        return
    vm_number = vm_number_match.group(0)

    # Adres IP serwera w sieci VPN
    server_ip_prefix = '.'.join(SERVER_SUBNET_CIDR.split('.')[:3]) + '.'
    server_vpn_ip = f"{server_ip_prefix}{vm_number}"
    print(f"ℹ️  Server address on the VPN network / Adres serwera w sieci VPN: {server_vpn_ip}")

    # Automatyczne generowanie nazwy i IP klienta
    last_octet = server_data.get('last_eud_octet', 0)
    new_octet = last_octet + 1
    client_name = f"EUD{new_octet}"
    client_vpn_ip = f"{EUD_SUBNET_PREFIX}{new_octet}"

    print(f"\n🚀 Configuring new peer '{client_name}' with IP {client_vpn_ip} for server '{instance_name}'...")
    print(f"🚀 Konfiguracja nowego peera '{client_name}' z IP {client_vpn_ip} dla serwera '{instance_name}'...")

    # --- Krok 4: Konfiguracja na serwerze przez SSH ---
    print("\n--- Step 4: Retrieving server's public key ---")
    print("--- Krok 4: Pobieranie klucza publicznego serwera ---")
    code, server_public_key = run_ssh_command(ssh_host_ip, ADMIN_USER, "sudo cat /etc/wireguard/server_public.key")
    if code != 0 or not server_public_key:
        print("❌ ERROR: Failed to retrieve server's public key.")
        print("❌ BŁĄD: Nie udało się pobrać klucza publicznego serwera.")
        return
    print("✅ Server public key retrieved / Klucz publiczny serwera pobrany.")

    print("\n--- Step 5: Generating client keys ---")
    print("--- Krok 5: Generowanie kluczy dla klienta ---")
    code, client_private_key = run_local_command(['wg', 'genkey'])
    if code != 0: return
    code, client_public_key = run_local_command(['wg', 'pubkey'], command_input=client_private_key)
    if code != 0: return
    print("✅ Client keys generated / Klucze klienta wygenerowane.")

    print("\n--- Step 6: Adding peer to server config ---")
    print("--- Krok 6: Dodawanie peera do konfiguracji serwera ---")
    peer_config_content = f"printf '\\n# Peer: {client_name}\\n[Peer]\\nPublicKey = {client_public_key}\\nAllowedIPs = {client_vpn_ip}/32\\n'"
    remote_command = f"sudo bash -c \"{peer_config_content} >> /etc/wireguard/wg0.conf\""
    code, _ = run_ssh_command(ssh_host_ip, ADMIN_USER, remote_command)
    if code != 0: return
    print("✅ Peer added to server configuration / Peer dodany do konfiguracji serwera.")

    print("\n--- Step 7: Restarting WireGuard service ---")
    print("--- Krok 7: Restartowanie usługi WireGuard ---")
    code, _ = run_ssh_command(ssh_host_ip, ADMIN_USER, "sudo systemctl restart wg-quick@wg0")
    if code != 0: return
    print("✅ WireGuard service restarted / Usługa WireGuard zrestartowana.")

    # --- Krok 8: Generowanie kodu QR ---
    print("\n--- Step 8: Creating QR code ---")
    print("--- Krok 8: Tworzenie kodu QR ---")

    # Domyślny tryb SPLIT TUNNEL (dostęp tylko do serwera przez jego IP wewn. i wewn. VPN)
    allowed_ips = f"{ssh_host_ip}/32, {server_vpn_ip}/32"
    print(f"ℹ️  Default client configuration with server-only access (AllowedIPs = {allowed_ips})")
    print(f"ℹ️  Domyślna konfiguracja klienta z dostępem tylko do serwera (AllowedIPs = {allowed_ips})")

    client_conf_content = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_vpn_ip}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_external_ip}:51820
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""
    qr_filename = os.path.join(QR_CODE_PATH, f"QR_{client_name}_{server_key}.png")
    code, _ = run_local_command(['qrencode', '-o', qr_filename, '-t', 'PNG'], command_input=client_conf_content)

    if code == 0:
        print("\n" + "=" * 60)
        print("✨ FINISHED SUCCESSFULLY! / ZAKOŃCZONO POMYŚLNIE! ✨")
        print(f"✅ QR code saved to file / Kod QR został zapisany w pliku: {os.path.abspath(qr_filename)}")
        print("\nEnglish: Now open the WireGuard app on your phone, press '+' and select 'Scan from QR code'.")
        print(
            "Polski:  Teraz otwórz aplikację WireGuard na swoim telefonie, naciśnij '+' i wybierz 'Skanuj z kodu QR'.")

        config[server_key]['last_eud_octet'] = new_octet
        save_config(config)
        print(f"\n✅ Updated 'last_eud_octet' counter for '{server_key}' to {new_octet} in the config file.")
        print(f"✅ Zaktualizowano licznik 'last_eud_octet' dla '{server_key}' na {new_octet} w pliku konfiguracyjnym.")
        print("=" * 60)
    else:
        print(
            "\n❌ ERROR: Failed to generate QR code. Make sure 'qrencode' is installed (`sudo apt-get install qrencode`).")
        print(
            "❌ BŁĄD: Nie udało się wygenerować kodu QR. Upewnij się, że program 'qrencode' jest zainstalowany (`sudo apt-get install qrencode`).")


if __name__ == '__main__':
    main()