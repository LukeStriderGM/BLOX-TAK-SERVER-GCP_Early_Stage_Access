#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === VM CREATION SCRIPT (v2.0 - Centralized Variables) ===
# === SKRYPT DO TWORZENIA MASZYN WIRTUALNYCH (v2.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import datetime
import yaml

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'
SSH_KEY_FILE = os.path.expanduser('~/.ssh/id_ed25519_sk.pub')


# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def run_command(command, capture_output=False):
    """
    English: Helper function to run system commands and print their output in real-time.
    Polski:  Funkcja pomocnicza do uruchamiania poleceń systemowych i drukowania ich wyjścia w czasie rzeczywistym.
    """
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding='utf-8')
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                if capture_output:
                    output_lines.append(line)
                else:
                    print(line)
        return_code = process.poll()
        return return_code, output_lines
    except FileNotFoundError:
        print(f"❌ ERROR: Command '{command[0]}' not found. Make sure it is installed.")
        print(f"❌ BŁĄD: Polecenie '{command[0]}' nie zostało znalezione. Upewnij się, że jest zainstalowane.")
        return 1, []
    except Exception as e:
        print(f"❌ An unexpected error occurred / Wystąpił nieoczekiwany błąd: {e}")
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


def get_ssh_key():
    """
    English: Reads the SSH public key from the default file location.
    Polski:  Odczytuje publiczny klucz SSH z domyślnej lokalizacji pliku.
    """
    if not os.path.exists(SSH_KEY_FILE):
        print(f"❌ ERROR: SSH key file not found at '{SSH_KEY_FILE}'")
        print(f"❌ BŁĄD: Nie znaleziono pliku klucza SSH w '{SSH_KEY_FILE}'")
        return None
    try:
        with open(SSH_KEY_FILE, 'r', encoding='utf-8') as f:
            key_content = f.read().strip()
            print(f"✅ Successfully loaded SSH key from '{SSH_KEY_FILE}'")
            print(f"✅ Pomyślnie załadowano klucz SSH z '{SSH_KEY_FILE}'")
            return key_content
    except IOError as e:
        print(f"❌ ERROR: Could not read SSH key file: {e}")
        print(f"❌ BŁĄD: Nie można odczytać pliku klucza SSH: {e}")
        return None


def get_next_vm_key():
    """
    English: Checks config.yaml and returns the next available key (e.g., VM3 if VM1 and VM2 exist).
    Polski:  Sprawdza config.yaml i zwraca następny dostępny klucz (np. VM3, jeśli istnieje VM1 i VM2).
    """
    if not os.path.exists(CONFIG_FILE):
        return 'VM1'
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        vm_keys = [k for k in config_data.keys() if isinstance(k, str) and k.startswith('VM')]
        if not vm_keys:
            return 'VM1'
        last_num = max([int(k.replace('VM', '')) for k in vm_keys])
        return f'VM{last_num + 1}'
    except (IOError, yaml.YAMLError, ValueError):
        return 'VM1'


def generate_credentials():
    """
    English: Generates a unique, GCP-compliant VM name and a password.
    Polski:  Generuje unikalną, zgodną z GCP nazwę maszyny wirtualnej oraz hasło.
    """
    now = datetime.datetime.now()
    timestamp_for_name = now.strftime('%Y-%m-%d-%H-%M-%S')
    vm_name = f'blox-tak-server-vm-{timestamp_for_name}'
    timestamp_for_password = now.strftime('%Y-%m-%d_%H-%M-%S')
    password = f'*P@ssw0rd_*_{timestamp_for_password}*'
    return vm_name, password


def update_config_file(vm_key, vm_name, password, ssh_key):
    """
    English: Updates config.yaml, saving the name, password, and SSH key of the machine.
    Polski:  Aktualizuje config.yaml, zapisując nazwę, hasło i klucz SSH maszyny.
    """
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
    config_data[vm_key] = {
        'name': vm_name,
        'password': password,
        'ssh_public_key': ssh_key
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    print("\n" + "*" * 60)
    print(f"✅ Configuration file '{CONFIG_FILE}' successfully updated with data for {vm_key}.")
    print(f"✅ Plik konfiguracyjny '{CONFIG_FILE}' pomyślnie zaktualizowany danymi dla {vm_key}.")
    print("*" * 60)


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    """
    English: Main function of the VM creation script.
    Polski:  Główna funkcja skryptu do tworzenia maszyn wirtualnych.
    """
    os.system("clear || cls")
    print("=" * 60)
    print("=== TERRAFORM VM CREATION WIZARD (v2.0) ===")
    print("=== KREATOR TWORZENIA MASZYN WIRTUALNYCH TERRAFORM (v2.0) ===")
    print("=" * 60)

    # --- Krok 1: Wczytaj konfigurację ---
    config = load_config()
    if not config:
        return

    # --- Krok 2: Wczytaj ustawienia globalne ---
    global_settings = config.get('GLOBAL_SETTINGS', {})
    if not global_settings:
        print("\n❌ ERROR: Section 'GLOBAL_SETTINGS' not found in config.yaml.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS' nie została znaleziona w pliku config.yaml.")
        return

    gcp_settings = global_settings.get('gcp', {})
    vm_settings = global_settings.get('vm', {})

    # --- Krok 3: Sprawdź inicjalizację Terraform ---
    if not os.path.isdir('.terraform'):
        print("\n❌ ERROR: The '.terraform' directory does not exist.")
        print("   Please run 'terraform init' in this directory before running the script.")
        print("\n❌ BŁĄD: Katalog '.terraform' nie istnieje.")
        print("   Proszę uruchomić 'terraform init' w tym katalogu przed uruchomieniem skryptu.")
        return

    # --- Krok 4: Wczytaj klucz SSH ---
    ssh_public_key = get_ssh_key()
    if not ssh_public_key:
        print("\nAborting due to missing SSH key.")
        print("Przerywam z powodu braku klucza SSH.")
        return

    # --- Krok 5: Wygeneruj dane dla nowej maszyny ---
    vm_key = get_next_vm_key()
    new_vm_name, new_password = generate_credentials()

    print(f"\n▶️  Next available key / Następny dostępny klucz: {vm_key}")
    print(f"🖥️  Generated name for the new machine / Wygenerowana nazwa dla nowej maszyny: {new_vm_name}")

    # --- Krok 6: Stwórz i przełącz na nowy obszar roboczy Terraform ---
    print(f"\n🔄 Creating and switching to workspace '{vm_key}'...")
    print(f"🔄 Tworzenie i przełączanie na obszar roboczy '{vm_key}'...")
    run_command(['terraform', 'workspace', 'new', vm_key])
    run_command(['terraform', 'workspace', 'select', vm_key])

    # --- Krok 7: Wykonaj Terraform Apply z nowymi zmiennymi ---
    print("\n--- Running Terraform Apply ---")
    print("--- Uruchamianie Terraform Apply ---")
    apply_command = [
        'terraform', 'apply', '-auto-approve',
        # Zmienne podstawowe
        f'-var=instance_name={new_vm_name}',
        f'-var=root_password={new_password}',
        f'-var=ssh_public_key={ssh_public_key}',
        # Zmienne z GLOBAL_SETTINGS
        f'-var=gcp_project_id={gcp_settings.get("project_id")}',
        f'-var=gcp_region={gcp_settings.get("region")}',
        f'-var=gcp_zone={gcp_settings.get("zone")}',
        f'-var=vm_machine_type={vm_settings.get("machine_type")}',
        f'-var=vm_disk_image={vm_settings.get("disk_image")}',
        f'-var=vm_disk_size_gb={vm_settings.get("disk_size_gb")}',
        f'-var=vm_disk_type={vm_settings.get("disk_type")}',
        f'-var=vm_admin_user={vm_settings.get("admin_user")}',
    ]
    return_code, _ = run_command(apply_command)

    # --- Krok 8: Zaktualizuj plik konfiguracyjny po sukcesie ---
    if return_code == 0:
        print("\n--- ✅ Terraform Apply completed successfully ---")
        print("--- ✅ Terraform Apply zakończone sukcesem ---")
        update_config_file(vm_key, new_vm_name, new_password, ssh_public_key)
    else:
        print(f"\n--- ❌ ERROR: Terraform Apply failed with exit code: {return_code} ---")
        print(f"--- ❌ BŁĄD: Terraform Apply zakończone z kodem błędu: {return_code} ---")
        print("The workspace was not cleaned up. Check the errors above.")
        print("Obszar roboczy nie został wyczyszczony. Sprawdź błędy powyżej.")

    # --- Krok 9: Przełącz z powrotem na domyślny obszar roboczy ---
    print("\n🔄 Switching back to the 'default' workspace...")
    print("🔄 Przełączam z powrotem na obszar roboczy 'default'...")
    run_command(['terraform', 'workspace', 'select', 'default'])

    if return_code == 0:
        print("\n✨ Process completed successfully! ✨")
        print("✨ Proces zakończony pomyślnie! ✨")


if __name__ == '__main__':
    main()