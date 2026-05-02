import sys
import os
import time
import yaml
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build


# --- CONFIGURATION ---
# --- KONFIGURACJA ---
SERVICE_ACCOUNT_FILE = 'credentials.json'
SPREADSHEET_ID = '1dAM40OTxRDzltWwb_dnrfRSE98S4XxXteFhoSMBLcJE'
CONFIG_FILE = 'config.yaml'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


# --- FILE OPERATIONS ---
# --- OPERACJE NA PLIKACH ---

def load_config():
    # Load configuration from YAML file
    # Załaduj konfigurację z pliku YAML
    with open(CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)


def save_config(row):
    # Update last processed row and save to YAML
    # Zaktualizuj ostatni przetworzony wiersz i zapisz w YAML
    config = load_config()
    config['last_row'] = row + 1
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file)


# --- DATA PROCESSING ---
# --- PRZETWARZANIE DANYCH ---

def clean_and_round(val):
    # Convert string to float, handle commas and round to 2 decimal places
    # Konwertuj tekst na float, obsłuż przecinki i zaokrąglij do 2 miejsc po przecinku
    if isinstance(val, str):
        temp_val = val.replace(',', '.')
        try:
            return round(float(temp_val), 2)
        except ValueError:
            return val
    elif isinstance(val, (int, float)):
        return round(float(val), 2)
    return val


# --- MAIN LOGIC ---
# --- GŁÓWNA LOGIKA ---

def sync_finops_final_master():
    # Check if system files exist
    # Sprawdź czy pliki systemowe istnieją
    if not os.path.exists(SERVICE_ACCOUNT_FILE) or not os.path.exists(CONFIG_FILE):
        print(f"🔴 Critical: System files (JSON/YAML) missing!")
        print(f"🔴 Krytyczne: Brak plików systemowych (JSON/YAML)!")
        sys.exit(1)

    try:
        # Initialize configuration and current state
        # Inicjalizacja konfiguracji i bieżącego stanu
        config = load_config()
        row = config['last_row']
        sheet_name = config['sheet_name']
        sheet_ref = f"'{sheet_name}'"

        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_month = now.month

        # Connect to Google Sheets API
        # Połącz się z Google Sheets API
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        # --- STEP 1: MONTHLY AUDIT ---
        # --- KROK 1: AUDYT MIESIĘCZNY ---

        # Check date in previous row to detect month change
        # Sprawdź datę w poprzednim wierszu aby wykryć zmianę miesiąca
        prev_row_data = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_ref}!A{row - 1}"
        ).execute()

        prev_date_str = prev_row_data.get('values', [[None]])[0][0]

        is_new_month = True
        if prev_date_str:
            try:
                if datetime.strptime(prev_date_str, "%Y-%m-%d").month == current_month:
                    is_new_month = False
            except:
                # If parsing fails, treat as new month
                # Jeśli parsowanie zawiedzie, traktuj jako nowy miesiąc
                pass

        # --- STEP 2: PREPARE FORMULAS ---
        # --- KROK 2: PRZYGOTUJ FORMUŁY ---

        # Calculation formulas (always active)
        # Formuły obliczeniowe (zawsze aktywne)
        formula_b = f"=F{row}/$J${row}"
        formula_d = f"=F{row}/$K${row}"
        formula_h = f"=F{row}-(F{row}*0,23)"
        val_i = "-"

        # Progression logic (C, E, G) - Reset to 0 on new month
        # Logika progresji (C, E, G) - Resetuj do 0 przy nowym miesiącu
        if is_new_month:
            val_c, val_e, val_g = 0, 0, 0
            print(f"🧠 New month detected ({current_month}). Resetting C, E, G to zero.")
            print(f"🧠 Wykryto nowy miesiąc ({current_month}). Reset kolumn C, E, G do zera.")
        else:
            val_c = f"=B{row}-B{row - 1}"
            val_e = f"=D{row}-D{row - 1}"
            val_g = f"=F{row}-F{row - 1}"

        # NBP Exchange rate formulas
        # Formuły kursów NBP
        formula_j = '=WARTOŚĆ(PODSTAW(IMPORTXML("http://api.nbp.pl/api/exchangerates/rates/a/usd/?format=xml"; "//Mid"); "."; ","))'
        formula_k = '=WARTOŚĆ(PODSTAW(IMPORTXML("http://api.nbp.pl/api/exchangerates/rates/a/eur/?format=xml"; "//Mid"); "."; ","))'
        formula_l = '=IMPORTXML("http://api.nbp.pl/api/exchangerates/rates/a/usd/?format=xml"; "//EffectiveDate")'

        # --- STEP 3: BATCH INJECTION ---
        # --- KROK 3: WSTRZYKIWANIE DANYCH ---

        # Inject data skipping column F
        # Wstrzykiwanie danych z pominięciem kolumny F
        update_payload = [
            {'range': f"{sheet_ref}!A{row}:E{row}", 'values': [[today_date, formula_b, val_c, formula_d, val_e]]},
            {'range': f"{sheet_ref}!G{row}:H{row}", 'values': [[val_g, formula_h]]},
            {'range': f"{sheet_ref}!I{row}", 'values': [[val_i]]},
            {'range': f"{sheet_ref}!J{row}:L{row}", 'values': [[formula_j, formula_k, formula_l]]}
        ]

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'valueInputOption': 'USER_ENTERED', 'data': update_payload}
        ).execute()

        # --- STEP 4: WAIT & SMART FREEZE ---
        # --- KROK 4: CZEKAJ I ZAMROŹ ---

        print(f"🔄 Row {row}: Waiting 8s for calculations and IMPORTXML...")
        print(f"🔄 Wiersz {row}: Oczekiwanie 8s na przeliczenia i IMPORTXML...")
        time.sleep(8)

        # Fetch updated ranges to freeze them as values
        # Pobierz zaktualizowane zakresy aby zamrozić je jako wartości
        ranges_to_fetch = [f"{sheet_ref}!A{row}:E{row}", f"{sheet_ref}!G{row}:H{row}", f"{sheet_ref}!J{row}:L{row}"]
        results = service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID, ranges=ranges_to_fetch
        ).execute()

        freeze_payload = []
        for vr in results.get('valueRanges', []):
            raw_row = vr.get('values', [[]])[0]
            # Clean values (remove apostrophes) and round
            # Czyścimy wartości (usuwamy apostrofy) i zaokrąglamy
            cleaned_row = [clean_and_round(v) for v in raw_row]
            freeze_payload.append({'range': vr.get('range'), 'values': [cleaned_row]})

        if freeze_payload:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'valueInputOption': 'USER_ENTERED', 'data': freeze_payload}
            ).execute()

            # --- STEP 5: FINALIZE ---
            # --- KROK 5: FINALIZACJA ---
            save_config(row)
            print(f"✅ Success! Row {row} archived.")
            print(f"✅ Sukces! Wiersz {row} zarchiwizowany.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        print(f"❌ Krytyczny błąd: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sync_finops_final_master()