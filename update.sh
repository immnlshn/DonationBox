#!/bin/bash

################################################################################
# DonationBox Update Script
# Aktualisiert Backend und/oder Frontend ohne Neuinstallation
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

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                    DonationBox Update                             ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Variablen
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_NAME="donationbox"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="donationbox"
VENV_DIR="$INSTALL_DIR/venv"
FRONTEND_BUILD_DIR="$INSTALL_DIR/frontend"

# Überprüfen ob installiert
if [ ! -d "$INSTALL_DIR" ]; then
    log_error "DonationBox ist nicht installiert!"
    log_info "Führen Sie zuerst ./install.sh aus"
    exit 1
fi

# Was soll aktualisiert werden?
echo "Was möchten Sie aktualisieren?"
echo "1) Backend"
echo "2) Frontend"
echo "3) Beides"
read -p "Auswahl (1-3): " -r CHOICE

UPDATE_BACKEND=false
UPDATE_FRONTEND=false

case $CHOICE in
    1) UPDATE_BACKEND=true ;;
    2) UPDATE_FRONTEND=true ;;
    3) UPDATE_BACKEND=true; UPDATE_FRONTEND=true ;;
    *) log_error "Ungültige Auswahl!"; exit 1 ;;
esac

################################################################################
# Backend aktualisieren
################################################################################

if [ "$UPDATE_BACKEND" = true ]; then
    log_info "Aktualisiere Backend..."

    # Service stoppen
    log_info "Stoppe Service..."
    sudo systemctl stop "$SERVICE_NAME"

    # Backup erstellen
    log_info "Erstelle Backup..."
    sudo cp -r "$INSTALL_DIR/backend" "$INSTALL_DIR/backend.backup.$(date +%Y%m%d_%H%M%S)"

    # Neue Dateien kopieren (außer .env)
    log_info "Kopiere neue Backend-Dateien..."
    rsync -av --exclude='.env' --exclude='*.pyc' --exclude='__pycache__' \
          "$BACKEND_DIR/" "$INSTALL_DIR/backend/"

    # Dependencies aktualisieren
    log_info "Aktualisiere Python-Dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade -r "$INSTALL_DIR/backend/requirements.txt"

    # Migrationen ausführen
    log_info "Führe Datenbank-Migrationen aus..."
    cd "$INSTALL_DIR/backend"
    "$VENV_DIR/bin/alembic" upgrade head || log_warning "Migration fehlgeschlagen"

    # Service starten
    log_info "Starte Service..."
    sudo systemctl start "$SERVICE_NAME"

    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Backend aktualisiert und gestartet!"
    else
        log_error "Service konnte nicht gestartet werden!"
        log_info "Prüfen Sie die Logs mit: sudo journalctl -u $SERVICE_NAME -n 50"
    fi
fi

################################################################################
# Frontend aktualisieren
################################################################################

if [ "$UPDATE_FRONTEND" = true ]; then
    log_info "Aktualisiere Frontend..."

    cd "$FRONTEND_DIR"

    # Backup erstellen
    log_info "Erstelle Backup..."
    sudo cp -r "$FRONTEND_BUILD_DIR" "$FRONTEND_BUILD_DIR.backup.$(date +%Y%m%d_%H%M%S)"

    # Dependencies aktualisieren
    log_info "Aktualisiere npm-Dependencies..."
    npm install

    # Build erstellen
    log_info "Erstelle neuen Build..."
    npm run build

    # Build deployen
    log_info "Deploye neuen Build..."
    sudo rm -rf "$FRONTEND_BUILD_DIR"/*
    sudo cp -r "$FRONTEND_DIR/dist/"* "$FRONTEND_BUILD_DIR/"
    sudo chown -R www-data:www-data "$FRONTEND_BUILD_DIR"

    # nginx neu laden
    log_info "Lade nginx neu..."
    sudo systemctl reload nginx

    log_success "Frontend aktualisiert!"
fi

log_success "Update abgeschlossen!"

# Status anzeigen
echo ""
log_info "Service-Status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l || true
