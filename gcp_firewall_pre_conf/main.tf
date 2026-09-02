# =====================================================================================
# === PRE-CONFIGURATION: GCP FIREWALL RULES (YAML DRIVEN) ===
# === PRE-KONFIGURACJA: REGUŁY ZAPORY SIECIOWEJ GCP (STEROWANE YAML) ===
# =====================================================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.25.0"
    }
  }
}

# =====================================================================================
# === VARIABLES & DATA SOURCES / ZMIENNE I ŹRÓDŁA DANYCH ===
# =====================================================================================

# English: Fetch and decode the main config.yaml file from the parent directory.
# Polski:  Zaciągnij i zdekoduj główny plik config.yaml z katalogu nadrzędnego.
locals {
  config         = yamldecode(file("../config.yaml"))
  gcp_project_id = local.config.GLOBAL_SETTINGS.gcp.project_id
  admin_ext_ip   = local.config.GLOBAL_SETTINGS.security.admin_ext_ip
}

# English: Provider configuration pulled dynamically from YAML.
# Polski:  Konfiguracja dostawcy zaciągnięta dynamicznie z YAML.
provider "google" {
  project = local.gcp_project_id
}

# =====================================================================================
# === FIREWALL RULES / REGUŁY ZAPORY SIECIOWEJ ===
# =====================================================================================

# --- SSH Access Rule / Reguła dostępu SSH ---
resource "google_compute_firewall" "ssh_22" {
  name    = "ssh-22"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # English: Restrict SSH access strictly to the Admin's IP defined in config.yaml.
  # Polski:  Ogranicz dostęp SSH rygorystycznie do IP Administratora zdefiniowanego w config.yaml.
  source_ranges = [local.admin_ext_ip]
  target_tags   = ["tak-server"]
  description   = "Allow SSH Access strictly from Admin IP"
}

# --- WireGuard VPN Traffic Rule / Reguła ruchu WireGuard VPN ---
resource "google_compute_firewall" "wire_guard" {
  name    = "wire-guard"
  network = "default"

  allow {
    protocol = "udp"
    ports    = ["51820"]
  }

  # English: WireGuard port must be open to the internet to accept encrypted handshakes.
  # Polski:  Port WireGuard musi być otwarty na świat, aby przyjmować szyfrowane uściski dłoni.
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["tak-server"]
  description   = "Allow WireGuard VPN Encrypted Traffic"
}