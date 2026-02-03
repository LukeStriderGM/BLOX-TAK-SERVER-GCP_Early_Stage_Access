// --- GOOGLE APPS SCRIPT: COST TRACKER ---
// --- GOOGLE APPS SCRIPT: ŚLEDZENIE KOSZTÓW ---

function pobierzKosztyGoogleCloud() {
  // --- CONFIGURATION ---
  // --- KONFIGURACJA ---

  // Enter your Google Cloud Project ID here
  // Wpisz tutaj ID swojego projektu Google Cloud
  var PROJECT_ID = 'YOUR_PROJECT_ID'; 
  
  // Enter the BigQuery table ID (Dataset.Table)
  // Wpisz ID tabeli BigQuery (ZbiórDanych.Tabela)
  var TABLE_NAME = 'YOUR_PROJECT_ID.billing_data.gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX'; 
  
  // Enter the name of the sheet tab to update
  // Wpisz nazwę zakładki arkusza do aktualizacji
  var SHEET_NAME = 'PRICES - CENY: BTSGCP';


  // --- VALIDATION ---
  // --- WALIDACJA ---

  // Check if the table name has been configured
  // Sprawdź, czy nazwa tabeli została skonfigurowana
  if (TABLE_NAME.includes('XXXXXX')) {
    Logger.log("🔴 STOP: Table name is missing. Please configure 'TABLE_NAME'.");
    Logger.log("🔴 STOP: Brakuje nazwy tabeli. Skonfiguruj 'TABLE_NAME'.");
    return;
  }

  try {
    // --- SQL QUERY CONSTRUCTION ---
    // --- KONSTRUKCJA ZAPYTANIA SQL ---

    // Define SQL query to sum costs for the current day in Poland
    // Zdefiniuj zapytanie SQL sumujące koszty dla obecnego dnia w Polsce
    var sql = `
      SELECT
        SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as cost_netto
      FROM \`` + TABLE_NAME + `\`
      WHERE
        project.id = @projectId
        AND DATE(usage_start_time, "Europe/Warsaw") = CURRENT_DATE("Europe/Warsaw")
    `;

    // Prepare the API request object
    // Przygotuj obiekt żądania API
    var request = {
      query: sql,
      useLegacySql: false,
      parameterMode: 'NAMED',
      queryParameters: [
        {
          name: 'projectId',
          parameterType: { type: 'STRING' },
          parameterValue: { value: PROJECT_ID }
        }
      ]
    };

    // --- BIGQUERY EXECUTION ---
    // --- WYKONANIE BIGQUERY ---

    Logger.log("🔄 Sending query to BigQuery...");
    Logger.log("🔄 Wysyłanie zapytania do BigQuery...");

    // Send the query job
    // Wyślij zadanie zapytania
    var queryResults = BigQuery.Jobs.query(request, PROJECT_ID);
    var jobId = queryResults.jobReference.jobId;

    // Wait for the job to complete
    // Czekaj na zakończenie zadania
    var sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
      Utilities.sleep(sleepTimeMs);
      sleepTimeMs *= 2;
      queryResults = BigQuery.Jobs.getQueryResults(PROJECT_ID, jobId);
    }

    // --- DATA PROCESSING ---
    // --- PRZETWARZANIE DANYCH ---

    // Extract rows from the result
    // Wyodrębnij wiersze z wyniku
    var rows = queryResults.rows;
    var netAmount = 0.0;

    // Parse the result if it exists
    // Sparsuj wynik, jeśli istnieje
    if (rows && rows.length > 0 && rows[0].f && rows[0].f[0].v !== null) {
      netAmount = parseFloat(rows[0].f[0].v);
    }

    // Calculate Gross amount (add 23% VAT)
    // Oblicz kwotę Brutto (dodaj 23% VAT)
    var grossAmount = netAmount * 1.23; 

    Logger.log(f("✅ Data retrieved. Net: " + netAmount.toFixed(2)));
    Logger.log(f("✅ Dane pobrane. Netto: " + netAmount.toFixed(2)));

    // --- SPREADSHEET UPDATE ---
    // --- AKTUALIZACJA ARKUSZA ---

    // Get the active spreadsheet and sheet
    // Pobierz aktywny arkusz i zakładkę
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME);
    
    // Get all dates from Column A
    // Pobierz wszystkie daty z Kolumny A
    var lastRow = sheet.getLastRow();
    var dateRange = sheet.getRange(1, 1, lastRow, 1).getValues();
    
    // Set today's date (midnight) for comparison
    // Ustaw dzisiejszą datę (północ) do porównania
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    
    var found = false;

    // Loop through rows to find today's date
    // Pętla przez wiersze, aby znaleźć dzisiejszą datę
    for (var i = 0; i < dateRange.length; i++) {
      var rowDate = dateRange[i][0];
      
      // Check if the cell contains a date object
      // Sprawdź, czy komórka zawiera obiekt daty
      if (rowDate instanceof Date) {
        var compareDate = new Date(rowDate);
        compareDate.setHours(0, 0, 0, 0);

        // If dates match, update Column B
        // Jeśli daty się zgadzają, zaktualizuj Kolumnę B
        if (compareDate.getTime() === today.getTime()) {
          // Update the cell (row i+1, column 2)
          // Zaktualizuj komórkę (wiersz i+1, kolumna 2)
          sheet.getRange(i + 1, 2).setValue(grossAmount);
          
          Logger.log(f("📂 Spreadsheet updated successfully."));
          Logger.log(f("📂 Arkusz zaktualizowany pomyślnie."));
          found = true;
          break;
        }
      }
    }

    // Log warning if date not found
    // Loguj ostrzeżenie, jeśli nie znaleziono daty
    if (!found) {
      Logger.log("⚠️ Warning: Today's date not found in Column A.");
      Logger.log("⚠️ Ostrzeżenie: Nie znaleziono dzisiejszej daty w Kolumnie A.");
    }

  } catch (e) {
    // --- ERROR HANDLING ---
    // --- OBSŁUGA BŁĘDÓW ---
    Logger.log("❌ Critical Error: " + e.toString());
    Logger.log("❌ Błąd Krytyczny: " + e.toString());
  }
}

// Helper function to mimic f-strings in JS (for style consistency)
// Funkcja pomocnicza imitująca f-stringi w JS (dla spójności stylu)
function f(string) {
  return string;
}
