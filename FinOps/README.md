## 🇺🇸 / 🇵🇱 Version 1.0.0.1 - Automated FinOps & BigQuery Cost Tracking

https://docs.google.com/spreadsheets/d/1dAM40OTxRDzltWwb_dnrfRSE98S4XxXteFhoSMBLcJE

This release integrates a serverless, maintenance-free financial operations module directly into the Google Workspace ecosystem, enabling precise, daily cost monitoring without external infrastructure.

### 🇺🇸 Key Features
* **Serverless Cost Agent (`billing_script.js`):** A Google Apps Script-based agent that executes scheduled runs (3:00 AM - 4:00 AM) within the Google Cloud ecosystem, requiring no external VM or maintenance.
* **Direct BigQuery Integration:** Bypasses estimated billing APIs by executing raw Standard SQL queries against the `gcp_billing_export` table for absolute financial accuracy.
* **Precision VAT Logic:** Automatically applies regional tax logic (+23% VAT) to net costs before data injection, ensuring alignment with accounting standards.
* **Resilient Sheet Injection:** Features a "Bulletproof" tab detection mechanism (targeting `+23%VAT`) that functions independently of the parent filename.

### 🇺🇸 Roadmap (Next Steps)
* **Granular VM Fingerprinting:** Future updates will leverage the unique instance naming convention (e.g., `blox-tak-server-vm-2026-01-20-03-11-56`) to isolate costs per specific micro-instance lifecycles using SQL wildcard filtering and Label matching.

<details>

<summary>🇵🇱 [Kliknij Aby Rozwinąć Opis Wydania po Polsku]</summary>

## 🇵🇱 Wersja 1.0.0.1 - Automatyczny FinOps i Śledzenie Kosztów BigQuery

https://docs.google.com/spreadsheets/d/1dAM40OTxRDzltWwb_dnrfRSE98S4XxXteFhoSMBLcJE

To wydanie integruje bezserwerowy, bezobsługowy moduł operacji finansowych bezpośrednio z ekosystemem Google Workspace, umożliwiając precyzyjne, codzienne monitorowanie kosztów bez konieczności utrzymywania zewnętrznej infrastruktury.

### 🇵🇱 Główne Funkcje
* **Serverless Cost Agent (`billing_script.js`):** Agent oparty na Google Apps Script, wykonujący zaplanowane przebiegi (3:00 - 4:00 rano) wewnątrz ekosystemu Google Cloud, niewymagający zewnętrznych maszyn wirtualnych ani konserwacji.
* **Bezpośrednia Integracja z BigQuery:** Omija API szacunkowych rozliczeń, wykonując surowe zapytania SQL (Standard SQL) bezpośrednio na tabeli `gcp_billing_export` dla zapewnienia absolutnej dokładności finansowej.
* **Precyzyjna Logika VAT:** Automatycznie stosuje regionalną logikę podatkową (+23% VAT) do kosztów netto przed ich wprowadzeniem, zapewniając zgodność ze standardami księgowymi.
* **Niezawodna Iniekcja Danych:** Posiada mechanizm wykrywania zakładki "Bulletproof" (celujący w `+23%VAT`), który działa niezależnie od nazwy pliku nadrzędnego.

### 🇵🇱 Mapa Drogowa (Kolejne Kroki)
* **Szczegółowy Fingerprinting Maszyn VM:** Przyszłe aktualizacje wykorzystają unikalną konwencję nazewnictwa instancji (np. `blox-tak-server-vm-2026-01-20-03-11-56`), aby izolować koszty dla cykli życia konkretnych mikro-instancji przy użyciu filtrowania SQL wildcard oraz dopasowania Etykiet (Labels).

</details>