#!/bin/bash
# --- FIN-OPS AUTOMATION SCRIPT ---
# --- SKRYPT AUTOMATYZACJI FIN-OPS ---

# Exit immediately if a command fails
# Zakończ natychmiast, jeśli komenda się nie powiedzie
set -e

# --- CHANGE DIRECTORY ---
# --- ZMIANA KATALOGU ---

# Move to the project folder so Python can find local files
# Przejdź do folderu projektu, aby Python znalazł lokalne pliki
cd /home/lukestridergm/PycharmProjects/FinOps/

# --- INITIALIZE ENVIRONMENT ---
# --- INICJALIZACJA ŚRODOWISKA ---

# Activate the virtual environment
# Aktywacja wirtualnego środowiska
source .venv/bin/activate

# --- EXECUTE LOGIC ---
# --- URUCHOMIENIE LOGIKI ---

# Run the VAT script
# Uruchomienie skryptu VAT
python fin-ops_F23VAT.py

echo "✅ VAT processing completed."
echo "✅ Przetwarzanie VAT zakończone."

# Run the main FinOps script
# Uruchomienie głównego skryptu FinOps
python fin-ops.py

echo "🧠 Tasks finished."
echo "🧠 Zadania zakończone."

# --- EXIT ---
# --- WYJŚCIE ---

deactivate