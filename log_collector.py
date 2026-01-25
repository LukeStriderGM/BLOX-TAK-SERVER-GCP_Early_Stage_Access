#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import yaml
import datetime
import glob
import tarfile
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pypdf import PdfReader, PdfWriter

# --- CONFIGURATION & CONSTANTS ---
# --- KONFIGURACJA I STAŁE ---

CONFIG_FILE = 'config.yaml'
EVIDENCE_DIR = 'evidence'

FONTS = {
    'R': "UbuntuMono-Regular.ttf",
    'B': "UbuntuMono-Bold.ttf",
    'I': "UbuntuMono-Italic.ttf"
}

# --- TRANSLATIONS ---
# --- TŁUMACZENIA ---

TEXTS = {
    'EN': {
        'header': "APPENDIX A: LOG PACKAGE MANIFEST",
        'desc': "This document certifies the extraction of the following system and container logs.",
        'filename': "FILENAME",
        'size': "SIZE (Bytes)",
        'archive_info': "ARCHIVE METADATA",
        'arch_name': "Archive Name:",
        'arch_hash': "Integrity Check (MD5):",
        'legal_title': "LEGAL DISCLAIMER / DATA RETENTION POLICY",
        'legal_text': "The list above confirms the security of the forensic material. The full log package (.tar.gz) contains sensitive data and is stored in a secure offline repository. It may be released to appropriate authorities, institutions, or the client only in justified cases.",
        'footer': "Forensic Log Collector | Chain of Custody",
        'status_pub': "[ PUBLIC RELEASE: METADATA ONLY - CONTENT SECURED OFFLINE ]",
        'status_priv': "[ INTERNAL: FULL CHAIN OF CUSTODY ]"
    },
    'PL': {
        'header': "ZAŁĄCZNIK A: SPIS ZAWARTOŚCI LOGÓW",
        'desc': "Niniejszy dokument potwierdza ekstrakcję następujących logów systemowych i kontenerów.",
        'filename': "NAZWA PLIKU",
        'size': "ROZMIAR (B)",
        'archive_info': "METADANE ARCHIWUM",
        'arch_name': "Nazwa Archiwum:",
        'arch_hash': "Suma Kontrolna (MD5):",
        'legal_title': "KLAUZULA PRAWNA / POLITYKA RETENCJI",
        'legal_text': "Powyższy wykaz stanowi potwierdzenie zabezpieczenia materiału dowodowego. Pełny pakiet logów (.tar.gz) zawiera dane wrażliwe i jest przechowywany w bezpiecznym depozycie offline. Może zostać udostępniony odpowiednim organom wyłącznie w uzasadnionych przypadkach.",
        'footer': "Kryminalistyka Cyfrowa | Łańcuch Dowodowy",
        'status_pub': "[ WERSJA PUBLICZNA: TYLKO METADANE - TREŚĆ ZABEZPIECZONA ]",
        'status_priv': "[ WEWNĘTRZNY: PEŁNY ŁAŃCUCH DOWODOWY ]"
    }
}

# --- HELPER FUNCTIONS ---
# --- FUNKCJE POMOCNICZE ---

def load_config():
    # Check if config file exists
    # Sprawdź, czy plik konfiguracyjny istnieje
    if not os.path.exists(CONFIG_FILE): return None
    
    # Load and parse YAML file
    # Wczytaj i przetwórz plik YAML
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return yaml.safe_load(f)

def run_local_command(command):
    try:
        # Execute shell command locally
        # Wykonaj komendę shell lokalnie
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Local execution failed: {e}")
        print(f"❌ Lokalne wykonanie nie powiodło się: {e}")
        return False

def get_file_hash(filepath):
    # Compute MD5 hash of a file
    # Oblicz hash MD5 pliku
    import hashlib
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# --- PDF CLASS ---
# --- KLASA PDF ---

class EvidencePDF(FPDF):
    def __init__(self, vm_name, lang):
        super().__init__()
        self.vm_name = vm_name
        self.lang = lang
        self.t = TEXTS[lang]
        
        try:
            self.add_font('UbuntuMono', '', FONTS['R'])
            self.add_font('UbuntuMono', 'B', FONTS['B'])
            self.add_font('UbuntuMono', 'I', FONTS['I'])
            self.font_family = 'UbuntuMono'
        except:
            self.font_family = 'Courier'

    def header(self):
        self.set_font(self.font_family, 'B', 14)
        self.cell(0, 10, self.t['header'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family, 'I', 8)
        self.cell(0, 10, f"{self.t['footer']} | {datetime.datetime.now().strftime('%Y-%m-%d')}", align='C')

    def print_row_grid(self, col1_text, col2_text, w1, w2, fill=False):
        # Calculate row height for text wrapping
        # Oblicz wysokość wiersza dla zawijania tekstu
        font_size = self.font_size_pt / 72 * 25.4
        line_height = font_size * 1.5
        
        # Check how many lines the text will occupy
        # Sprawdź ile linii zajmie tekst
        lines1 = self.multi_cell(w1, line_height, str(col1_text), dry_run=True, output="LINES")
        lines2 = self.multi_cell(w2, line_height, str(col2_text), dry_run=True, output="LINES")
        
        max_lines = max(len(lines1), len(lines2))
        row_height = max_lines * line_height

        # Check for page break
        # Sprawdź podział strony
        if self.get_y() + row_height > self.page_break_trigger:
            self.add_page()

        x_start, y_start = self.get_x(), self.get_y()

        if fill:
            self.set_fill_color(220, 220, 220)
            self.rect(x_start, y_start, w1 + w2, row_height, 'F')
        
        # Column 1 (File Name - Wrapped)
        # Kolumna 1 (Nazwa pliku - zawijana)
        self.set_xy(x_start, y_start)
        self.multi_cell(w1, line_height, str(col1_text), border=0, align='L')
        
        # Column 2 (Size)
        # Kolumna 2 (Rozmiar)
        self.set_xy(x_start + w1, y_start)
        self.multi_cell(w2, line_height, str(col2_text), border=0, align='L')

        # Draw borders on top
        # Rysuj obramowania na wierzchu
        self.rect(x_start, y_start, w1, row_height)
        self.rect(x_start + w1, y_start, w2, row_height)

        self.set_xy(x_start, y_start + row_height)

def create_manifest_pdf(vm_name, archive_path, file_list, lang, is_public, output_pdf):
    # Initialize PDF and fonts
    # Inicjalizuj PDF i czcionki
    pdf = EvidencePDF(vm_name, lang)
    t = TEXTS[lang]
    font = pdf.font_family

    pdf.add_page()
    pdf.set_font(font, '', 10)
    pdf.multi_cell(0, 5, t['desc'])
    pdf.ln(5)

    # Archive Metadata Section
    # Sekcja metadanych archiwum
    pdf.set_font(font, 'B', 11)
    pdf.cell(0, 6, t['archive_info'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(font, '', 10)
    
    archive_name = os.path.basename(archive_path)
    archive_hash = get_file_hash(archive_path)
    
    pdf.cell(50, 6, t['arch_name'], border=0)
    pdf.cell(0, 6, archive_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(50, 6, t['arch_hash'], border=0)
    pdf.cell(0, 6, archive_hash, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # --- FILE TABLE (ALWAYS VISIBLE) ---
    # --- TABELA PLIKÓW (ZAWSZE WIDOCZNA) ---
    w_name = 140
    w_size = 50
    
    pdf.set_font(font, 'B', 10)
    pdf.print_row_grid(t['filename'], t['size'], w_name, w_size, fill=True)
    
    pdf.set_font(font, '', 9)
    for fname, fsize in file_list:
        # Use full filename and grid for wrapping
        # Użyj pełnej nazwy i siatki do zawijania
        pdf.print_row_grid(fname, str(fsize), w_name, w_size, fill=False)

    pdf.ln(10)
    
    # --- STATUS & LEGAL DISCLAIMER ---
    # --- STATUS I KLAUZULA PRAWNA ---
    status_msg = t['status_pub'] if is_public else t['status_priv']
    
    pdf.set_font(font, 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, status_msg, border=1, fill=True, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    pdf.set_font(font, 'B', 11)
    pdf.cell(0, 8, t['legal_title'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font(font, 'I', 10)
    pdf.multi_cell(0, 5, t['legal_text'], border=1, align='L')

    pdf.output(output_pdf)
    return output_pdf

def merge_pdfs(original_report, appendix_pdf):
    # Merge original report with appendix
    # Scal oryginalny raport z załącznikiem
    writer = PdfWriter()
    try:
        reader_orig = PdfReader(original_report)
        for page in reader_orig.pages:
            writer.add_page(page)
        reader_app = PdfReader(appendix_pdf)
        for page in reader_app.pages:
            writer.add_page(page)

        with open(original_report, "wb") as f_out:
            writer.write(f_out)
        print(f"      📎 Merged logs manifest into: {os.path.basename(original_report)}")
        print(f"      📎 Scalono manifest logów do: {os.path.basename(original_report)}")
    except Exception as e:
        print(f"❌ Error merging PDF: {e}")
        print(f"❌ Błąd scalania PDF: {e}")

def remote_harvest_script(timestamp):
    # Define remote bash script for log collection
    # Zdefiniuj zdalny skrypt bash do zbierania logów
    temp_dir = f"/tmp/harvest_{timestamp}"
    archive_name = f"/tmp/logs_{timestamp}.tar.gz"
    
    script = f"""
    mkdir -p {temp_dir}/system
    mkdir -p {temp_dir}/docker_std
    mkdir -p {temp_dir}/docker_internal
    sudo cp /var/log/syslog {temp_dir}/system/ 2>/dev/null
    sudo cp /var/log/auth.log {temp_dir}/system/ 2>/dev/null
    sudo dmesg > {temp_dir}/system/dmesg_boot.txt
    for container in $(sudo docker ps -a -q); do
        name=$(sudo docker inspect --format='{{{{.Name}}}}' $container | cut -c2-)
        sudo docker logs $container > {temp_dir}/docker_std/$name.log 2>&1
        if [[ "$name" == *"tak-server-tak"* ]]; then
             echo "   -> Detected TAK Server: $name. Extracting internal logs..."
             mkdir -p {temp_dir}/docker_internal/$name
             sudo docker cp $container:/opt/tak/logs/ {temp_dir}/docker_internal/$name/ 2>/dev/null
        fi
    done
    sudo tar -czf {archive_name} -C /tmp harvest_{timestamp}
    sudo chmod 644 {archive_name}
    sudo rm -rf {temp_dir}
    echo "READY:{archive_name}"
    """
    return script

# --- MAIN EXECUTION ---
# --- GŁÓWNE WYKONANIE ---

def main():
    # Clear terminal screen
    # Wyczyść ekran terminala
    os.system("clear || cls")
    
    print("=" * 60)
    print("=== LOG COLLECTOR v7.0 (NO CENSORSHIP) ===")
    print("=== ZBIERACZ LOGÓW v7.0 (BEZ CENZURY) ===")
    print("=" * 60)
    
    cfg = load_config()
    if not cfg: return

    vms = {k: v for k, v in cfg.items() if isinstance(v, dict) and 'name' in v and k != 'LOCAL_CONFIG'}
    
    print("\nSelect Target VM:")
    print("Wybierz Docelową VM:")
    for key, data in vms.items():
        print(f"  - {key}: {data['name']}")

    print("\n> ", end="")
    server_key = input().strip().upper()
    if server_key not in vms: return

    vm_data = vms[server_key]
    user = vm_data.get('user', 'blox_tak_server_admin')
    internal_ip = vm_data.get('internal_ip')
    vm_name = vm_data.get('name', server_key)

    if not internal_ip:
        print("❌ Error: Internal IP missing.")
        print("❌ Błąd: Brak wewnętrznego IP.")
        return

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    local_evidence_path = Path(EVIDENCE_DIR) / vm_name / "logs"
    local_evidence_path.mkdir(parents=True, exist_ok=True)
    local_archive_name = local_evidence_path / f"logs_{ts}.tar.gz"

    # --- 1. HARVEST ---
    # --- 1. ZBIERANIE ---
    print(f"\n[1/4] Harvesting logs from {internal_ip} as {user}...")
    print(f"[1/4] Zbieranie logów z {internal_ip} jako {user}...")
    
    ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{internal_ip}', remote_harvest_script(ts)]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if "READY:" not in result.stdout:
            print(f"❌ Harvest failed: {result.stderr}")
            print(f"❌ Zbieranie nieudane: {result.stderr}")
            return
        remote_file = result.stdout.split("READY:")[1].strip().split()[0]
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Błąd: {e}")
        return

    # --- 2. DOWNLOAD ---
    # --- 2. POBIERANIE ---
    print(f"[2/4] Downloading archive...")
    print(f"[2/4] Pobieranie archiwum...")
    
    scp_cmd = f"scp -o StrictHostKeyChecking=no {user}@{internal_ip}:{remote_file} {local_archive_name}"
    if not run_local_command(scp_cmd): return
    subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{internal_ip}', f'sudo rm -f {remote_file}'])

    # --- 3. ANALYZE ---
    # --- 3. ANALIZA ---
    print(f"[3/4] Analyzing package contents...")
    print(f"[3/4] Analiza zawartości pakietu...")
    
    file_list = []
    try:
        with tarfile.open(local_archive_name, "r:gz") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    file_list.append((member.name, member.size))
    except Exception as e:
        print(f"❌ Failed to read archive: {e}")
        print(f"❌ Błąd odczytu archiwum: {e}")
        return

    # --- 4. UPDATE REPORTS (WSZYSTKIE WERSJE) ---
    # --- 4. AKTUALIZACJA RAPORTÓW (WSZYSTKIE WERSJE) ---
    print(f"[4/4] Updating existing PDF reports...")
    print(f"[4/4] Aktualizacja istniejących raportów PDF...")
    
    reports = glob.glob(f"*PORT_{vm_name}_*.pdf")
    
    count = 0
    if not reports:
        print("⚠️  No reports found.")
        print("⚠️  Nie znaleziono raportów.")
    else:
        for report in reports:
            if "FINAL" in report: continue
            if "tmp" in report: continue
            
            is_public = "PUBLIC" in report
            lang = 'EN'
            if 'RAPORT' in report: lang = 'PL'
            elif 'REPORT' in report: lang = 'EN'
            
            vis = "🙈 PUBLIC" if is_public else "🔒 PRIVATE"
            print(f"   > Processing: {report} [{lang}] {vis}")
            print(f"   > Przetwarzanie: {report} [{lang}] {vis}")
            
            tmp = f"tmp_manifest_{lang}_{'pub' if is_public else 'priv'}.pdf"
            
            # Generate Manifest with FULL TABLE
            # Generuj Manifest z PEŁNĄ TABELĄ
            create_manifest_pdf(vm_name, str(local_archive_name), file_list, lang, is_public, tmp)
            
            merge_pdfs(report, tmp)
            os.remove(tmp)
            count += 1

    print("\n" + "=" * 60)
    print(f"✅ PROCESS COMPLETE. Updated {count} reports.")
    print(f"✅ PROCES ZAKOŃCZONY. Zaktualizowano {count} raportów.")
    print(f"📂 Archive: {local_archive_name}")
    print(f"📂 Archiwum: {local_archive_name}")
    print("=" * 60)

if __name__ == "__main__":
    main()
