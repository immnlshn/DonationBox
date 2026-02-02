#!/bin/bash
set -e

#####################################
# DonationBox - Simple Install
#####################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# Check root
[ "$EUID" -eq 0 ] && error "Nicht als root ausführen! Verwende: ./install.sh"

# Vars
INSTALL_DIR="/opt/donationbox"
SERVICE_USER="$USER"
DB_DIR="/var/lib/donationbox"
LOG_DIR="/var/log/donationbox"

echo -e "${GREEN}╔════════════════════════════════╗${NC}"
echo -e "${GREEN}║   DonationBox Installation     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════╝${NC}"


#####################################
# 1. System-Pakete installieren
#####################################

log "System-Pakete installieren..."

# Alte NodeSource-Repos entfernen falls vorhanden
sudo rm -f /etc/apt/sources.list.d/nodesource.list
sudo rm -f /etc/apt/keyrings/nodesource.gpg

# Konfligierende Pakete entfernen
sudo apt-get remove -y nodejs npm nodejs-legacy 2>/dev/null || true
sudo apt-get autoremove -y

# System aktualisieren
sudo apt-get update

# Python und basics installieren
log "Installiere Python, nginx, sqlite..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-lgpio \
    nginx \
    sqlite3 \
    curl

# Node.js via nodesource
log "Installiere Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs


#####################################
# 2. Verzeichnisse vorbereiten
#####################################

log "Verzeichnisse erstellen..."

# Backup falls vorhanden
if [ -d "$INSTALL_DIR" ]; then
    warn "Erstelle Backup..."
    sudo mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%s)"
fi

sudo mkdir -p "$INSTALL_DIR"/{backend,frontend}
sudo mkdir -p "$DB_DIR"
sudo mkdir -p "$LOG_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$DB_DIR" "$LOG_DIR"


#####################################
# 3. Backend installieren
#####################################

log "Backend installieren..."

# Dateien kopieren
cp -r backend/* "$INSTALL_DIR/backend/"

# Virtual Environment
log "Python venv erstellen..."
python3 -m venv "$INSTALL_DIR/venv"

# Dependencies
log "Python-Pakete installieren..."
"$INSTALL_DIR/venv/bin/pip" install -q --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/backend/requirements.txt"

# .env erstellen
log "Konfiguration erstellen..."
if [ ! -f "$INSTALL_DIR/backend/.env" ]; then
    cat > "$INSTALL_DIR/backend/.env" << EOF
APP_NAME=DonationBox API
ENV=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
DATABASE_URL=sqlite:///$DB_DIR/database.db
ALLOWED_ORIGINS=["*"]
ENABLE_GPIO=true
SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

# Datenbank initialisieren
log "Datenbank initialisieren..."
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" -c "
import asyncio
from backend.core.database import setup_database
from backend.models.base import Base

async def init_db():
    engine, _ = setup_database()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(init_db())
print('✓ Datenbank erstellt')
" || warn "Datenbank-Initialisierung übersprungen (möglicherweise schon vorhanden)"


#####################################
# 4. Frontend bauen
#####################################

log "Frontend bauen..."
cd "$(dirname "$0")/frontend"
npm install --silent
npm run build

# Build kopieren
log "Frontend deployen..."
sudo cp -r dist/* "$INSTALL_DIR/frontend/"
sudo chown -R www-data:www-data "$INSTALL_DIR/frontend"


#####################################
# 5. nginx konfigurieren
#####################################

log "nginx konfigurieren..."

sudo tee /etc/nginx/sites-available/donationbox > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/donationbox/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/donationbox /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx



#####################################
# 6. systemd Service
#####################################

log "Service erstellen..."

sudo tee /etc/systemd/system/donationbox.service > /dev/null << EOF
[Unit]
Description=DonationBox Backend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --log-level info
Restart=always
RestartSec=3

# Logging
StandardOutput=append:$LOG_DIR/backend.log
StandardError=append:$LOG_DIR/backend.error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable donationbox
sudo systemctl start donationbox

# Status prüfen
sleep 2
if sudo systemctl is-active --quiet donationbox; then
    log "Service läuft!"
else
    error "Service konnte nicht gestartet werden! Logs: sudo journalctl -u donationbox -n 50"
fi


#####################################
# 7. Berechtigungen
#####################################

log "Berechtigungen setzen..."

sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
sudo chmod 600 "$INSTALL_DIR/backend/.env"

# GPIO-Gruppen
for group in gpio i2c spi dialout; do
    if getent group $group > /dev/null 2>&1; then
        sudo usermod -a -G $group "$SERVICE_USER"
    fi
done

#####################################
# Fertig!
#####################################

IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation erfolgreich!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Frontend:  ${YELLOW}http://$IP${NC}"
echo -e "Backend:   ${YELLOW}http://$IP:8000${NC}"
echo -e "API Docs:  ${YELLOW}http://$IP:8000/docs${NC}"
echo ""
echo -e "${GREEN}Befehle:${NC}"
echo -e "  Status:      ${YELLOW}sudo systemctl status donationbox${NC}"
echo -e "  Neustarten:  ${YELLOW}sudo systemctl restart donationbox${NC}"
echo -e "  Logs:        ${YELLOW}sudo journalctl -u donationbox -f${NC}"
echo -e "  Deinstall:   ${YELLOW}./uninstall.sh${NC}"
echo ""

