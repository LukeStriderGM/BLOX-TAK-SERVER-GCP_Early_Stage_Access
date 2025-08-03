# =====================================================================================
# === TERRAFORM CONFIGURATION FOR GOOGLE CLOUD VM (v2.0 - Centralized Variables) ===
# === KONFIGURACJA TERRAFORM DLA MASZYNY WIRTUALNEJ W GOOGLE CLOUD (v2.0 - Zmienne Scentralizowane) ===
# =====================================================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.25.0"
    }
  }
}

# --- Zmienne wejściowe / Input Variables ---
# Te zmienne są przekazywane przez skrypt deploy_vm.py z pliku config.yaml
# This variables are passed from the deploy_vm.py script from the config.yaml file

# Zmienne podstawowe
variable "instance_name" {
  description = "The name of the Compute Engine instance. / Nazwa instancji Compute Engine."
  type        = string
}
variable "root_password" {
  description = "The password for the admin user. / Hasło dla użytkownika."
  type        = string
  sensitive   = true
}
variable "ssh_public_key" {
  description = "Public SSH key for the admin user. / Publiczny klucz SSH dla użytkownika."
  type        = string
  sensitive   = true
}

# Zmienne z GLOBAL_SETTINGS.gcp
variable "gcp_project_id" {
  description = "Google Cloud Project ID. / ID projektu w Google Cloud."
  type        = string
}
variable "gcp_region" {
  description = "Google Cloud Region. / Region w Google Cloud."
  type        = string
}
variable "gcp_zone" {
  description = "Google Cloud Zone. / Strefa w Google Cloud."
  type        = string
}

# Zmienne z GLOBAL_SETTINGS.vm
variable "vm_machine_type" {
  description = "The machine type for the VM. / Typ maszyny dla VM."
  type        = string
}
variable "vm_disk_image" {
  description = "The boot disk image for the VM. / Obraz dysku startowego dla VM."
  type        = string
}
variable "vm_disk_size_gb" {
  description = "The boot disk size in GB. / Rozmiar dysku startowego w GB."
  type        = number
}
variable "vm_disk_type" {
  description = "The boot disk type. / Typ dysku startowego."
  type        = string
}
variable "vm_admin_user" {
  description = "The username for the admin user on the VM. / Nazwa użytkownika admina na VM."
  type        = string
}

# --- Konfiguracja dostawcy / Provider Configuration ---

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# --- Główny zasób maszyny wirtualnej / Main VM Resource ---

resource "google_compute_instance" "tak-server-vm" {
  name         = var.instance_name
  zone         = var.gcp_zone
  machine_type = var.vm_machine_type

  boot_disk {
    auto_delete = true
    device_name = var.instance_name
    initialize_params {
      image = var.vm_disk_image
      size  = var.vm_disk_size_gb
      type  = var.vm_disk_type
    }
    mode = "READ_WRITE"
  }

  metadata = {
    # Dodanie klucza SSH do autoryzowanych kluczy użytkownika
    ssh-keys = "${var.vm_admin_user}:${var.ssh_public_key}"

    # Konfiguracja początkowa maszyny za pomocą cloud-init
    user-data = <<-EOT
      #cloud-config

      # Stwórz nowego użytkownika z uprawnieniami sudo
      users:
        - name: ${var.vm_admin_user}
          sudo: ALL=(ALL) NOPASSWD:ALL
          groups: [adm, sudo]
          shell: /bin/bash

      # Ustaw hasło dla nowego użytkownika
      chpasswd:
        list: |
          ${var.vm_admin_user}:${var.root_password}
        expire: False

      # Rekomendacja: Wyłącz logowanie hasłem, skoro mamy klucze SSH
      runcmd:
        - [ sed, -i, -e, 's/^#?PasswordAuthentication .*/PasswordAuthentication no/g', /etc/ssh/sshd_config ]
        - [ systemctl, restart, sshd ]
    EOT
  }

  network_interface {
    subnetwork = "projects/${var.gcp_project_id}/regions/${var.gcp_region}/subnetworks/default"
    access_config {
      network_tier = "PREMIUM"
    }
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  shielded_instance_config {
    enable_integrity_monitoring = true
    enable_secure_boot          = true
    enable_vtpm                 = true
  }

  deletion_protection = true
  can_ip_forward      = false
  enable_display      = false
  hostname            = "takserver.local"
  tags                = ["tak-server"]

  labels = {
    goog-ec-src         = "vm_add-tf"
    goog-ops-agent-policy = "v2-x86-template-1-4-0"
  }
}