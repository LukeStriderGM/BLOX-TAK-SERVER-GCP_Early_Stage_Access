#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =====================================================================================
# === FIREWALL PRE-CONFIGURATION DESTROY SCRIPT (v1.0) ===
# === SKRYPT USUWAJĄCY PRE-KONFIGURACJĘ ZAPORY (v1.0) ===
# =====================================================================================

import os
import subprocess

# --- Configuration ---
# --- Konfiguracja ---
FIREWALL_DIR = 'gcp_firewall_pre_conf'


# =====================================================================================
# === HELPER FUNCTIONS ===
# === FUNKCJE POMOCNICZE ===
# =====================================================================================

def run_command(command, cwd=None):
    """
    English: Helper function to run system commands and print their output in real-time.
    Polski:  Funkcja pomocnicza do uruchamiania poleceń systemowych i drukowania ich wyjścia.
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


# =====================================================================================
# === MAIN SCRIPT LOGIC ===
# =====================================================================================

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== GCP FIREWALL TEARDOWN WIZARD (v1.0) ===")
    print("=== KREATOR USUWANIA ZAPORY SIECIOWEJ GCP (v1.0) ===")
    print("=" * 60)

    # --- Krok 1: Weryfikacja katalogu Terraforma ---
    if not os.path.isdir(FIREWALL_DIR):
        print(f"\n❌ ERROR: The '{FIREWALL_DIR}' directory does not exist.")
        print(f"❌ BŁĄD: Katalog '{FIREWALL_DIR}' nie istnieje.")
        return

    print(f"🔄 Initializing Terraform in '{FIREWALL_DIR}'...")
    print(f"🔄 Inicjalizacja Terraform w katalogu '{FIREWALL_DIR}'...")

    # --- Krok 2: Terraform Init ---
    init_code = run_command(['terraform', 'init'], cwd=FIREWALL_DIR)
    if init_code != 0:
        print("\n❌ ERROR: Terraform init failed.")
        print("❌ BŁĄD: Inicjalizacja Terraform nie powiodła się.")
        return

    # --- Krok 3: Terraform Destroy ---
    print("\n--- Running Terraform Destroy (Removing Firewall Rules) ---")
    print("--- Uruchamianie Terraform Destroy (Usuwanie reguł zapory) ---")

    destroy_code = run_command(['terraform', 'destroy', '-auto-approve'], cwd=FIREWALL_DIR)

    # --- Krok 4: Podsumowanie ---
    print("\n" + "=" * 60)
    if destroy_code == 0:
        print("✨ FIREWALL TEARDOWN COMPLETED SUCCESSFULLY! ✨")
        print("✨ USUWANIE ZAPORY SIECIOWEJ ZAKOŃCZONE POMYŚLNIE! ✨")
    else:
        print("❌ ERROR: Failed to destroy firewall rules. Check the logs above.")
        print("❌ BŁĄD: Nie udało się usunąć reguł zapory. Sprawdź powyższe logi.")
    print("=" * 60)


if __name__ == '__main__':
    main()