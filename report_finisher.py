#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import glob
import subprocess
import json
import yaml
import time
import zipfile
import hashlib
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pypdf import PdfReader, PdfWriter

# --- CONFIGURATION & CONSTANTS ---
# --- KONFIGURACJA I STAŁE ---

CONFIG_FILE = 'config.yaml'

FONTS = {
    'R': "UbuntuMono-Regular.ttf",
    'B': "UbuntuMono-Bold.ttf",
    'I': "UbuntuMono-Italic.ttf"
}

# --- DYNAMIC CONFIG LOADING ---
# --- DYNAMICZNE ŁADOWANIE KONFIGURACJI ---

def get_config_paths():
    # Defaults in case of missing config
    # Wartości domyślne w przypadku braku konfiguracji
    default_pcap = []
    default_evidence = "evidence"
    
    if not os.path.exists(CONFIG_FILE):
        return default_pcap, default_evidence

    try:
        with open(CONFIG_FILE, 'r') as f:
            cfg = yaml.safe_load(f)
        
        paths = cfg.get('LOCAL_PATHS', {})
        
        # Load PCAP directories and expand user path (~)
        # Wczytaj katalogi PCAP i rozwiń ścieżkę użytkownika (~)
        raw_dirs = paths.get('pcap_directories', default_pcap)
        clean_dirs = [os.path.expanduser(p) for p in raw_dirs]
        
        # Load output directory
        # Wczytaj katalog wyjściowy
        ev_dir = paths.get('evidence_output_dir', default_evidence)
        
        return clean_dirs, ev_dir
    except Exception as e:
        print(f"⚠️ Config Load Error: {e}")
        print(f"⚠️ Błąd ładowania konfiguracji: {e}")
        return default_pcap, default_evidence

# Load global variables dynamically from YAML
# Załaduj zmienne globalne dynamicznie z YAML
PCAP_PATHS, EVIDENCE_DIR = get_config_paths()

# --- TRANSLATIONS ---
# --- TŁUMACZENIA ---

TEXTS = {
    'EN': {
        'header': "APPENDIX B: INFRASTRUCTURE & NETWORK SECURITY",
        'snap_sec': "1. GOLDEN IMAGE CHECKPOINT (COLD STORAGE)",
        'snap_desc': "System stopped. Filesystem consistency guaranteed.",
        'snap_name': "Snapshot ID:",
        'snap_time': "Creation Time:",
        'snap_status': "Status:",
        'snap_size': "Storage / Disk:",
        'snap_link': "GOLDEN IMAGE SOURCE (URI):",
        'net_sec': "2. NETWORK TRAFFIC INTERCEPTION (PCAPNG)",
        'filename': "FILENAME",
        'size': "SIZE",
        'source': "SOURCE",
        'legal': "LEGAL WARNING (SIGINT/COMINT)",
        'legal_text': "PCAPNG files contain full network packet captures. These files are classified as HIGHLY SENSITIVE. They are stored in a separate air-gapped evidence locker and are NOT included in the standard report body (Metadata listing above serves as proof of capture).",
        'footer': "Final System Validation | Ready for Deployment"
    },
    'PL': {
        'header': "ZAŁĄCZNIK B: BEZPIECZEŃSTWO I SIECI",
        'snap_sec': "1. PUNKT PRZYWRACANIA (ZIMNA MIGAWKA)",
        'snap_desc': "System zatrzymany. Gwarantowana spójność systemu plików.",
        'snap_name': "ID Snapshotu:",
        'snap_time': "Data utworzenia:",
        'snap_status': "Status:",
        'snap_size': "Rozmiar (Snap/Dysk):",
        'snap_link': "ŹRÓDŁO OBRAZU (URI - DISK_IMAGE):",
        'net_sec': "2. PRZECHWYCONY RUCH SIECIOWY (PCAPNG)",
        'filename': "NAZWA PLIKU",
        'size': "ROZMIAR",
        'source': "ŹRÓDŁO",
        'legal': "OSTRZEŻENIE PRAWNE (SIGINT/COMINT)",
        'legal_text': "Pliki PCAPNG zawierają pełny zrzut pakietów sieciowych. Pliki te są sklasyfikowane jako WRAŻLIWE. Przechowywane są w odseparowanym depozycie i NIE są dołączane do treści raportu (Powyższa lista służy jako dowód zabezpieczenia).",
        'footer': "Finalna Walidacja Systemu | Gotowość Operacyjna"
    }
}

# --- HELPER FUNCTIONS ---
# --- FUNKCJE POMOCNICZE ---

def load_config():
    # Check if config file exists
    # Sprawdź, czy plik konfiguracyjny istnieje
    if not os.path.exists(CONFIG_FILE): return None
    with open(CONFIG_FILE, 'r') as f: return yaml.safe_load(f)

def run_cmd(cmd):
    # Execute system command safely
    # Wykonaj polecenie systemowe bezpiecznie
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def calculate_hash(file_path):
    # Calculate SHA256 checksum
    # Oblicz sumę kontrolną SHA256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# --- GCLOUD LOGIC ---
# --- LOGIKA GCLOUD ---

def manage_vm_lifecycle(vm_name, project_id, zone):
    # Initialize snapshot naming
    # Inicjalizuj nazewnictwo snapshotu
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    snap_name = f"snap-tak-cold-{ts}" 
    desc = f"COLD SNAPSHOT from {vm_name}"
    
    print(f"\n🛑 Checking VM status: {vm_name}...")
    print(f"🛑 Sprawdzanie statusu VM: {vm_name}...")
    
    ok, out, err = run_cmd(['gcloud', 'compute', 'instances', 'stop', vm_name, f'--project={project_id}', f'--zone={zone}', '--quiet'])
    if not ok and "is already stopped" not in err:
        print(f"⚠️ Warning during stop: {err}")
        print(f"⚠️ Ostrzeżenie podczas zatrzymywania: {err}")
    else:
        print("   VM is stopped/stopping.")
        print("   VM jest zatrzymana/zatrzymuje się.")

    print(f"📸 CREATING COLD SNAPSHOT: {snap_name}...")
    print(f"📸 TWORZENIE ZIMNEJ MIGAWKI: {snap_name}...")
    
    cmd_snap = [
        'gcloud', 'compute', 'disks', 'snapshot', vm_name,
        f'--project={project_id}', f'--zone={zone}',
        f'--snapshot-names={snap_name}', f'--description={desc}', '--quiet'
    ]
    ok, out, err = run_cmd(cmd_snap)
    if not ok:
        print(f"❌ Snapshot failed: {err}")
        print(f"❌ Snapshot nieudany: {err}")
        run_cmd(['gcloud', 'compute', 'instances', 'start', vm_name, f'--project={project_id}', f'--zone={zone}', '--quiet'])
        return None

    print(f"🚀 RESTARTING VM: {vm_name} (Back to business)...")
    print(f"🚀 RESTART VM: {vm_name} (Powrót do działania)...")
    run_cmd(['gcloud', 'compute', 'instances', 'start', vm_name, f'--project={project_id}', f'--zone={zone}', '--quiet'])
    return snap_name

def get_snapshot_details(snap_name, project_id):
    print(f"📡 Fetching Snapshot URI & REAL SIZE...")
    print(f"📡 Pobieranie URI Snapshotu i ROZMIARU RZECZYWISTEGO...")
    
    # Wait for Google to calculate storage bytes
    # Poczekaj aż Google przeliczy bajty
    time.sleep(5) 
    
    cmd = [
        'gcloud', 'compute', 'snapshots', 'describe', snap_name,
        f'--project={project_id}', '--format=json'
    ]
    ok, out, err = run_cmd(cmd)
    if not ok: return None
    snap = json.loads(out)
    
    raw_time = snap.get('creationTimestamp', '')
    try:
        dt_aware = datetime.datetime.fromisoformat(raw_time)
        dt_local = dt_aware.astimezone()
        fmt_time = dt_local.strftime('%Y-%m-%d %H:%M:%S (Local)')
    except Exception as e: 
        fmt_time = raw_time

    # --- SIZE LOGIC V6.3 ---
    # --- LOGIKA ROZMIARU V6.3 ---
    disk_size_gb = snap.get('diskSizeGb', '0')
    storage_bytes = int(snap.get('storageBytes', 0))
    
    if storage_bytes > 0:
        real_size_gb = storage_bytes / (1024**3) # Convert to GB
        # Format: "X.XX GB (Real) / Y GB (Disk)"
        size_str = f"{real_size_gb:.2f} GB (Real) / {disk_size_gb} GB (Disk)"
    else:
        size_str = f"Calculating... / {disk_size_gb} GB (Disk)"

    return {
        'name': snap.get('name', 'UNKNOWN'),
        'status': snap.get('status', 'UNKNOWN'),
        'size': size_str, # TWO VALUES
        'time': fmt_time, 
        'link': snap.get('selfLink', 'UNKNOWN')
    }

def get_pcap_full_paths():
    # Scan directories for PCAP files
    # Skanuj katalogi w poszukiwaniu plików PCAP
    files = []
    
    if not PCAP_PATHS:
        print("⚠️ No PCAP directories configured in config.yaml (LOCAL_PATHS).")
        print("⚠️ Nie skonfigurowano katalogów PCAP w config.yaml (LOCAL_PATHS).")
        return []

    for path in PCAP_PATHS:
        if not os.path.exists(path): 
            print(f"⚠️ Path not found: {path}")
            print(f"⚠️ Ścieżka nie znaleziona: {path}")
            continue
        
        found_count = 0
        for filepath in glob.glob(os.path.join(path, "*.pcapng")):
            files.append(filepath)
            found_count += 1
        
        if found_count == 0:
            print(f"   (No .pcapng files in: {path})")
            print(f"   (Brak plików .pcapng w: {path})")

    return files

def get_pcap_list_for_pdf():
    # Prepare PCAP list for PDF table
    # Przygotuj listę PCAP dla tabeli PDF
    files = []
    for filepath in get_pcap_full_paths():
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        source = os.path.basename(os.path.dirname(filepath))
        name = os.path.basename(filepath)
        files.append((source, name, f"{size_mb:.2f} MB"))
    return files

# --- PACKAGING LOGIC ---
# --- LOGIKA PAKOWANIA ---

def create_master_bundle(reports, pcaps, snap_data, vm_key, vm_name):
    # Generate timestamp and zip name
    # Generuj znacznik czasu i nazwę zip
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    clean_vm_name = vm_name.replace(" ", "_") 
    zip_name = f"EVIDENCE_{vm_key}_{clean_vm_name}_{ts}.zip"
    
    print(f"\n📦 PACKAGING MASTER EVIDENCE: {zip_name}")
    print(f"📦 PAKOWANIE GŁÓWNEGO MATERIAŁU: {zip_name}")
    print(f"   Target: {vm_key} -> {vm_name}")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Reports
        for report in reports:
            if os.path.exists(report):
                zf.write(report, arcname=f"REPORTS/{os.path.basename(report)}")
                print(f"   + PDF: {report}")

        # 2. PCAP
        for pcap_path in pcaps:
            if os.path.exists(pcap_path):
                src_folder = os.path.basename(os.path.dirname(pcap_path))
                fname = os.path.basename(pcap_path)
                zf.write(pcap_path, arcname=f"NETWORK_PCAP/{src_folder}/{fname}")
                print(f"   + PCAP: {src_folder}/{fname}")

        # 3. LOGS
        print("   🔍 Deep scanning for Logs...")
        print("   🔍 Głębokie skanowanie logów...")
        found_logs = False
        
        # Use EVIDENCE_DIR loaded from config
        if os.path.exists(EVIDENCE_DIR):
            for root, dirs, files in os.walk(EVIDENCE_DIR):
                for file in files:
                    if file.endswith(".tar.gz") or file.endswith(".zip"):
                        full_path = os.path.join(root, file)
                        zf.write(full_path, arcname=f"SYSTEM_LOGS/{file}")
                        print(f"   + LOGS: {file}")
                        found_logs = True
        else:
             print(f"⚠️ Evidence directory not found: {EVIDENCE_DIR}")
             print(f"⚠️ Nie znaleziono katalogu dowodów: {EVIDENCE_DIR}")
        
        if not found_logs:
            print("   ⚠️ WARNING: No log archives found!")
            print("   ⚠️ OSTRZEŻENIE: Nie znaleziono archiwów logów!")

        # 4. Info (ORIGINAL V6.3 FORMAT)
        # 4. Info (ORYGINALNY FORMAT V6.3)
        info_content = f"""
============================================================
=== BLOX-TAK-SERVER | FORENSIC SNAPSHOT INFO ===
============================================================
Target Key:   {vm_key}
Target Name:  {vm_name}
Snapshot ID:  {snap_data['name']}
Created At:   {snap_data['time']}
Status:       {snap_data['status']}
STORAGE SIZE: {snap_data['size']}
------------------------------------------------------------
RECOVERY LINK (DISK_IMAGE):
{snap_data['link']}
============================================================
        """
        zf.writestr("SNAPSHOT_INFO.txt", info_content)
        print("   + INFO: SNAPSHOT_INFO.txt")

    checksum = calculate_hash(zip_name)
    hash_filename = f"{zip_name}.sha256"
    print(f"🔒 PACKAGE SHA-256: {checksum}")
    print(f"🔒 SUMA KONTROLNA PAKIETU: {checksum}")
    
    with open(hash_filename, "w") as f:
        f.write(f"{checksum}  {zip_name}")

# --- PDF GENERATION ---
# --- GENEROWANIE PDF ---

class FinisherPDF(FPDF):
    def __init__(self, lang, snap_data):
        super().__init__()
        self.lang = lang
        self.t = TEXTS[lang]
        self.snap = snap_data

    def header(self):
        self.set_font('UbuntuMono', 'B', 14)
        self.cell(0, 10, self.t['header'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('UbuntuMono', 'I', 8)
        self.cell(0, 10, f"{self.t['footer']} | {datetime.datetime.now().strftime('%Y-%m-%d')}", align='C')

def create_appendix_b(lang, output_pdf, pcap_list_pdf, snap_data):
    # Initialize PDF object
    # Inicjalizuj obiekt PDF
    pdf = FinisherPDF(lang, snap_data)
    t = TEXTS[lang]
    try:
        pdf.add_font('UbuntuMono', '', FONTS['R'])
        pdf.add_font('UbuntuMono', 'B', FONTS['B'])
        pdf.add_font('UbuntuMono', 'I', FONTS['I'])
        font = 'UbuntuMono'
    except: font = 'Courier'

    pdf.add_page()
    
    # 1. SNAPSHOT (FULL VISIBILITY)
    # 1. SNAPSHOT (PEŁNA WIDOCZNOŚĆ)
    pdf.set_font(font, 'B', 12)
    pdf.cell(0, 8, t['snap_sec'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(font, '', 10)
    pdf.cell(0, 5, t['snap_desc'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    if snap_data:
        pdf.set_fill_color(240, 248, 255)
        pdf.rect(10, pdf.get_y(), 190, 50, 'F') 
        pdf.set_xy(12, pdf.get_y() + 2)
        
        def add_row(label, value, color=(0,0,0)):
            pdf.set_x(12)
            pdf.set_font(font, 'B', 10)
            pdf.cell(40, 6, label, border=0)
            pdf.set_font(font, '', 10)
            pdf.set_text_color(*color)
            pdf.cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0,0,0)

        add_row(t['snap_name'], snap_data['name'])
        add_row(t['snap_time'], snap_data['time'])
        add_row(t['snap_size'], snap_data['size']) # RESTORED TWO VALUES
        
        status_color = (0, 100, 0) if snap_data['status'] in ['READY', 'UPLOADING'] else (200, 0, 0)
        add_row(t['snap_status'], snap_data['status'], status_color)
        
        pdf.ln(2)
        pdf.set_x(12)
        pdf.set_font(font, 'B', 10)
        pdf.cell(0, 6, t['snap_link'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(12)
        
        # EXPLICIT LINK FOR EVERYONE
        # JAWNY LINK DLA WSZYSTKICH
        pdf.set_font(font, '', 8)
        pdf.set_text_color(0, 0, 150)
        pdf.multi_cell(185, 4, snap_data['link'])
        pdf.set_text_color(0,0,0)
    else:
        pdf.cell(0, 10, "SNAPSHOT ERROR", align='C')
    pdf.ln(10)

    # 2. NETWORK (FULL VISIBILITY)
    # 2. SIECI (PEŁNA WIDOCZNOŚĆ)
    pdf.set_font(font, 'B', 12)
    pdf.cell(0, 8, t['net_sec'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # FULL TABLE
    # PEŁNA TABELA
    pdf.set_font(font, 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(25, 7, t['source'], 1, 0, 'C', True)
    pdf.cell(135, 7, t['filename'], 1, 0, 'C', True)
    pdf.cell(30, 7, t['size'], 1, 1, 'C', True)
    pdf.set_font(font, '', 8)
    if pcap_list_pdf:
        for source, fname, fsize in pcap_list_pdf:
            pdf.cell(25, 6, source, 1, 0, 'C')
            pdf.cell(135, 6, fname, 1, 0, 'L')
            pdf.cell(30, 6, fsize, 1, 1, 'R')
    else:
        pdf.cell(190, 6, "NO PCAP FILES DETECTED", 1, 1, 'C')
    
    pdf.ln(10)
    
    # 3. LEGAL
    # 3. PRAWNE
    pdf.set_font(font, 'B', 11)
    pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 8, t['legal'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(font, 'I', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5, t['legal_text'], border=1, align='L')
    pdf.output(output_pdf)

def update_pdf_inplace(original_report, appendix_pdf):
    # Merge PDFs and overwrite the original file
    # Scal PDFy i nadpisz oryginalny plik
    writer = PdfWriter()
    try:
        # Read Original
        # Czytaj Oryginał
        reader_orig = PdfReader(original_report)
        for page in reader_orig.pages:
            writer.add_page(page)
        
        # Read Appendix
        # Czytaj Załącznik
        reader_app = PdfReader(appendix_pdf)
        for page in reader_app.pages:
            writer.add_page(page)

        # Write to temp file first
        # Najpierw zapisz do pliku tymczasowego
        temp_merged_name = original_report + ".tmp_merged"
        with open(temp_merged_name, "wb") as f_out:
            writer.write(f_out)
        
        # Replace original with merged
        # Zastąp oryginał scalonym
        os.replace(temp_merged_name, original_report)
        
        print(f"      📎 Updated (In-Place): {os.path.basename(original_report)}")
        print(f"      📎 Zaktualizowano (W miejscu): {os.path.basename(original_report)}")
    except Exception as e:
        print(f"❌ Error merging PDF: {e}")
        print(f"❌ Błąd scalania PDF: {e}")

# --- MAIN EXECUTION ---
# --- GŁÓWNE WYKONANIE ---

def main():
    # Clear terminal
    # Wyczyść terminal
    os.system("clear || cls")
    
    print("="*60)
    print("=== REPORT FINISHER v12.3 (YAML CONFIG + IN-PLACE) ===")
    print("=== FINALIZATOR RAPORTÓW v12.3 (KONFIGURACJA YAML + NADPISYWANIE) ===")
    print("="*60)
    
    # Load configuration
    # Wczytaj konfigurację
    config = load_config()
    if not config: 
        print("❌ Config file not found!")
        print("❌ Nie znaleziono pliku konfiguracyjnego!")
        return
    
    gcp_conf = config.get('GLOBAL_SETTINGS', {}).get('gcp', {})
    project_id = gcp_conf.get('project_id')
    zone = gcp_conf.get('zone')
    
    # --- LIST CANDIDATES ---
    # --- LISTA KANDYDATÓW ---
    candidates = []
    for key, val in config.items():
        if key in ['GLOBAL_SETTINGS', 'LOCAL_CONFIG', 'LOCAL_PATHS']: continue
        if isinstance(val, dict) and 'name' in val:
            candidates.append((key, val['name']))

    if not candidates:
        print("❌ No VM found in config!")
        print("❌ Nie znaleziono VM w konfiguracji!")
        return

    target_key = None
    target_vm_name = None

    print("\n🔎 Targets detected. Select VM to Finalize:")
    print("🔎 Wykryto cele. Wybierz VM do finalizacji:")
    for idx, (k, n) in enumerate(candidates):
        print(f"   [{idx+1}] {k} -> {n}")
        
    try:
        print("\n👉 Enter number: ")
        print("👉 Wpisz numer: ")
        choice = int(input("> "))
        if 1 <= choice <= len(candidates):
            target_key, target_vm_name = candidates[choice-1]
            print(f"✅ Selected: {target_vm_name}")
            print(f"✅ Wybrano: {target_vm_name}")
        else:
            print("❌ Invalid selection."); return
    except ValueError:
        print("❌ Invalid input."); return
            
    snap_name = manage_vm_lifecycle(target_vm_name, project_id, zone)
    if not snap_name: return

    snap_data = get_snapshot_details(snap_name, project_id)
    if snap_data:
        print(f"\n🔗 DISK_IMAGE URI:\n{snap_data['link']}")
        print(f"🕒 TIMESTAMP: {snap_data['time']}")
        # RESTORED LOGIC REQUESTED
        print(f"💾 DISK INFO: {snap_data['size']}\n")

    pcaps_full = get_pcap_full_paths()
    pcaps_pdf = get_pcap_list_for_pdf()
    print(f"🔍 Found {len(pcaps_full)} PCAP files.")
    print(f"🔍 Znaleziono {len(pcaps_full)} plików PCAP.")

    # --- PROCESS ALL REPORT VARIANTS ---
    # --- PRZETWARZANIE WSZYSTKICH WARIANTÓW RAPORTÓW ---
    
    # Find base reports (Auditor output)
    reports = glob.glob("*PORT_*.pdf")
    # Filter out temp files just in case
    reports = [r for r in reports if "temp" not in r]
    
    if not reports:
        print("❌ No base reports found! Run auditor_smart.py first.")
        print("❌ Nie znaleziono raportów bazowych! Uruchom najpierw auditor_smart.py.")
        return

    # In-place update list
    final_reports = [] 

    for report in reports:
        lang = 'EN' if 'REPORT' in report else 'PL'
        print(f"\nProcessing {report} [{lang}]...")
        print(f"Przetwarzanie {report} [{lang}]...")
        
        temp = f"temp_appendix_{lang}.pdf"
        
        # GENERATE APPENDIX B (NO CENSORSHIP)
        # GENERUJ ZAŁĄCZNIK B (BEZ CENZURY)
        create_appendix_b(lang, temp, pcaps_pdf, snap_data)
        
        # MERGE AND OVERWRITE
        # SCAL I NADPISZ
        update_pdf_inplace(report, temp)
        
        final_reports.append(report)
        os.remove(temp)

    create_master_bundle(final_reports, pcaps_full, snap_data, target_key, target_vm_name)

    print("\n" + "="*60)
    print("🎉 REPORT COMPLETE")
    print("🎉 RAPORT UKOŃCZONY")
    print("="*60)

if __name__ == "__main__":
    main()
