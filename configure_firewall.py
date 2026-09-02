#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === FIREWALL PRE-CONFIGURATION SCRIPT (v1.0 - YAML Driven) ===
# === SKRYPT PRE-KONFIGURACJI ZAPORY SIECIOWEJ (v1.0 - Sterowany YAML) ===
# =====================================================================================

import os
import subprocess
import yaml

# --- Configuration ---
# --- Konfiguracja ---
CONFIG_FILE = 'config.yaml'
FIREWALL_DIR = 'gcp_firewall_pre_conf'


# =====================================================================================
# === HELPER FUNCTIONS ===
# === FUNKCJE POMOCNICZE ===
# =====================================================================================

def run_command(command, cwd=None):
    """
    English: Helper function to run system commands and print their output in real-time.
    Polski:  Funkcja pomocnicza do uruchamiania poleceń systemowych i drukowania ich wyjścia w czasie rzeczywistym.
    """
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', cwd=cwd
        )
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
# === MAIN SCRIPT LOGIC ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== GCP FIREWALL PRE-CONFIGURATION WIZARD (v1.0) ===")
    print("=== KREATOR PRE-KONFIGURACJI ZAPORY SIECIOWEJ GCP (v1.0) ===")
    print("=" * 60)

    # --- Krok 1: Weryfikacja katalogu Terraforma ---
    if not os.path.isdir(FIREWALL_DIR):
        print(f"\n❌ ERROR: The '{FIREWALL_DIR}' directory does not exist.")
        print(f"❌ BŁĄD: Katalog '{FIREWALL_DIR}' nie istnieje.")
        return

    # --- Krok 2: Weryfikacja pliku konfiguracyjnego ---
    config = load_config()
    if not config:
        return

    global_settings = config.get('GLOBAL_SETTINGS', {})
    security_settings = global_settings.get('security', {})
    admin_ip = security_settings.get('admin_ext_ip')

    if not admin_ip:
        print("\n❌ ERROR: Missing 'admin_ext_ip' in 'GLOBAL_SETTINGS.security' (config.yaml).")
        print("❌ BŁĄD: Brak 'admin_ext_ip' w sekcji 'GLOBAL_SETTINGS.security' (config.yaml).")
        return

    print(f"\n🛡️  Target Admin IP for SSH / Docelowy adres IP Admina dla SSH: {admin_ip}")
    print(f"🔄 Initializing Terraform in '{FIREWALL_DIR}'...")
    print(f"🔄 Inicjalizacja Terraform w katalogu '{FIREWALL_DIR}'...")

    # --- Krok 3: Terraform Init ---
    init_code = run_command(['terraform', 'init'], cwd=FIREWALL_DIR)
    if init_code != 0:
        print("\n❌ ERROR: Terraform init failed.")
        print("❌ BŁĄD: Inicjalizacja Terraform nie powiodła się.")
        return

    # --- Krok 4: Terraform Apply ---
    print("\n--- Running Terraform Apply (Applying Firewall Rules) ---")
    print("--- Uruchamianie Terraform Apply (Wdrażanie reguł zapory) ---")

    apply_code = run_command(['terraform', 'apply', '-auto-approve'], cwd=FIREWALL_DIR)

    # --- Krok 5: Podsumowanie ---
    print("\n" + "=" * 60)
    if apply_code == 0:
        print("✨ FIREWALL PRE-CONFIGURATION COMPLETED SUCCESSFULLY! ✨")
        print("✨ PRE-KONFIGURACJA ZAPORY SIECIOWEJ ZAKOŃCZONA POMYŚLNIE! ✨")
        print("\nEnglish: Your GCP project is now secure. You can proceed with deploy_vm.py.")
        print("Polski:  Twój projekt GCP jest teraz bezpieczny. Możesz kontynuować z deploy_vm.py.")
    else:
        print("❌ ERROR: Failed to apply firewall rules. Check the logs above.")
        print("❌ BŁĄD: Nie udało się wdrożyć reguł zapory. Sprawdź powyższe logi.")
    print("=" * 60)


if __name__ == '__main__':
    main()