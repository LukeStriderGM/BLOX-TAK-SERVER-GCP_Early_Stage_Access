# --- IMPORTS ---
# --- IMPORTY ---
import os
import sys
import yaml
from google.oauth2 import service_account
from google.cloud import bigquery
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# --- KONFIGURACJA ---
SERVICE_ACCOUNT_FILE = 'credentials.json'
CONFIG_FILE = 'config.yaml'
SPREADSHEET_ID = '1dAM40OTxRDzltWwb_dnrfRSE98S4XxXteFhoSMBLcJE'

BQ_CLIENT_PROJECT = 'blox-tak-support-506512'
TARGET_COST_PROJECT = 'blox-tak-int'
BQ_TABLE = 'blox-tak-support-506512.billing_data.gcp_billing_export_v1_01DD0A_C0EEF2_052566'

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_and_inject_cost():
    # Verify system files exist
    # Sprawdź czy istnieją pliki systemowe
    if not os.path.exists(SERVICE_ACCOUNT_FILE) or not os.path.exists(CONFIG_FILE):
        print(f"🔴 Critical Error: Missing system files!", file=sys.stderr)
        print(f"🔴 Krytyczny błąd: Brak plików systemowych!", file=sys.stderr)
        sys.exit(1)

    try:
        # Load config to find the current row and sheet name
        # Załaduj konfigurację, aby znaleźć obecny wiersz i nazwę arkusza
        with open(CONFIG_FILE, 'r') as file:
            config = yaml.safe_load(file)
        row = config['last_row']
        sheet_name = config['sheet_name']

        # Authenticate Google Cloud and Google Sheets
        # Autoryzuj Google Cloud i Google Sheets
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        bq_client = bigquery.Client(credentials=creds, project=BQ_CLIENT_PROJECT)
        sheets_service = build('sheets', 'v4', credentials=creds)

        # --- STEP 1: FETCH COST FROM BIGQUERY ---
        # --- KROK 1: POBIERZ KOSZT Z BIGQUERY ---

        # SQL Query: Fetching RAW burned costs
        # Zapytanie SQL: Pobieranie SUROWYCH przepalonych kosztów
        sql = f"""
            SELECT
                SUM(cost) as raw_cost
            FROM `{BQ_TABLE}`
            WHERE
                project.id = @projectId
                AND usage_start_time >= TIMESTAMP(DATE_TRUNC(CURRENT_DATE("Europe/Warsaw"), MONTH))
        """

        # Execute SQL query
        # Wykonaj zapytanie SQL
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("projectId", "STRING", TARGET_COST_PROJECT)
            ]
        )
        query_job = bq_client.query(sql, job_config=job_config)
        results = query_job.result()

        # Process results and calculate VAT
        # Przetwórz wyniki i oblicz VAT
        raw_amount = 0.0
        for db_row in results:
            if db_row.raw_cost is not None:
                raw_amount = float(db_row.raw_cost)

        gross_amount = round(raw_amount * 1.23, 2)

        print(f"🔄 GCP Cost calculated: {gross_amount} PLN")
        print(f"🔄 Koszt GCP obliczony: {gross_amount} PLN")

        # --- STEP 2: INJECT COST INTO SHEET (COLUMN F) ---
        # --- KROK 2: WSTRZYKNIJ KOSZT DO ARKUSZA (KOLUMNA F) ---

        # Prepare the update payload for column F
        # Przygotuj pakiet aktualizacji dla kolumny F
        sheet_ref = f"'{sheet_name}'!F{row}"
        body = {'values': [[gross_amount]]}

        # Update Google Sheet
        # Zaktualizuj Arkusz Google
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=sheet_ref,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"✅ Success! Cost {gross_amount} injected into {sheet_ref}")
        print(f"✅ Sukces! Koszt {gross_amount} wstrzyknięty do {sheet_ref}")

    except Exception as e:
        # Handle errors gracefully
        # Obsłuż błędy z gracją
        print(f"❌ Critical Error: {e}", file=sys.stderr)
        print(f"❌ Krytyczny błąd: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Execute the injection process
    # Uruchom proces wstrzykiwania
    get_and_inject_cost()