#!/bin/bash

################################################################################
# DonationBox Deinstallations-Script
# Entfernt die DonationBox-Installation komplett vom System
################################################################################

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${RED}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                 DonationBox Deinstallation                        ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Variablen
PROJECT_NAME="donationbox"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="donationbox"
DATABASE_DIR="/var/lib/$PROJECT_NAME"
LOG_DIR="/var/log/$PROJECT_NAME"
NGINX_CONFIG="/etc/nginx/sites-available/$PROJECT_NAME"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Bestätigung
read -p "Möchten Sie DonationBox wirklich deinstallieren? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Deinstallation abgebrochen."
    exit 0
fi

log_info "Starte Deinstallation..."

# Service stoppen und deaktivieren
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_info "Stoppe Service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    log_info "Deaktiviere Service..."
    sudo systemctl disable "$SERVICE_NAME"
fi

# Service-Datei entfernen
if [ -f "$SERVICE_FILE" ]; then
    log_info "Entferne systemd Service..."
    sudo rm "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

# nginx-Konfiguration entfernen
if [ -f "$NGINX_CONFIG" ]; then
    log_info "Entferne nginx-Konfiguration..."
    sudo rm -f /etc/nginx/sites-enabled/"$PROJECT_NAME"
    sudo rm -f "$NGINX_CONFIG"
    sudo systemctl reload nginx
fi

# Installationsverzeichnis entfernen
if [ -d "$INSTALL_DIR" ]; then
    log_info "Entferne Installationsverzeichnis..."
    sudo rm -rf "$INSTALL_DIR"
fi

# Optional: Datenbank und Logs entfernen
read -p "Datenbank und Logs auch entfernen? (yes/no): " -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if [ -d "$DATABASE_DIR" ]; then
        log_info "Entferne Datenbank..."
        sudo rm -rf "$DATABASE_DIR"
    fi
    if [ -d "$LOG_DIR" ]; then
        log_info "Entferne Logs..."
        sudo rm -rf "$LOG_DIR"
    fi
fi

log_success "Deinstallation abgeschlossen!"
