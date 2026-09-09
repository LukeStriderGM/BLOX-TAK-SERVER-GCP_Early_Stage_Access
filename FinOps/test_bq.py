import os
import sys
from google.oauth2 import service_account
from google.cloud import bigquery

SERVICE_ACCOUNT_FILE = 'credentials.json'
BQ_CLIENT_PROJECT = 'blox-tak-support-506512'
# Wracamy do głównej tabeli v1
BQ_TABLE = 'blox-tak-support-506512.billing_data.gcp_billing_export_v1_01DD0A_C0EEF2_052566'


def global_audit():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    bq_client = bigquery.Client(credentials=creds, project=BQ_CLIENT_PROJECT)

    print("🔍 Skanuję całą tabelę v1 w poszukiwaniu aktywnych projektów i usług...")

    # Zapytanie grupujące po projektach i usługach, żeby zobaczyć, co tam w ogóle jest
    sql = f"""
        SELECT
            project.id as project_id,
            service.description as service_name,
            COUNT(*) as record_count,
            SUM(cost) as total_cost
        FROM `{BQ_TABLE}`
        GROUP BY project_id, service_name
        ORDER BY record_count DESC
        LIMIT 15
    """

    query_job = bq_client.query(sql)
    results = query_job.result()

    print("-" * 70)
    for row in results:
        print(
            f"Projekt: {row.project_id} | Usługa: {row.service_name} | Wpisów: {row.record_count} | Koszt: {row.total_cost}")
    print("-" * 70)


if __name__ == "__main__":
    global_audit()