import sys
import os
import yaml
from google.oauth2 import service_account
from google.cloud import bigquery
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# --- KONFIGURACJA ---
SERVICE_ACCOUNT_FILE = 'credentials.json'
SPREADSHEET_ID = '1dAM40OTxRDzltWwb_dnrfRSE98S4XxXteFhoSMBLcJE'
CONFIG_FILE = 'config.yaml'
# Scopes for Sheets and BigQuery
# Zakresy dla Arkuszy i BigQuery
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/cloud-platform'
]

# GCP Billing Details
# Szczegóły bilingu GCP
GCP_PROJECT_ID = 'blox-tak-server'
BQ_TABLE = 'blox-tak-gemini-467013.billing_data.gcp_billing_export_v1_013118_62714A_101995'


# --- FILE OPERATIONS ---
# --- OPERACJE NA PLIKACH ---

def load_config():
    # Load current row from YAML
    # Załaduj bieżący wiersz z YAML
    with open(CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)


# --- MAIN LOGIC ---
# --- GŁÓWNA LOGIKA ---

def update_gcp_cost_column_f():
    # Validate system files
    # Walidacja plików systemowych
    if not os.path.exists(SERVICE_ACCOUNT_FILE) or not os.path.exists(CONFIG_FILE):
        print(f"🔴 Critical: Required files missing!")
        print(f"🔴 Krytyczne: Brak wymaganych plików!")
        sys.exit(1)

    try:
        # Load configuration
        # Załaduj konfigurację
        config = load_config()
        row = config['last_row']
        sheet_name = config['sheet_name']

        # Initialize Google Services
        # Inicjalizacja usług Google
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        bq_client = bigquery.Client(credentials=creds, project=GCP_PROJECT_ID)
        sheets_service = build('sheets', 'v4', credentials=creds)

        # --- STEP 1: QUERY BIGQUERY ---
        # --- KROK 1: ZAPYTANIE BIGQUERY ---

        print(f"🔄 Fetching costs for row {row} from BigQuery...")
        print(f"🔄 Pobieranie kosztów dla wiersza {row} z BigQuery...")

        # Sum net costs for the current month
        # Sumuj koszty netto dla bieżącego miesiąca
        sql = f"""
            SELECT
                SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as cost_netto
            FROM `{BQ_TABLE}`
            WHERE
                project.id = @projectId
                AND usage_start_time >= TIMESTAMP(DATE_TRUNC(CURRENT_DATE("Europe/Warsaw"), MONTH))
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("projectId", "STRING", GCP_PROJECT_ID)
            ]
        )

        query_job = bq_client.query(sql, job_config=job_config)
        results = query_job.result()

        net_amount = 0.0
        for bq_row in results:
            if bq_row.cost_netto is not None:
                net_amount = float(bq_row.cost_netto)

        # Apply 23% VAT and round to 2 decimals
        # Nałóż 23% VAT i zaokrąglij do 2 miejsc po przecinku
        gross_amount = round(net_amount * 1.23, 2)

        # --- STEP 2: UPDATE COLUMN F ---
        # --- KROK 2: AKTUALIZACJA KOLUMNY F ---

        target_cell = f"'{sheet_name}'!F{row}"

        print(f"🔄 Writing {gross_amount} to {target_cell}...")
        print(f"🔄 Zapisywanie {gross_amount} do {target_cell}...")

        body = {'values': [[gross_amount]]}

        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=target_cell,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"✅ Column F updated successfully.")
        print(f"✅ Kolumna F zaktualizowana pomyślnie.")

    except Exception as e:
        print(f"❌ Error during GCP sync: {e}")
        print(f"❌ Błąd podczas synchronizacji GCP: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_gcp_cost_column_f()