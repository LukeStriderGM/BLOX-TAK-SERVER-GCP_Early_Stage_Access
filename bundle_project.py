import os
import datetime

# =====================================================================================
# === CONFIGURATION ===
# === KONFIGURACJA ===
# =====================================================================================

# English: Set your project version here. It will be used in the output filename.
# Polski:  Ustaw tutaj wersję swojego projektu. Zostanie ona użyta w nazwie pliku wyjściowego.
VERSION = "1.0.0.3"

# List of directories to absolutely exclude from the bundling process.
# Lista katalogów do bezwzględnego wykluczenia z procesu pakowania.
DIRECTORIES_TO_EXCLUDE = {
    '.git',
    '.idea',
    '.venv',
    'venv',
    'env',
    '__pycache__',
    '.terraform',
    'terraform.tfstate.d',
    'gcp_tak_certs'
}

# List of specific files to exclude (e.g., configuration files with passwords).
# Lista konkretnych plików do wykluczenia (np. pliki konfiguracyjne z hasłami).
FILES_TO_EXCLUDE = {
    'token.json',
    'client_secret.json',
    'config.yaml',
    '.terraform.lock.hcl'
}

# List of file extensions to be ignored.
# Lista rozszerzeń plików, które mają być ignorowane.
EXTENSIONS_TO_EXCLUDE = {
    '.p12',
    '.zip',
    '.png',
    '.log',
    '.tmp',
    '.pdf',
    '.ttf'
}


# =====================================================================================
# === MAIN SCRIPT LOGIC ===
# === GŁÓWNA LOGIKA SKRYPTU ===
# =====================================================================================

def bundle_project_files():
    """
    Walks through the project directory, collects the content of all allowed
    files, and saves them into a single, large text file.

    Przechodzi przez katalog projektu, zbiera zawartość wszystkich dozwolonych
    plików i zapisuje je w jednym, dużym pliku tekstowym.
    """
    project_root = os.path.abspath(os.path.dirname(__file__))
    project_name = os.path.basename(project_root)

    # --- ZMIANA: Dynamiczne tworzenie nazwy pliku wyjściowego ---
    # --- CHANGE: Dynamically create the output filename ---
    output_filename = f"{project_name}_{VERSION}_bundle.txt"

    print("Starting project bundling...")
    print("Rozpoczynam pakowanie projektu...")
    print(f"Root directory: {project_root}")
    print(f"Katalog główny: {project_root}")
    print(f"Output file: {output_filename}\n")
    print(f"Plik wyjściowy: {output_filename}\n")

    try:
        with open(output_filename, 'w', encoding='utf-8') as bundle_file:
            bundle_file.write(f"Project Bundle: {project_name}\n")
            bundle_file.write(f"Version: {VERSION}\n")
            bundle_file.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            bundle_file.write("=" * 40 + "\n\n")

            for root, dirs, files in os.walk(project_root, topdown=True):
                dirs[:] = [d for d in dirs if d not in DIRECTORIES_TO_EXCLUDE]

                for filename in sorted(files):
                    # --- ZMIANA: Sprawdzanie dynamicznej nazwy pliku wyjściowego ---
                    # --- CHANGE: Check against the dynamic output filename ---
                    if filename == output_filename or filename in FILES_TO_EXCLUDE or any(filename.endswith(ext) for ext in EXTENSIONS_TO_EXCLUDE):
                        print(f"--- Skipping file: {filename}")
                        print(f"--- Pomijam plik: {filename}")
                        continue

                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, project_root)

                    print(f"+++ Adding file: {relative_path}")
                    print(f"+++ Dodaję plik: {relative_path}")

                    bundle_file.write(f"--- START FILE: {relative_path} ---\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as source_file:
                            bundle_file.write(source_file.read())
                    except Exception as e:
                        bundle_file.write(f"\n[ERROR READING FILE / BŁĄD ODCZYTU PLIKU: {e}]\n")
                    bundle_file.write(f"\n--- END FILE: {relative_path} ---\n\n")

        print("\nProject bundling completed successfully!")
        print("Pakowanie projektu zakończone pomyślnie!")
        print(f"The result has been saved to the file: {output_filename}")
        print(f"Wynik został zapisany w pliku: {output_filename}")

    except IOError as e:
        print(f"\nERROR: Could not write to the output file: {e}")
        print(f"BŁĄD: Nie można zapisać pliku wyjściowego: {e}")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        print(f"BŁĄD: Wystąpił nieoczekiwany problem: {e}")


if __name__ == "__main__":
    bundle_project_files()
