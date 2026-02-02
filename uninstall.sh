#!/bin/bash
set -e

#####################################
# DonationBox - Simple Uninstall
#####################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo -e "${RED}╔════════════════════════════════╗${NC}"
echo -e "${RED}║  DonationBox Deinstallation    ║${NC}"
echo -e "${RED}╚════════════════════════════════╝${NC}"
echo ""

# Confirm
read -p "Wirklich deinstallieren? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

# Stop and disable service
log "Service stoppen..."
sudo systemctl stop donationbox || true
sudo systemctl disable donationbox || true

# Remove service file
log "Service entfernen..."
sudo rm -f /etc/systemd/system/donationbox.service
sudo systemctl daemon-reload

# Remove nginx config
log "nginx-Konfiguration entfernen..."
sudo rm -f /etc/nginx/sites-enabled/donationbox
sudo rm -f /etc/nginx/sites-available/donationbox
sudo systemctl restart nginx || true

# Backup database
log "Datenbank sichern..."
if [ -d "/var/lib/donationbox" ]; then
    BACKUP="/var/lib/donationbox.backup.$(date +%s)"
    sudo mv /var/lib/donationbox "$BACKUP"
    warn "Datenbank gesichert nach: $BACKUP"
fi

# Remove installation
log "Installation entfernen..."
sudo rm -rf /opt/donationbox
sudo rm -rf /var/log/donationbox

echo ""
echo -e "${GREEN}✓ Deinstallation abgeschlossen!${NC}"
echo ""
