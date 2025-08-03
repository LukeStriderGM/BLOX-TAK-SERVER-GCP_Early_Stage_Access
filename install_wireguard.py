#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === WIREGUARD INSTALLATION SCRIPT (v4.0 - Centralized Variables) ===
# === SKRYPT INSTALACJI WIREGUARD (v4.0 - Zmienne Scentralizowane) ===
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

def run_command(command, capture_output=False, shell=False):
    """
    English: Runs system commands and handles their output.
    Polski:  Uruchamia polecenia systemowe i obsługuje ich wyjście.
    """
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', shell=shell
        )
        stdout, stderr = process.communicate()
        output_lines = []
        if stdout:
            lines = filter(None, stdout.strip().split('\n'))
            for line in lines:
                if capture_output:
                    output_lines.append(line)
                else:
                    print(line)
        if stderr and not capture_output:
            print(f"DEBUG/STDERR: {stderr.strip()}", file=sys.stderr)
        return process.returncode, output_lines
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd: {e}")
        return 1, []


def load_config():
    """
    English: Loads the entire config.yaml file.
    Polski:  Wczytuje cały plik config.yaml.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file '{CONFIG_FILE}' not found.")
        print(f"❌ Plik konfiguracyjny '{CONFIG_FILE}' nie został znaleziony.")
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error loading config file '{CONFIG_FILE}': {e}")
        print(f"❌ Błąd ładowania pliku konfiguracyjnego '{CONFIG_FILE}': {e}")
        return None


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== WIREGUARD INSTALLATION WIZARD (v4.0) ===")
    print("=== KREATOR INSTALACJI WIREGUARD (v4.0) ===")
    print("=" * 60)

    config = load_config()
    if not config: return

    # --- Krok 1: Wczytaj ustawienia globalne ---
    global_settings = config.get('GLOBAL_SETTINGS', {})
    vpn_settings = global_settings.get('vpn', {})
    gcp_settings = global_settings.get('gcp', {})
    vm_settings = global_settings.get('vm', {})

    if not all([vpn_settings, gcp_settings, vm_settings]):
        print("\n❌ ERROR: 'GLOBAL_SETTINGS' section in config.yaml is incomplete.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS' w config.yaml jest niekompletna.")
        return

    ADMIN_USER = vm_settings.get('admin_user', 'blox_tak_server_admin')
    PROJECT_ID = gcp_settings.get('project_id')
    ZONE = gcp_settings.get('zone')

    # --- Krok 2: Wybierz maszynę docelową ---
    vms = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not vms:
        print(f"\n❌ No server machine configurations found in '{CONFIG_FILE}'.")
        print(f"\n❌ Nie znaleziono konfiguracji maszyn serwerowych w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable server machines for WireGuard installation:")
    print("Dostępne maszyny serwerowe do instalacji WireGuard:")
    for key, data in vms.items():
        print(f"  - {key}: {data['name']}")

    vm_key = input(
        "\nEnter the key of the machine to install WireGuard on:\nPodaj klucz maszyny, na której zainstalować WireGuard:\n> ").strip().upper()
    if vm_key not in vms:
        print(f"\n❌ ERROR: Key '{vm_key}' not found in the list of available machines.")
        print(f"❌ BŁĄD: Klucz '{vm_key}' nie został znaleziony na liście dostępnych maszyn.")
        return

    vm_name = vms[vm_key]['name']

    # --- Krok 3: Przygotuj adresację IP z pliku konfiguracyjnego ---
    vm_number_match = re.search(r'\d+', vm_key)
    if not vm_number_match:
        print(f"❌ ERROR: Cannot determine server number from key '{vm_key}'. Key must contain a number (e.g., VM1).")
        print(f"❌ BŁĄD: Nie można ustalić numeru serwera z klucza '{vm_key}'. Klucz musi zawierać cyfrę (np. VM1).")
        return
    vm_number = vm_number_match.group(0)

    server_subnet_cidr = vpn_settings.get('server_subnet')  # np. '10.200.0.0/24'
    ip_prefix = '.'.join(server_subnet_cidr.split('.')[:3]) + '.'  # np. '10.200.0.'
    subnet_mask = server_subnet_cidr.split('/')[1]  # np. '24'

    server_vpn_ip = f"{ip_prefix}{vm_number}"  # np. '10.200.0.1'
    server_vpn_ip_with_mask = f"{server_vpn_ip}/{subnet_mask}"  # np. '10.200.0.1/24'

    print(f"\n🚀 Starting WireGuard installation on '{vm_name}'...")
    print(f"🚀 Rozpoczynanie instalacji WireGuard na '{vm_name}'...")
    print(f"   Server VPN IP will be set to / Adres IP serwera VPN zostanie ustawiony na: {server_vpn_ip_with_mask}")

    # --- Krok 4: Uruchom skrypt instalacyjny na zdalnej maszynie ---
    install_script = f"""
        set -e
        echo "--- Installing WireGuard / Instalacja WireGuard ---"
        sudo apt-get update -y && sudo apt-get install -y wireguard

        echo "--- Generating server keys / Generowanie kluczy serwera ---"
        sudo wg genkey | sudo tee /etc/wireguard/server_private.key | sudo wg pubkey | sudo tee /etc/wireguard/server_public.key > /dev/null
        sudo chmod 600 /etc/wireguard/server_private.key /etc/wireguard/server_public.key

        echo "--- Creating server config with IP {server_vpn_ip_with_mask} ---"
        PRIVATE_KEY=$(sudo cat /etc/wireguard/server_private.key)
        echo "[Interface]
Address = {server_vpn_ip_with_mask}
ListenPort = 51820
PrivateKey = ${{PRIVATE_KEY}}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o ens4 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o ens4 -j MASQUERADE" | sudo tee /etc/wireguard/wg0.conf > /dev/null

        echo "--- Enabling IP forwarding / Włączenie przekierowywania IP ---"
        sudo sysctl -w net.ipv4.ip_forward=1
        echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

        echo "--- Starting WireGuard service / Uruchomienie usługi WireGuard ---"
        sudo systemctl enable wg-quick@wg0
        sudo systemctl start wg-quick@wg0

        echo "✨ WireGuard installation completed successfully! / Instalacja WireGuard zakończona pomyślnie! ✨"
    """

    gcloud_ssh_command = [
        'gcloud', 'compute', 'ssh',
        f'{ADMIN_USER}@{vm_name}',
        f'--project={PROJECT_ID}',
        f'--zone={ZONE}',
        '--quiet',
        '--',
        install_script
    ]

    code, _ = run_command(gcloud_ssh_command)

    if code == 0:
        print(f"\n✅ WireGuard installation on '{vm_name}' completed successfully!")
        print(f"✅ Instalacja WireGuard na '{vm_name}' zakończona pomyślnie!")
    else:
        print(f"\n❌ ERROR: WireGuard installation on '{vm_name}' failed with exit code: {code}.")
        print(f"❌ BŁĄD: Instalacja WireGuard na '{vm_name}' zakończona błędem. Kod błędu: {code}.")


if __name__ == '__main__':
    main()