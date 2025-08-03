# 🇺🇸 BLOX-TAK-SERVER-GCP (Early Stage Access)

Welcome to the early stage private repository for the **BLOX-TAK-SERVER-GCP** project. This suite of scripts is designed to provide a robust, secure, and highly automated foundation for deploying a TAK (Team Awareness Kit) ecosystem on the Google Cloud Platform.

This repository is currently shared with a select group of authorities, mentors, and leaders within the TAK community for feedback, discussion, and testing. The goal is to refine this core infrastructure before a potential public release.

<details>

<summary>🇵🇱 [Kliknij Trójkąt Po Lewej Stronie Aby Rozwinąć Opis w Języku Polskim]</summary>

# 🇵🇱 BLOX-TAK-SERVER-GCP (Dostęp Do Wczesnego Etapu)

Witaj we wczesnym, prywatnym repozytorium projektu **BLOX-TAK-SERVER-GCP**. Ten pakiet skryptów został zaprojektowany, aby zapewnić solidną, bezpieczną i wysoce zautomatyzowaną podstawę do wdrażania ekosystemu TAK (Team Awareness Kit) na platformie Google Cloud Platform.

To repozytorium jest obecnie udostępniane wybranej grupie autorytetów, mentorów i liderów w społeczności TAK w celu uzyskania opinii, dyskusji i testów. Celem jest udoskonalenie tej podstawowej infrastruktury przed potencjalnym publicznym wydaniem.

</details>

---

## 🇺🇸 Core Features

This package contains the foundational scripts to deploy and manage a complete server instance from scratch. The entire process, from a clean GCP project to a fully operational server with an admin and first client, can be completed in **under one hour**.

* **Automated VM Deployment**: Utilizes **Terraform** to create and configure a secure GCP virtual machine based on Ubuntu 22.04 LTS.
* **Mandatory Hardware-Key Security**: Enforces the use of a **YubiKey** (or similar FIDO/U2F key) for all SSH administrative access, eliminating password-based logins.
* **Automated WireGuard VPN**: Deploys a WireGuard server for secure, encrypted communication tunnels. Includes scripts to configure both admin (split-tunnel by default) and end-user (split-tunnel by default) clients.
* **For mission-critical security**, at this stage you can manually switch to the full-tunnel function, which completely cuts off external network traffic and allows you to operate only in a pure TAK ecosystem.
* **Docker & TAK Server Installation**: Fully automates the installation of Docker and the TAK Server itself, including downloading necessary files from Google Drive.
* **Client & Certificate Management**: Includes Python scripts to add new SSH keys and configure clients for WireGuard.
* **Bilingual Interface**: All scripts provide interactive prompts and status messages in both English and Polish.

<details>

<summary>🇵🇱</summary>

## 🇵🇱 Główne Funkcjonalności

Ten pakiet zawiera podstawowe skrypty do wdrożenia i zarządzania kompletną instancją serwera od zera. Cały proces, od czystego projektu GCP do w pełni działającego serwera z administratorem i pierwszym klientem, można ukończyć w **mniej niż godzinę**.

* **Automatyczne Wdrożenie Maszyny Wirtualnej**: Wykorzystuje **Terraform** do tworzenia i konfigurowania bezpiecznej maszyny wirtualnej GCP opartej na Ubuntu 22.04 LTS.
* **Wymuszone Bezpieczeństwo Kluczem Sprzętowym**: Wymusza użycie **YubiKey** (lub podobnego klucza FIDO/U2F) do całego administracyjnego dostępu przez SSH, eliminując logowanie oparte na haśle.
* **Automatyczny VPN WireGuard**: Wdraża serwer WireGuard do bezpiecznych, szyfrowanych tuneli komunikacyjnych. Zawiera skrypty do konfiguracji zarówno klientów administracyjnych (domyślnie split-tunnel), jak i końcowych użytkowników (domyślnie split-tunnel).
* **Dla bezpieczeństwa misji o znaczeniu krytycznym**, na tym etapie można przejść ręcznie na funkcję full-tunnel która całkowicie odcina zewnętrzny ruch z sieci i pozwala operować tylko w czystym ekosystemie TAK.
* **Instalacja Dockera i Serwera TAK**: W pełni automatyzuje instalację Dockera i samego Serwera TAK, w tym pobieranie niezbędnych plików z Dysku Google.
* **Zarządzanie Klientami i Certyfikatami**: Zawiera skrypty Pythona do dodawania nowych kluczy SSH i konfigurowania klientów dla WireGuard.
* **Dwujęzyczny Interfejs**: Wszystkie skrypty zapewniają interaktywne monity i komunikaty o stanie w języku angielskim i polskim.

</details>

---

## 🇺🇸 Prerequisites

To use these scripts, you will need the following on your **local admin machine** (which should be Ubuntu 22.04 for full compatibility):

1.  **Google Cloud Platform (GCP) Account**: A GCP account with an active project and billing enabled.
2.  **Google Cloud CLI**: The `gcloud` command-line tool installed and authenticated.
3.  **Terraform**: The Terraform CLI installed.
4.  **YubiKey (or other FIDO/U2F key)**: A hardware security key for generating your `ed25519-sk` SSH key. **This is not optional.**
5.  **Python 3 & Dependencies**.

<details>

<summary>🇵🇱</summary>

## 🇵🇱 Wymagania Wstępne

Do użycia tych skryptów potrzebne będą następujące elementy na Twojej **lokalnej maszynie administracyjnej** (która dla pełnej kompatybilności powinna być oparta na Ubuntu 22.04):

1.  **Konto Google Cloud Platform (GCP)**: Konto GCP z aktywnym projektem i włączonymi płatnościami.
2.  **Google Cloud CLI**: Zainstalowane i uwierzytelnione narzędzie wiersza poleceń `gcloud`.
3.  **Terraform**: Zainstalowany interfejs CLI Terraform.
4.  **YubiKey (lub inny klucz FIDO/U2F)**: Sprzętowy klucz bezpieczeństwa do wygenerowania Twojego klucza SSH `ed25519-sk`. **To nie jest opcjonalne.**
5.  **Python 3 i Zależności**.

</details>

---

## 🇺🇸 Deployment Guide / 🇵🇱 Instrukcja Wdrożenia

Follow these steps in order to set up your complete TAK Server ecosystem.

### 🇺🇸 Step 1: Prerequisites, Setup, and Firewall Configuration

This initial step covers everything you need to do on your **local admin machine** and in the **GCP Console** before deploying the virtual machine.

### Part A: Local Admin Machine Setup

1.  **Install Core Dependencies**:
    * First, update your system and install Python, pip, venv, and other required tools like `qrencode` and `wireguard`.
        ```bash
        sudo apt-get update && sudo apt-get install -y python3-pip python3-venv qrencode wireguard apt-transport-https ca-certificates curl
        ```

2.  **Install Google Cloud CLI**:
    * Add the gcloud CLI package source and install the command-line tool.
        ```bash
        curl -fsSL [https://packages.cloud.google.com/apt/doc/apt-key.gpg](https://packages.cloud.google.com/apt/doc/apt-key.gpg) | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
        echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] [https://packages.cloud.google.com/apt](https://packages.cloud.google.com/apt) cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
        sudo apt-get update && sudo apt-get install -y google-cloud-cli
        ```

3.  **Install Terraform**:
    * Add the HashiCorp repository and install Terraform.
        ```bash
        sudo curl -fsSL [https://apt.releases.hashicorp.com/gpg](https://apt.releases.hashicorp.com/gpg) | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] [https://apt.releases.hashicorp.com](https://apt.releases.hashicorp.com) $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update && sudo apt-get install -y terraform
        ```

4.  **Configure GCP Account & Generate SSH Key**:
    * Log in to your GCP account, set the project, and generate a new hardware-backed SSH key. **A YubiKey (or similar FIDO/U2F key) is mandatory.**
        ```bash
        # Log in to your Google Account (will open a browser)
        gcloud auth login

        # Set your target GCP Project ID
        gcloud config set project <YOUR_PROJECT_ID>

        # Generate a new security key-backed SSH key
        ssh-keygen -t ed25519-sk -C "your_email@example.com"
        ```

5.  **Clone Repository & Install Python Dependencies**:
    * Finally, clone the project repository and install the required Python packages.
        ```bash
        git clone <URL_TO_THIS_PRIVATE_REPOSITORY>
        cd BLOX-TAK-SERVER-GCP
        pip install -r requirements.txt
        ```

### Part B: GCP Firewall Configuration

Before deploying the virtual machine, you must configure the firewall in your GCP project's VPC network to allow necessary traffic.

1.  Navigate to **VPC network -> Firewall** in your Google Cloud Console.
2.  Click **CREATE FIREWALL RULE** and create the following two rules:

#### Rule 1: Allow SSH Access from Admin IP
* **Name**: `ssh-22`
* **Direction of traffic**: `Ingress`
* **Action on match**: `Allow`
* **Targets**: `Specified target tags`
* **Target tags**: `tak-server`
* **Source filter**: `IPv4 ranges`
* **Source IPv4 ranges**: `0.0.0.0/32` (Enter your own admin IP here)
* **Protocols and ports**: `Specified protocols and ports` -> `tcp`: `22`

#### Rule 2: Allow WireGuard VPN Traffic
* **Name**: `wire-guard`
* **Direction of traffic**: `Ingress`
* **Action on match**: `Allow`
* **Targets**: `Specified target tags`
* **Target tags**: `tak-server`
* **Source filter**: `IPv4 ranges`
* **Source IPv4 ranges**: `0.0.0.0/0`
* **Protocols and ports**: `Specified protocols and ports` -> `udp`: `51820`

<details>
<summary>🇵🇱</summary>

### 🇵🇱 Krok 1: Wymagania, Konfiguracja i Reguły Zapory Sieciowej

Ten początkowy krok obejmuje wszystko, co musisz zrobić na swojej **lokalnej maszynie administracyjnej** oraz w **Konsoli GCP** przed wdrożeniem maszyny wirtualnej.

### Część A: Konfiguracja Lokalnej Maszyny Administracyjnej

1.  **Zainstaluj Podstawowe Zależności**:
    * Najpierw zaktualizuj system i zainstaluj Python, pip, venv oraz inne wymagane narzędzia, takie jak `qrencode` i `wireguard`.
        ```bash
        sudo apt-get update && sudo apt-get install -y python3-pip python3-venv qrencode wireguard apt-transport-https ca-certificates curl
        ```

2.  **Zainstaluj Google Cloud CLI**:
    * Dodaj źródło pakietów gcloud CLI i zainstaluj narzędzie wiersza poleceń.
        ```bash
        curl -fsSL [https://packages.cloud.google.com/apt/doc/apt-key.gpg](https://packages.cloud.google.com/apt/doc/apt-key.gpg) | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
        echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] [https://packages.cloud.google.com/apt](https://packages.cloud.google.com/apt) cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
        sudo apt-get update && sudo apt-get install -y google-cloud-cli
        ```

3.  **Zainstaluj Terraform**:
    * Dodaj repozytorium HashiCorp i zainstaluj Terraform.
        ```bash
        sudo curl -fsSL [https://apt.releases.hashicorp.com/gpg](https://apt.releases.hashicorp.com/gpg) | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] [https://apt.releases.hashicorp.com](https://apt.releases.hashicorp.com) $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update && sudo apt-get install -y terraform
        ```

4.  **Skonfiguruj Konto GCP i Wygeneruj Klucz SSH**:
    * Zaloguj się na swoje konto GCP, ustaw projekt i wygeneruj nowy klucz SSH wspierany sprzętowo. **Klucz YubiKey (lub podobny klucz FIDO/U2F) jest obowiązkowy.**
        ```bash
        # Zaloguj się na swoje konto Google (otworzy się przeglądarka)
        gcloud auth login

        # Ustaw docelowy identyfikator projektu GCP
        gcloud config set project <TWÓJ_PROJECT_ID>

        # Wygeneruj nowy klucz SSH oparty na kluczu bezpieczeństwa
        ssh-keygen -t ed25519-sk -C "twoj_email@example.com"
        ```

5.  **Sklonuj Repozytorium i Zainstaluj Zależności Python**:
    * Na koniec sklonuj repozytorium projektu i zainstaluj wymagane pakiety Python.
        ```bash
        git clone <URL_DO_TEGO_PRYWATNEGO_REPOZYTORIUM>
        cd BLOX-TAK-SERVER-GCP
        pip install -r requirements.txt
        ```

### Część B: Konfiguracja Reguł Zapory Sieciowej GCP

Przed wdrożeniem maszyny wirtualnej musisz skonfigurować zaporę sieciową (firewall) w sieci VPC swojego projektu GCP, aby zezwolić na niezbędny ruch.

1.  W konsoli Google Cloud przejdź do **Sieć VPC -> Zapora sieciowa**.
2.  Kliknij **UTWÓRZ REGUŁĘ ZAPORY SIECIOWEJ** i utwórz dwie poniższe reguły:

#### Reguła 1: Zezwól na Dostęp SSH z Adresu IP Administratora
* **Nazwa**: `ssh-22`
* **Kierunek ruchu**: `Przychodzący`
* **Działanie w przypadku dopasowania**: `Zezwalaj`
* **Cele**: `Określone tagi docelowe`
* **Tagi docelowe**: `tak-server`
* **Filtr źródłowy**: `Zakresy IPv4`
* **Źródłowe zakresy IPv4**: `0.0.0.0/32` (Wprowadź tutaj własny adres IP administratora)
* **Protokoły i porty**: `Określone protokoły i porty` -> `tcp`: `22`

#### Reguła 2: Zezwól na Ruch VPN WireGuard
* **Nazwa**: `wire-guard`
* **Kierunek ruchu**: `Przychodzący`
* **Działanie w przypadku dopasowania**: `Zezwalaj`
* **Cele**: `Określone tagi docelowe`
* **Tagi docelowe**: `tak-server`
* **Filtr źródłowy**: `Zakresy IPv4`
* **Źródłowe zakresy IPv4**: `0.0.0.0/0`
* **Protokoły i porty**: `Określone protokoły i porty` -> `udp`: `51820`

</details>

---

### 🇺🇸 Step 2: Deploy the GCP Virtual Machine

This script uses Terraform to create the VM, sets up a dedicated user, and adds your YubiKey public key for access.

```bash
# Initialize Terraform
terraform init

# Run the deployment script
python3 deploy_vm.py
```
The script will automatically create a config.yaml file with the new VM's details.

### Step 3: Configure VPN & Core Services

Install WireGuard on the Server:

```bash
python3 install_wireguard.py
```

Configure Your Admin VPN Peer:
This creates a local WireGuard configuration to connect your admin machine to the server's private network.

```bash
python3 configure_peer.py
```

After it completes, activate the tunnel:

```bash
# The path will be shown at the end of the script's output
sudo wg-quick up /etc/wireguard/admin_VM1/admin.conf
```
VM1, VM2, VM3 ...

You should now be able to connect to the server using its internal VPN IP (e.g., 10.200.0.1). 2, 3 ... 

<br>
Install Docker:
This script will connect to the server over the VPN to perform the installation.

```bash
python3 install_docker.py
```

### Step 4: Install TAK Server

Download TAK Server Files to the VM:
This script uses gdown on the remote server to download the necessary TAK Server zip file.

```bash
python3 gdown.py
```

Run the TAK Server Setup:
This is an interactive script that will guide you through the TAK server installation on the remote machine.

```bash
python3 setup.py
```

After the installation is complete, it will automatically copy the generated client certificates to your local machine.

### Step 5: Configure Clients
Add an Android WireGuard Client:
This will generate a QR code to easily add a new VPN profile to the WireGuard app on an Android device. By default, this tunnel is configured for split-tunnel traffic to conserve battery and allow normal phone operation. It can be manually changed to full-tunnel if the mission requires it.

```bash
python3 configure_peer_android.py
```

Your basic TAK server ecosystem is now operational!

<details>

<summary>🇵🇱</summary>

### 🇵🇱 Krok 2: Wdróż Maszynę Wirtualną GCP
Ten skrypt używa Terraform do stworzenia maszyny wirtualnej, konfiguruje dedykowanego użytkownika i dodaje Twój publiczny klucz YubiKey w celu uzyskania dostępu.

```bash
# Zainicjuj Terraform
terraform init
# Uruchom skrypt wdrożeniowy
python3 deploy_vm.py
```

Skrypt automatycznie utworzy plik config.yaml ze szczegółami nowej maszyny wirtualnej.

### Krok 3: Skonfiguruj VPN i Podstawowe Usługi

Zainstaluj WireGuard na Serwerze:

```bash
python3 install_wireguard.py
```

Skonfiguruj Swój Administracyjny Peer VPN:
Tworzy to lokalną konfigurację WireGuard do połączenia Twojej maszyny administracyjnej z prywatną siecią serwera.


```bash
python3 configure_peer.py
```

Po zakończeniu, aktywuj tunel:

```bash
# Ścieżka zostanie pokazana na końcu wyniku skryptu
sudo wg-quick up /etc/wireguard/admin_VM1/admin.conf
```

VM1, VM2, VM3 ...

Powinieneś teraz móc połączyć się z serwerem, używając jego wewnętrznego adresu IP VPN (np. 10.200.0.1). 2, 3 ...

<br>
Zainstaluj Docker:
Ten skrypt połączy się z serwerem przez VPN, aby przeprowadzić instalację.

```bash
python3 install_docker.py
```

### Krok 4: Zainstaluj Serwer TAK

Pobierz Pliki Serwera TAK na Maszynę Wirtualną:
Ten skrypt używa gdown na zdalnym serwerze do pobrania wymaganego pliku zip Serwera TAK.

```bash
python3 gdown.py
```

Uruchom Instalator Serwera TAK:
To interaktywny skrypt, który przeprowadzi Cię przez proces instalacji serwera TAK na zdalnej maszynie.

```bash
python3 setup.py
```

Po zakończeniu instalacji, automatycznie skopiuje wygenerowane certyfikaty klienta na Twoją lokalną maszynę.

### Krok 5: Skonfiguruj Klientów

Dodaj Klienta WireGuard na Androida:
Wygeneruje to kod QR, aby łatwo dodać nowy profil VPN do aplikacji WireGuard na urządzeniu z Androidem. Domyślnie ten tunel jest skonfigurowany jako split-tunnel, aby oszczędzać baterię i umożliwiać normalne działanie telefonu. Można go ręcznie zmienić na full-tunnel, jeśli misja tego wymaga.

```bash
python3 configure_peer_android.py
```

Twój podstawowy ekosystem serwera TAK jest teraz gotowy do działania!

</details>

---

## 🇺🇸 This repository provides the core infrastructure for the TAK ecosystem.

### Extended options enable automatic configuration of the MUMBLE-MURMUR server for VoIP communication using the VOICE plugin in the ATAK application.

There is also the option to run a "drone simulation" for testing with the UAS-TOOL plugin. If needed, I am also ready to undertake the first-time integration of physical drones compatible with this plugin: in the BLOX-TAK-SERVER-GCP.

### But the true power of the BLOX-TAK-SERVER-GCP ecosystem is realized in cooperation with the BLOX-TAK-SERVER-UCP-GCP software package (IUCP - Individual User Connection Profile).

The IUCP project integrates directly with this GCP foundation and provides:

* **Automated Onboarding from Google Forms:** Automatically processes new user submissions from a Google Form or a CSV file.
* **Bulk Certificate Generation:** Generates and signs TAK .p12 client certificates for dozens of users simultaneously.
* **Automated Configuration Packaging:** Creates user-specific .zip packages containing their certificate, ATAK preferences (.pref), and other necessary files.
* **Automated Email Distribution:** Securely delivers the user package directly to their inbox using the Gmail API.
* **Advanced Maintenance:** Scripts for bulk certificate revocation and user lifecycle management.

The IUCP extension transforms an hour-long server configuration into a system where adding a new, fully prepared user takes less than a minute of automated work.

<details>

<summary>🇵🇱</summary>

## 🇵🇱 To repozytorium dostarcza podstawową infrastrukturę ekosystemu TAK.

### Opcje rozszerzone zapweniają automatyczną konfigurację serwera MUMBLE-MURMUR dla komunikacji VoIP dla wtyczki VOICE w aplikacji ATAK.

Jest również możliwość uruchomienia "symulacji drona" do testów z wtyczką UAS-TOOL. W razie potrzeby, jestem gotowy podjąć się również pierwszy raz integracji dronów fizycznych - kompatybilnych z tą wtyczką: w BLOX-TAK-SERVER-GCP.

### Lecz prawdziwa moc ekosystemu BLOX-TAK-SERVER-GCP jest realizowana we współpracy z pakietem oprogramowania BLOX-TAK-SERVER-IPPU-GCP (IPPU - Indywidualny Profil Połączeniowy Użytkownika).

Projekt IPPU integruje się bezpośrednio z tą podstawą GCP i zapewnia:

* **Automatyczny Onboarding z Formularzy Google:** Automatycznie przetwarza nowe zgłoszenia użytkowników z Formularza Google lub pliku CSV.
* **Grupowe Generowanie Certyfikatów:** Generuje i podpisuje certyfikaty klienta TAK .p12 dla dziesiątek użytkowników jednocześnie.
* **Automatyczne Pakowanie Konfiguracji:** Tworzy specyficzne dla użytkownika pakiety .zip zawierające ich certyfikat, preferencje ATAK (.pref) i inne niezbędne pliki.
* **Automatyczna Dystrybucja E-mail:** Bezpiecznie dostarcza pakiet użytkownika bezpośrednio na jego skrzynkę odbiorczą za pomocą API Gmaila.
* **Zaawansowana Konserwacja:** Skrypty do masowego unieważniania certyfikatów i zarządzania cyklem życia użytkownika.

Rozszerzenie IPPU przekształca godzinną konfigurację serwera w system, w którym dodanie nowego, w pełni przygotowanego użytkownika zajmuje mniej niż minutę zautomatyzowanej pracy.

</details>

---

## 🇺🇸 Maintenance & Teardown

```bash 
python3 cleanup_vm.py
```
Runs a script on the VM to remove all TAK-related components.

<br>

```bash 
python3 destroy_vm.py
```
IRREVERSIBLE. Uses Terraform to completely destroy the virtual machine and its associated workspace. Use with caution.

<details>

<summary>🇵🇱</summary>

## Konserwacja i Demontaż

```bash 
python3 cleanup_vm.py
```
Uruchamia na maszynie wirtualnej skrypt usuwający wszystkie komponenty związane z TAK.

<br>

```bash 
python3 destroy_vm.py
```

NIEODWRACALNE. Używa Terraform do całkowitego zniszczenia maszyny wirtualnej i jej powiązanego obszaru roboczego. Używaj z ostrożnością.

</details>

---

## 🇺🇸 License
This project is licensed under the MIT License. See the LICENSE file for details.

<details>

<summary>🇵🇱</summary>

## Licencja

Ten projekt jest objęty licencją MIT. Zobacz plik LICENSE, aby uzyskać szczegółowe informacje.

</details>

---

## 🇺🇸 Code of Conduct
This project and everyone participating in it is governed by the Contributor Covenant. See the CODE_OF_CONDUCT.md file for details.

<details>
<summary>🇵🇱</summary>

Kodeks Postępowania

Ten projekt i wszyscy w nim uczestniczący podlegają Zasadom Współtwórcy (Contributor Covenant). Zobacz plik CODE_OF_CONDUCT.md, aby uzyskać szczegółowe informacje.

</details>

---