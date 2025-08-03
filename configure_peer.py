#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === ADMIN WIREGUARD PEER CONFIGURATION SCRIPT (v5.0 - Centralized Variables) ===
# === SKRYPT KONFIGURACJI PEERA WIREGUARD DLA ADMINA (v5.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import yaml
import sys
import shlex

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'


# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def run_command_local(command, password=None, capture_output=False, shell=False):
    """
    English: Executes a command on the local machine.
    Polski:  Wykonuje polecenie na lokalnej maszynie.
    """
    try:
        if shell and isinstance(command, list):
            command = shlex.join(command)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if password else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            shell=shell
        )
        stdout, stderr = process.communicate(input=password + '\n' if password else None)
        if stdout:
            if capture_output:
                return process.returncode, stdout.strip().split('\n')
            else:
                print(stdout.strip())
        if stderr and not capture_output:
            print(f"DEBUG/STDERR: {stderr.strip()}", file=sys.stderr)
        return process.returncode, [] if capture_output else None
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd: {e}")
        return 1, [] if capture_output else None


def run_command_remote(vm_name, remote_command_str, user, project_id, zone, capture_output=False):
    """
    English: Executes a command on a remote GCloud VM via SSH.
    Polski:  Wykonuje polecenie na zdalnej maszynie GCloud przez SSH.
    """
    gcloud_ssh_command = [
        'gcloud', 'compute', 'ssh',
        f'{user}@{vm_name}',
        f'--project={project_id}',
        f'--zone={zone}',
        '--quiet',
        '--',
        remote_command_str
    ]
    try:
        process = subprocess.Popen(
            gcloud_ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            shell=False
        )
        stdout, stderr = process.communicate()
        if stdout:
            if capture_output:
                return process.returncode, stdout.strip().split('\n')
            else:
                print(stdout.strip())
        if stderr and not capture_output:
            print(f"DEBUG/STDERR (Remote): {stderr.strip()}", file=sys.stderr)
        return process.returncode, [] if capture_output else None
    except Exception as e:
        print(f"❌ An unexpected error occurred during remote command execution: {e}")
        print(f"❌ Wystąpił nieoczekiwany błąd podczas wykonywania zdalnego polecenia: {e}")
        return 1, [] if capture_output else None


def load_config():
    """
    English: Loads the YAML configuration file.
    Polski:  Wczytuje plik konfiguracyjny YAML.
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


def save_config(config_data):
    """
    English: Saves the configuration data back to the YAML file.
    Polski:  Zapisuje dane konfiguracyjne z powrotem do pliku YAML.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Configuration saved to '{CONFIG_FILE}'.")
        print(f"✅ Konfiguracja zapisana w '{CONFIG_FILE}'.")
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error saving config file '{CONFIG_FILE}': {e}")
        print(f"❌ Błąd zapisu pliku konfiguracyjnego '{CONFIG_FILE}': {e}")


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== ADMIN WIREGUARD PEER WIZARD (v5.0) ===")
    print("=== KREATOR PEERA WIREGUARD DLA ADMINA (v5.0) ===")
    print("=" * 60)

    config = load_config()
    if not config: return

    # --- Krok 1: Wczytaj ustawienia ---
    local_config = config.get('LOCAL_CONFIG', {})
    global_settings = config.get('GLOBAL_SETTINGS', {})

    local_password = local_config.get('password')

    gcp_settings = global_settings.get('gcp', {})
    vm_settings = global_settings.get('vm', {})
    vpn_settings = global_settings.get('vpn', {})

    if not all([local_password, gcp_settings, vm_settings, vpn_settings]):
        print("\n❌ ERROR: 'LOCAL_CONFIG' or 'GLOBAL_SETTINGS' sections in config.yaml are incomplete.")
        print("❌ BŁĄD: Sekcje 'LOCAL_CONFIG' lub 'GLOBAL_SETTINGS' w config.yaml są niekompletne.")
        return

    ADMIN_USER = vm_settings.get('admin_user', 'blox_tak_server_admin')
    PROJECT_ID = gcp_settings.get('project_id')
    ZONE = gcp_settings.get('zone')
    ADMIN_VPN_IP = vpn_settings.get('admin_ip')

    # --- Krok 2: Wybierz maszynę docelową ---
    vms = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    if not vms:
        print(f"\n❌ No server machine configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji maszyn serwerowych w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable server machines to configure peer:")
    print("Dostępne maszyny serwerowe do konfiguracji peera:")
    for key, data in vms.items():
        print(f"  - {key}: {data['name']}")

    vm_key = input(
        "\nEnter the key of the machine to configure the admin peer on:\nPodaj klucz maszyny, na której skonfigurować peera admina:\n> ").strip().upper()
    if vm_key not in vms:
        print(f"\n❌ ERROR: Key '{vm_key}' not found.")
        print(f"❌ BŁĄD: Klucz '{vm_key}' nie został znaleziony.")
        return

    vm_name = vms[vm_key]['name']

    # --- Krok 3: Pobierz informacje o serwerze (IP, klucz publiczny) ---
    print(f"\n🔄 Retrieving server information for '{vm_name}'...")
    print(f"🔄 Pobieranie informacji o serwerze dla '{vm_name}'...")

    code, server_public_key_lines = run_command_remote(vm_name, "sudo cat /etc/wireguard/server_public.key", ADMIN_USER,
                                                       PROJECT_ID, ZONE, capture_output=True)
    if code != 0 or not server_public_key_lines:
        print(f"❌ ERROR: Failed to retrieve server public key from '{vm_name}'.")
        print(f"❌ BŁĄD: Nie udało się pobrać klucza publicznego serwera z '{vm_name}'.")
        return
    server_public_key = server_public_key_lines[0]
    print(f"✅ Server Public Key / Klucz publiczny serwera: {server_public_key}")

    get_ext_ip_cmd = ['gcloud', 'compute', 'instances', 'describe', vm_name, f'--project={PROJECT_ID}',
                      f'--zone={ZONE}', '--format=get(networkInterfaces[0].accessConfigs[0].natIP)']
    code, server_external_ip_lines = run_command_local(get_ext_ip_cmd, capture_output=True)
    if code != 0 or not server_external_ip_lines:
        print(f"❌ ERROR: Could not fetch server's external IP for '{vm_name}'.")
        print(f"❌ BŁĄD: Nie można było pobrać zewnętrznego adresu IP serwera dla '{vm_name}'.")
        return
    server_external_ip = server_external_ip_lines[0]
    print(f"✅ Server External IP / Zewnętrzny adres IP serwera: {server_external_ip}")

    get_int_ip_cmd = ['gcloud', 'compute', 'instances', 'describe', vm_name, f'--project={PROJECT_ID}',
                      f'--zone={ZONE}', '--format=get(networkInterfaces[0].networkIP)']
    code, server_internal_ip_lines = run_command_local(get_int_ip_cmd, capture_output=True)
    if code != 0 or not server_internal_ip_lines:
        print(f"❌ ERROR: Could not fetch server's internal IP for '{vm_name}'.")
        print(f"❌ BŁĄD: Nie można było pobrać wewnętrznego adresu IP serwera dla '{vm_name}'.")
        return
    server_internal_ip = server_internal_ip_lines[0]
    print(f"✅ Server Internal IP / Wewnętrzny adres IP serwera: {server_internal_ip}")

    print(f"\n🔄 Updating '{CONFIG_FILE}' with new IP addresses...")
    print(f"🔄 Aktualizacja '{CONFIG_FILE}' nowymi adresami IP...")
    config[vm_key]['external_ip'] = server_external_ip
    config[vm_key]['internal_ip'] = server_internal_ip
    save_config(config)

    # --- Krok 4: Generuj lokalne klucze admina ---
    base_client_path = '/etc/wireguard/'
    client_keys_path = os.path.join(base_client_path, f"admin_{vm_key}")
    client_conf_path = os.path.join(client_keys_path, "admin.conf")
    private_key_path = os.path.join(client_keys_path, 'admin_private.key')
    public_key_path = os.path.join(client_keys_path, 'admin_public.key')

    print(f"\n🔄 Generating WireGuard admin keys in '{client_keys_path}'...")
    print(f"🔄 Generowanie kluczy admina WireGuard w '{client_keys_path}'...")
    run_command_local(f"sudo -S mkdir -p {client_keys_path}", password=local_password, shell=True)
    run_command_local(f"sudo -S wg genkey | sudo -S tee {private_key_path} > /dev/null", password=local_password,
                      shell=True)
    run_command_local(f"sudo -S cat {private_key_path} | sudo -S wg pubkey | sudo -S tee {public_key_path} > /dev/null",
                      password=local_password, shell=True)

    code, client_public_key_lines = run_command_local(f"sudo -S cat {public_key_path}", password=local_password,
                                                      capture_output=True, shell=True)
    if code != 0 or not client_public_key_lines: return
    client_public_key = client_public_key_lines[0]
    print(f"✅ Admin Public Key / Klucz publiczny admina: {client_public_key}")

    code, client_private_key_lines = run_command_local(f"sudo -S cat {private_key_path}", password=local_password,
                                                       capture_output=True, shell=True)
    if code != 0 or not client_private_key_lines: return
    client_private_key = client_private_key_lines[0]

    # --- Krok 5: Dodaj peera admina do serwera WireGuard ---
    print(f"\n🔄 Adding admin peer to WireGuard configuration on '{vm_name}'...")
    print(f"🔄 Dodawanie peera admina do konfiguracji WireGuard na '{vm_name}'...")

    admin_vpn_ip_no_mask = ADMIN_VPN_IP.split('/')[0]
    peer_config_content = f"\\n# Peer: Admin for {vm_key}\\n[Peer]\\nPublicKey = {client_public_key}\\nAllowedIPs = {admin_vpn_ip_no_mask}/32\\n"
    remote_command = f"sudo printf '{peer_config_content}' | sudo tee -a /etc/wireguard/wg0.conf"
    code, _ = run_command_remote(vm_name, remote_command, ADMIN_USER, PROJECT_ID, ZONE)
    if code != 0: return

    print(f"✅ Admin peer ({admin_vpn_ip_no_mask}) added to server's WireGuard configuration.")
    print(f"✅ Peer admina ({admin_vpn_ip_no_mask}) dodany do konfiguracji serwera.")

    # --- Krok 6: Zrestartuj WireGuard na serwerze i utwórz lokalną konfigurację ---
    print(f"\n🔄 Restarting WireGuard service on '{vm_name}'...")
    print(f"🔄 Ponowne uruchamianie usługi WireGuard na '{vm_name}'...")
    code, _ = run_command_remote(vm_name, "sudo systemctl restart wg-quick@wg0", ADMIN_USER, PROJECT_ID, ZONE)
    if code != 0: return
    print(f"✅ WireGuard service restarted on '{vm_name}'.")
    print(f"✅ Usługa WireGuard pomyślnie ponownie uruchomiona na '{vm_name}'.")

    print(f"\n🔄 Creating WireGuard admin configuration file at '{client_conf_path}'...")
    print(f"🔄 Tworzenie pliku konfiguracyjnego admina WireGuard w '{client_conf_path}'...")

    allowed_ips_for_peer = "0.0.0.0/0, ::/0"  # Pełny tunel dla admina
    client_conf_content = f"""
[Interface]
# Admin Client for {vm_key}
PrivateKey = {client_private_key}
Address = {ADMIN_VPN_IP}
ListenPort = 51820
DNS = 8.8.8.8

[Peer]
# Server: {vm_name}
PublicKey = {server_public_key}
Endpoint = {server_external_ip}:51820
AllowedIPs = {allowed_ips_for_peer}
PersistentKeepalive = 25
""".strip()

    write_client_conf_cmd = f"echo '{client_conf_content}' | sudo -S tee {client_conf_path} > /dev/null"
    code, _ = run_command_local(write_client_conf_cmd, password=local_password, shell=True)
    if code != 0: return

    print(f"✅ WireGuard admin configuration saved to '{client_conf_path}'.")
    print(f"✅ Konfiguracja admina WireGuard zapisana w '{client_conf_path}'.")
    print("\n✨ Admin peer configuration completed successfully! ✨")
    print("✨ Konfiguracja peera admina zakończona pomyślnie! ✨")
    print(f"\nTo enable the client, run / Aby włączyć klienta, uruchom:")
    print(f"  sudo wg-quick up {client_conf_path}")
    print(f"\nTo disable, run / Aby wyłączyć, uruchom:")
    print(f"  sudo wg-quick down {client_conf_path}")


if __name__ == '__main__':
    main()