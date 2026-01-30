#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import yaml
import datetime
import glob
from fpdf import FPDF, XPos, YPos
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("❌ Critical Error: 'pypdf' library is missing.")
    exit(1)

CONFIG_FILE = 'config.yaml'
FONTS = {'R': "UbuntuMono-Regular.ttf", 'B': "UbuntuMono-Bold.ttf"}

# --- TEXT CONSTANTS (PL/EN) ---
TEXTS = {
    'PL': {
        'title': "ZAŁĄCZNIK C: SKAN ANTYWIRUSOWY (CLAMAV)",
        'box_title': "UWAGA: ANALIZA FAŁSZYWYCH ALARMÓW I BŁĘDÓW SYSTEMOWYCH",
        'box_body': (
            "1. WYKRYTE ZAGROŻENIA (False Positive): Pliki w ścieżkach zawierających 'Neo23x0_signature-base' "
            "to bazy sygnatur YARA używane przez system obronny MALCOLM. Nie stanowią one zagrożenia, lecz są "
            "częścią mechanizmu wykrywania ataków.\n\n"
            "2. BŁĘDY DOSTĘPU (Not supported file type/Failed to open): Ostrzeżenia dotyczące katalogów '/sys', "
            "'/proc', '/dev', '/run' wynikają z architektury systemu Linux (są to wirtualne systemy plików). "
            "Ich występowanie podczas pełnego skanowania systemu (root scan) jest naturalne, ponieważ ClamAV "
            "nie może odczytać strumieni systemowych jako zwykłych plików."
        )
    },
    'EN': {
        'title': "APPENDIX C: ANTIVIRUS SECURITY SCAN (CLAMAV)",
        'box_title': "NOTE: ANALYSIS OF FALSE POSITIVES AND SYSTEM ERRORS",
        'box_body': (
            "1. DETECTED THREATS (False Positive): Files located in 'Neo23x0_signature-base' paths are YARA "
            "signatures used by the MALCOLM defense system. They are not active threats but part of the attack "
            "detection mechanism.\n\n"
            "2. ACCESS ERRORS (Not supported file type/Failed to open): Warnings regarding '/sys', '/proc', "
            "'/dev', '/run' directories stem from Linux architecture (virtual filesystems). Their presence "
            "during a full system scan is expected as ClamAV cannot read system streams as regular files."
        )
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE): return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return yaml.safe_load(f)

def run_ssh_task(host_ip, user, cmd):
    print(f"\n🔄 Executing remote scan on {host_ip} (Turbo Mode - FULL SYSTEM)...")
    print(f"🔄 Wykonywanie zdalnego skanowania na {host_ip} (Tryb Turbo - PEŁNY SYSTEM)...")
    ssh = ['ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{host_ip}', cmd]
    try:
        # Increase timeout significantly for full scan
        res = subprocess.run(ssh, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        print(f"❌ SSH Error: {e}")
        return None

class ClamReportPDF(FPDF):
    def __init__(self, lang='EN'):
        super().__init__()
        self.lang = lang

    def header(self):
        if os.path.exists(FONTS['R']):
            self.add_font('UbuntuMono', '', FONTS['R'])
            self.add_font('UbuntuMono', 'B', FONTS['B'])
            self.set_font('UbuntuMono', 'B', 14)
        else:
            self.set_font('Courier', 'B', 14)
        
        title_text = TEXTS[self.lang]['title']
        self.cell(0, 10, title_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

def generate_pdf_for_lang(lang, output_data, filename):
    pdf = ClamReportPDF(lang)
    pdf.add_page()
    
    # Use smaller font to fit more errors per page
    if os.path.exists(FONTS['R']):
        pdf.set_font('UbuntuMono', '', 8) 
    else:
        pdf.set_font('Courier', '', 8)
    
    # 1. ADD SCAN CONTENT
    summary_started = False
    for line in output_data.split('\n'):
        line = line.strip()
        if not line: continue

        # Header for summary - Bold
        if "----------- SCAN SUMMARY -----------" in line:
            summary_started = True
            pdf.ln(5)
            pdf.set_font('', 'B', 10)
            pdf.cell(0, 8, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('', '', 8)
            continue
        
        # Determine color and wrap logic
        if summary_started:
            # Summary lines are short, cell is fine, but let's use multi_cell for consistency
            pdf.multi_cell(0, 4, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif "FOUND" in line:
            # Threats in RED
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 4, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)
        elif "Infected files:" in line:
             pdf.set_font('', 'B', 10)
             pdf.multi_cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
             pdf.set_font('', '', 8)
        else:
            # WARNINGS / ERRORS / NORMAL LINES
            # FORCE WRAPPING FOR EVERYTHING using multi_cell
            pdf.multi_cell(0, 4, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # 2. ADD EXPLANATORY FRAME (RAMKA)
    pdf.add_page() 
    pdf.ln(5)
    
    # Title of the box
    pdf.set_font('', 'B', 11)
    pdf.multi_cell(0, 6, TEXTS[lang]['box_title'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    
    # Content of the box
    pdf.set_font('', '', 10)
    pdf.ln(2)
    
    # Create a visual box (border=1) with multi-line explanation
    pdf.multi_cell(0, 6, TEXTS[lang]['box_body'], border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.output(filename)

def main():
    os.system("clear || cls")
    print("=" * 60)
    print("=== SMART AUDITOR: CLAMAV (v2.5 FINAL) ===")
    print("=" * 60)

    config = load_config()
    if not config: return
    vms = {k: v for k, v in config.items() if isinstance(v, dict) and 'name' in v}
    
    print("\nAvailable VMs / Dostępne VM:")
    for k, v in vms.items(): print(f" [{k}] {v['name']}")
    key = input("\nSelect VM Key / Wybierz Klucz VM:\n> ").strip().upper()
    if key not in vms: return
    
    vm = vms[key]
    user = vm.get('admin_user', 'blox_tak_server_admin')
    ip = vm.get('internal_ip')

    log_file = f"/root/clam_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
    
    # FULL SCAN on '/'
    scan_cmd = (
        f"sudo clamdscan --multiscan --fdpass "
        f"--log='{log_file}' /; "
        f"sudo cat {log_file}"
    )

    # Execute Scan
    output = run_ssh_task(ip, user, scan_cmd)
    if not output: 
        print("❌ No output / Brak danych")
        return

    print("✅ Scan Complete. Generating PDF assets...")

    # Generate Temp PDFs
    temp_pl = "temp_clamav_PL.pdf"
    temp_en = "temp_clamav_EN.pdf"
    
    generate_pdf_for_lang('PL', output, temp_pl)
    generate_pdf_for_lang('EN', output, temp_en)

    # Merge Logic
    files = glob.glob(f"*{vm['name']}*.pdf")
    if not files:
        print("⚠️  No reports found to append to.")

    for report_file in files:
        if "temp_clamav" in report_file: continue
        
        # Detect Language
        if "_PL" in report_file:
            source_temp = temp_pl
            lang_detected = "PL"
        else:
            source_temp = temp_en
            lang_detected = "EN"

        print(f"\n📎 Appending [{lang_detected}] to: {report_file}")
        
        try:
            reader_base = PdfReader(report_file)
            reader_clam = PdfReader(source_temp)
            writer = PdfWriter()
            
            for p in reader_base.pages: writer.add_page(p)
            for p in reader_clam.pages: writer.add_page(p)
            
            with open(report_file, "wb") as f_out: writer.write(f_out)
            print("✅ Success")
        except Exception as e: print(f"❌ Merge Error: {e}")

    # Cleanup
    if os.path.exists(temp_pl): os.remove(temp_pl)
    if os.path.exists(temp_en): os.remove(temp_en)

    print("\n✨ Done.")

if __name__ == "__main__":
    main()
