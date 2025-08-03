#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === VM DESTRUCTION SCRIPT (v3.0 - Centralized Variables) ===
# === SKRYPT DO USUWANIA MASZYN WIRTUALNYCH (v3.0 - Zmienne Scentralizowane) ===
# =====================================================================================

import os
import subprocess
import yaml

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'


# =====================================================================================
# === HELPER FUNCTIONS (bez zmian) ===
# === FUNKCJE POMOCNICZE (no changes) ===
# =====================================================================================

def run_command(command):
    """
    English: Helper function to run system commands and print their output in real-time.
    Polski:  Funkcja pomocnicza do uruchamiania poleceń systemowych i drukowania ich wyjścia w czasie rzeczywistym.
    """
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding='utf-8')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        return process.poll()
    except Exception as e:
        print(f"❌ An unexpected error occurred / Wystąpił nieoczekiwany błąd: {e}")
        return 1


def load_config():
    """
    English: Loads config.yaml and returns a dictionary of available VMs.
    Polski:  Wczytuje config.yaml i zwraca słownik dostępnych maszyn wirtualnych.
    """
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError):
        return None


def remove_from_config(vm_key_to_delete):
    """
    English: Removes a given key from the config.yaml file.
    Polski:  Usuwa dany klucz z pliku config.yaml.
    """
    config_data = load_config()
    if vm_key_to_delete in config_data:
        del config_data[vm_key_to_delete]
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    print("\n" + "*" * 60)
    print(f"✅ Entry for '{vm_key_to_delete}' has been removed from {CONFIG_FILE}.")
    print(f"✅ Wpis dla '{vm_key_to_delete}' został usunięty z pliku {CONFIG_FILE}.")
    print("*" * 60)


# =====================================================================================
# === MAIN SCRIPT LOGIC (ZMODYFIKOWANA / MODIFIED) ===
# =====================================================================================

def main():
    """
    English: Main function of the VM destruction script.
    Polski:  Główna funkcja skryptu do usuwania maszyn wirtualnych.
    """
    os.system("clear || cls")
    print("=" * 60)
    print("=== TERRAFORM VM DESTRUCTION WIZARD (v3.0) ===")
    print("=== KREATOR USUWANIA MASZYN WIRTUALNYCH TERRAFORM (v3.0) ===")
    print("=" * 60)

    all_config = load_config()
    if not all_config:
        print(f"\n❌ Configuration file '{CONFIG_FILE}' does not exist or is empty.")
        print(f"❌ Plik konfiguracyjny '{CONFIG_FILE}' nie istnieje lub jest pusty.")
        return

    # --- Krok 1: Wczytaj ustawienia ---
    global_settings = all_config.get('GLOBAL_SETTINGS', {})
    gcp_settings = global_settings.get('gcp', {})
    vm_settings = global_settings.get('vm', {})

    if not all([gcp_settings, vm_settings]):
        print("\n❌ ERROR: Section 'GLOBAL_SETTINGS' in config.yaml is incomplete.")
        print("❌ BŁĄD: Sekcja 'GLOBAL_SETTINGS' w config.yaml jest niekompletna.")
        return

    # --- Krok 2: Wybierz maszynę do usunięcia ---
    vms = {k: v for k, v in all_config.items() if isinstance(v, dict) and 'name' in v}
    if not vms:
        print(f"\n❌ No machine configurations found in '{CONFIG_FILE}'.")
        print(f"❌ Nie znaleziono konfiguracji maszyn w pliku '{CONFIG_FILE}'.")
        return

    print("\nAvailable machines for deletion:")
    print("Dostępne maszyny do usunięcia:")
    for key, data in vms.items():
        print(f"  - {key}: {data['name']}")

    vm_key = input(
        "\nEnter the key of the machine to delete (e.g., VM1):\nPodaj klucz maszyny do usunięcia (np. VM1): ").strip().upper()
    if vm_key not in vms:
        print(f"\n❌ ERROR: Key '{vm_key}' not found in the configuration file.")
        print(f"❌ BŁĄD: Klucz '{vm_key}' nie został znaleziony w pliku konfiguracyjnym.")
        return

    vm_to_delete_data = vms[vm_key]
    vm_name = vm_to_delete_data['name']
    ssh_key = vm_to_delete_data.get('ssh_public_key', 'dummy-key-for-destroy')

    print("\n" + "!" * 60)
    print("!!! WARNING: This operation is irreversible and will permanently delete the VM. !!!")
    print("!!! OSTRZEŻENIE: Ta operacja jest nieodwracalna i trwale usunie maszynę wirtualną. !!!")
    print("!" * 60)
    confirm = input(
        f"\nAre you sure you want to permanently delete machine '{vm_name}' ({vm_key})? [y/N]:\nCzy na pewno chcesz trwale usunąć maszynę '{vm_name}' ({vm_key})? [t/N]: ").strip().lower()
    if confirm not in ['y', 't']:
        print("\nOperation cancelled by user / Operacja anulowana przez użytkownika.")
        return

    # --- Krok 3: Uruchom Terraform Destroy z pełnym zestawem zmiennych ---
    print(f"\n🔄 Switching to workspace '{vm_key}' for deletion...")
    print(f"🔄 Przełączanie na obszar roboczy '{vm_key}' w celu usunięcia...")
    run_command(['terraform', 'workspace', 'select', vm_key])

    print("\n--- Running Terraform Destroy ---")
    print("--- Uruchamianie Terraform Destroy ---")

    destroy_command = [
        'terraform', 'destroy', '-auto-approve',
        # Zmienne podstawowe
        f'-var=instance_name={vm_name}',
        f'-var=root_password=dummy-password',  # Hasło nie jest potrzebne do usunięcia
        f'-var=ssh_public_key={ssh_key}',
        # Zmienne z GLOBAL_SETTINGS - konieczne, aby Terraform poprawnie odczytał stan
        f'-var=gcp_project_id={gcp_settings.get("project_id")}',
        f'-var=gcp_region={gcp_settings.get("region")}',
        f'-var=gcp_zone={gcp_settings.get("zone")}',
        f'-var=vm_machine_type={vm_settings.get("machine_type")}',
        f'-var=vm_disk_image={vm_settings.get("disk_image")}',
        f'-var=vm_disk_size_gb={vm_settings.get("disk_size_gb")}',
        f'-var=vm_disk_type={vm_settings.get("disk_type")}',
        f'-var=vm_admin_user={vm_settings.get("admin_user")}',
    ]
    return_code = run_command(destroy_command)

    # --- Krok 4: Posprzątaj po udanym usunięciu ---
    if return_code == 0:
        print("\n--- ✅ Terraform Destroy completed successfully ---")
        print("--- ✅ Terraform Destroy zakończone sukcesem ---")
        remove_from_config(vm_key)

        print("\n🧹 Cleaning up workspace...")
        print("🧹 Sprzątanie obszaru roboczego...")
        run_command(['terraform', 'workspace', 'select', 'default'])
        run_command(['terraform', 'workspace', 'delete', vm_key])

        print("\n✨ Process completed successfully! ✨")
        print("✨ Proces zakończony pomyślnie! ✨")
    else:
        print(f"\n--- ❌ ERROR: Terraform Destroy failed with exit code: {return_code} ---")
        print(f"--- ❌ BŁĄD: Terraform Destroy zakończone z kodem błędu: {return_code} ---")
        print("Check the errors above. The entry in config.yaml and the workspace were not removed.")
        print("Sprawdź błędy powyżej. Wpis w config.yaml i obszar roboczy nie zostały usunięte.")


if __name__ == '__main__':
    main()