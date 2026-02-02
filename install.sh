#!/bin/bash

################################################################################
# DonationBox Installation Script
# Installiert alle notwendigen Pakete, richtet Services ein und deployt die App
################################################################################

set -e  # Exit on error

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging-Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                    DonationBox Installation                       ║
║                                                                   ║
║  Installiert Backend, Frontend und systemd Service                ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Überprüfung ob als root ausgeführt
if [ "$EUID" -eq 0 ]; then
    log_error "Bitte führen Sie das Skript NICHT als root aus!"
    log_info "Verwenden Sie: ./install.sh"
    log_info "Sudo wird nur bei Bedarf verwendet."
    exit 1
fi

# Variablen
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_NAME="donationbox"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="donationbox"
SERVICE_USER="$USER"
VENV_DIR="$INSTALL_DIR/venv"
FRONTEND_BUILD_DIR="$INSTALL_DIR/frontend"
DATABASE_DIR="/var/lib/$PROJECT_NAME"
LOG_DIR="/var/log/$PROJECT_NAME"

log_info "Installation startet..."
log_info "Projekt-Verzeichnis: $SCRIPT_DIR"
log_info "Installations-Verzeichnis: $INSTALL_DIR"
log_info "Service-User: $SERVICE_USER"

# Debian-Version erkennen
DEBIAN_VERSION=$(cat /etc/os-release | grep VERSION_CODENAME | cut -d= -f2)
log_info "Erkannte Debian-Version: $DEBIAN_VERSION"

################################################################################
# 1. System-Pakete installieren
################################################################################

log_info "Schritt 1: System-Pakete installieren (Debian Trixie)..."

log_info "System wird aktualisiert..."
sudo apt-get update

log_info "Installiere Python3, pip und venv..."
sudo apt-get install -y python3 python3-pip python3-venv python3-dev

log_info "Installiere Raspberry Pi GPIO-Pakete..."
# Für Raspberry Pi GPIO-Support unter Debian
sudo apt-get install -y python3-lgpio python3-rpi.lgpio || log_warning "GPIO-Pakete nicht verfügbar (evtl. kein Raspberry Pi)"

log_info "Installiere Node.js und npm..."
if ! command -v node &> /dev/null; then
    # Für Debian Trixie: Node.js aus dem offiziellen Repository
    log_info "Füge NodeSource Repository hinzu..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    log_success "Node.js $(node --version) installiert!"
else
    NODE_VERSION=$(node --version)
    log_success "Node.js ist bereits installiert: $NODE_VERSION"
fi

log_info "Installiere nginx für Frontend-Hosting..."
sudo apt-get install -y nginx

log_info "Installiere zusätzliche Abhängigkeiten..."
sudo apt-get install -y git curl build-essential wget ca-certificates gnupg

# Raspberry Pi spezifische Pakete
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    log_info "Raspberry Pi erkannt, installiere zusätzliche Pakete..."
    sudo apt-get install -y raspi-config rpi-update libraspberrypi-bin || log_warning "Einige RPi-Pakete nicht verfügbar"
fi

log_success "System-Pakete installiert!"

################################################################################
# 2. Installationsverzeichnis vorbereiten
################################################################################

log_info "Schritt 2: Installationsverzeichnis vorbereiten..."

# Installationsverzeichnis erstellen
if [ -d "$INSTALL_DIR" ]; then
    log_warning "Installationsverzeichnis existiert bereits. Erstelle Backup..."
    sudo mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Datenbank- und Log-Verzeichnisse erstellen
sudo mkdir -p "$DATABASE_DIR"
sudo chown "$SERVICE_USER:$SERVICE_USER" "$DATABASE_DIR"

sudo mkdir -p "$LOG_DIR"
sudo chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"

log_success "Verzeichnisse erstellt!"

################################################################################
# 3. Backend installieren
################################################################################

log_info "Schritt 3: Backend installieren..."

# Backend-Dateien kopieren
log_info "Kopiere Backend-Dateien..."
cp -r "$BACKEND_DIR" "$INSTALL_DIR/"

# Python Virtual Environment erstellen
log_info "Erstelle Python Virtual Environment..."
python3 -m venv "$VENV_DIR"

# Abhängigkeiten installieren
log_info "Installiere Python-Abhängigkeiten..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"

# .env Datei erstellen (falls nicht vorhanden)
ENV_FILE="$INSTALL_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_info "Erstelle .env Datei..."
    cat > "$ENV_FILE" << EOF
# DonationBox Configuration
APP_NAME=DonationBox API
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///$DATABASE_DIR/database.db

# CORS (adjust for your domain)
ALLOWED_ORIGINS=["http://localhost", "http://localhost:80", "http://$(hostname -I | awk '{print $1}')"]

# GPIO Settings (für Raspberry Pi)
ENABLE_GPIO=true
PIN_FACTORY=native

# Security
SECRET_KEY=$(openssl rand -hex 32)
EOF
    log_success ".env Datei erstellt!"
else
    log_warning ".env Datei existiert bereits, wird nicht überschrieben."
fi

# Datenbank initialisieren
log_info "Initialisiere Datenbank..."
cd "$INSTALL_DIR/backend"
"$VENV_DIR/bin/alembic" upgrade head || {
    log_warning "Alembic Migration fehlgeschlagen. Erstelle neue Datenbank..."
    "$VENV_DIR/bin/python" -c "from backend.core.database import create_tables; import asyncio; asyncio.run(create_tables())"
}

log_success "Backend installiert!"

################################################################################
# 4. Frontend bauen und installieren
################################################################################

log_info "Schritt 4: Frontend bauen und installieren..."

cd "$FRONTEND_DIR"

# npm Abhängigkeiten installieren
log_info "Installiere npm-Abhängigkeiten..."
npm install

# Production Build erstellen
log_info "Erstelle Production Build..."
npm run build

# Build zum Installationsverzeichnis kopieren
log_info "Kopiere Frontend-Build..."
sudo mkdir -p "$FRONTEND_BUILD_DIR"
sudo cp -r "$FRONTEND_DIR/dist/"* "$FRONTEND_BUILD_DIR/"
sudo chown -R www-data:www-data "$FRONTEND_BUILD_DIR"

log_success "Frontend gebaut und installiert!"

################################################################################
# 5. nginx konfigurieren
################################################################################

log_info "Schritt 5: nginx konfigurieren..."

# nginx Konfiguration erstellen
NGINX_CONFIG="/etc/nginx/sites-available/$PROJECT_NAME"
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/donationbox/frontend;
        try_files $uri $uri/ /index.html;

        # Cache-Control für statische Assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Logging
    access_log /var/log/nginx/donationbox_access.log;
    error_log /var/log/nginx/donationbox_error.log;
}
EOF

# nginx-Konfiguration aktivieren
sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/

# Standard-Site deaktivieren (optional)
sudo rm -f /etc/nginx/sites-enabled/default

# nginx Konfiguration testen
log_info "Teste nginx-Konfiguration..."
sudo nginx -t

# nginx neustarten
log_info "Starte nginx neu..."
sudo systemctl restart nginx
sudo systemctl enable nginx

log_success "nginx konfiguriert!"

################################################################################
# 6. systemd Service erstellen
################################################################################

log_info "Schritt 6: systemd Service erstellen..."

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=DonationBox Backend Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 1

# Restart-Konfiguration
Restart=always
RestartSec=10

# Logging
StandardOutput=append:$LOG_DIR/backend.log
StandardError=append:$LOG_DIR/backend.error.log

# Sicherheit
NoNewPrivileges=true
PrivateTmp=true

# Limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# systemd neu laden
log_info "Lade systemd-Konfiguration neu..."
sudo systemctl daemon-reload

# Service aktivieren
log_info "Aktiviere Service..."
sudo systemctl enable "$SERVICE_NAME"

# Service starten
log_info "Starte Service..."
sudo systemctl start "$SERVICE_NAME"

# Kurz warten und Status prüfen
sleep 2
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Service läuft!"
else
    log_error "Service konnte nicht gestartet werden!"
    log_info "Prüfen Sie die Logs mit: sudo journalctl -u $SERVICE_NAME -n 50"
fi

log_success "systemd Service erstellt!"

################################################################################
# 7. Berechtigungen setzen
################################################################################

log_info "Schritt 7: Berechtigungen setzen..."

sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
sudo chmod -R 755 "$INSTALL_DIR"
sudo chmod 600 "$INSTALL_DIR/backend/.env"

# GPIO-Berechtigungen (für Raspberry Pi unter Debian)
if [ -e /dev/gpiomem ]; then
    log_info "GPIO erkannt, setze Berechtigungen..."

    # Benutzer zu gpio-Gruppe hinzufügen (falls vorhanden)
    if getent group gpio > /dev/null 2>&1; then
        sudo usermod -a -G gpio "$SERVICE_USER"
        log_success "Benutzer zu gpio-Gruppe hinzugefügt"
    else
        log_warning "gpio-Gruppe existiert nicht, erstelle sie..."
        sudo groupadd -f gpio
        sudo usermod -a -G gpio "$SERVICE_USER"
        # Setze Berechtigungen für /dev/gpiomem
        echo 'SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\''chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio; chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio; chown -R root:gpio /sys$devpath && chmod -R 770 /sys$devpath'\''"' | sudo tee /etc/udev/rules.d/99-gpio.rules > /dev/null
        echo 'SUBSYSTEM=="bcm2835-gpiomem", KERNEL=="gpiomem", GROUP="gpio", MODE="0660"' | sudo tee -a /etc/udev/rules.d/99-gpio.rules > /dev/null
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        log_success "GPIO-Berechtigungen konfiguriert"
    fi

    # Benutzer zu i2c und spi Gruppen hinzufügen (oft benötigt)
    for group in i2c spi dialout; do
        if getent group $group > /dev/null 2>&1; then
            sudo usermod -a -G $group "$SERVICE_USER"
            log_info "Benutzer zu $group-Gruppe hinzugefügt"
        fi
    done

    log_warning "WICHTIG: Der Benutzer $SERVICE_USER muss sich ab- und wieder anmelden, damit GPIO-Berechtigungen wirksam werden!"
fi

log_success "Berechtigungen gesetzt!"

################################################################################
# 8. Firewall konfigurieren (optional)
################################################################################

log_info "Schritt 8: Firewall konfigurieren (optional)..."

if command -v ufw &> /dev/null; then
    log_info "ufw erkannt, konfiguriere Firewall..."
    sudo ufw allow 80/tcp comment 'DonationBox HTTP'
    sudo ufw allow 8000/tcp comment 'DonationBox Backend (optional)'
    log_success "Firewall-Regeln hinzugefügt!"
else
    log_info "ufw nicht installiert, überspringe Firewall-Konfiguration"
fi

################################################################################
# Abschluss
################################################################################

echo ""
log_success "═════════════════════════════════════════════════════════════"
log_success "          Installation erfolgreich abgeschlossen!            "
log_success "═════════════════════════════════════════════════════════════"
echo ""

# IP-Adresse ermitteln
IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}DonationBox ist jetzt verfügbar unter:${NC}"
echo -e "  Frontend:  ${BLUE}http://$IP_ADDR${NC} oder ${BLUE}http://localhost${NC}"
echo -e "  Backend:   ${BLUE}http://$IP_ADDR:8000${NC}"
echo -e "  API Docs:  ${BLUE}http://$IP_ADDR:8000/docs${NC}"
echo ""

echo -e "${GREEN}Wichtige Befehle:${NC}"
echo -e "  Service starten:     ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "  Service stoppen:     ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Service neustarten:  ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Service-Status:      ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  Logs ansehen:        ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Backend-Logs:        ${YELLOW}tail -f $LOG_DIR/backend.log${NC}"
echo -e "  nginx neustarten:    ${YELLOW}sudo systemctl restart nginx${NC}"
echo ""

echo -e "${GREEN}Konfigurationsdateien:${NC}"
echo -e "  Backend:         ${YELLOW}$INSTALL_DIR/backend/.env${NC}"
echo -e "  nginx:           ${YELLOW}/etc/nginx/sites-available/$PROJECT_NAME${NC}"
echo -e "  systemd Service: ${YELLOW}/etc/systemd/system/$SERVICE_NAME.service${NC}"
echo -e "  Datenbank:       ${YELLOW}$DATABASE_DIR/database.db${NC}"
echo ""

echo -e "${GREEN}Nächste Schritte:${NC}"
echo -e "  1. Öffnen Sie http://$IP_ADDR in Ihrem Browser"
echo -e "  2. Passen Sie die Konfiguration in $INSTALL_DIR/backend/.env an"
echo -e "  3. Erstellen Sie eine Voting-Kampagne über die API"
echo ""

log_info "Installation abgeschlossen!"
