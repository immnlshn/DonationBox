#!/bin/bash

################################################################################
# DonationBox Management Script
# Einfaches Management-Interface für die DonationBox
################################################################################

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE_NAME="donationbox"
LOG_DIR="/var/log/donationbox"
DATABASE_DIR="/var/lib/donationbox"
INSTALL_DIR="/opt/donationbox"

show_header() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                  DonationBox Management                           ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_status() {
    echo -e "${BLUE}═══ Service Status ═══${NC}"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l || echo -e "${RED}Service nicht gefunden${NC}"
    echo ""
}

show_menu() {
    echo -e "${GREEN}Was möchten Sie tun?${NC}"
    echo ""
    echo "  1) Service starten"
    echo "  2) Service stoppen"
    echo "  3) Service neustarten"
    echo "  4) Service-Status anzeigen"
    echo "  5) Logs anzeigen (live)"
    echo "  6) Logs anzeigen (letzte 100 Zeilen)"
    echo "  7) Fehler-Logs anzeigen"
    echo "  8) Datenbank-Backup erstellen"
    echo "  9) nginx neustarten"
    echo " 10) System-Informationen"
    echo "  0) Beenden"
    echo ""
    read -p "Auswahl: " -r choice
    echo ""
}

start_service() {
    echo -e "${BLUE}Starte Service...${NC}"
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ Service gestartet${NC}"
    else
        echo -e "${RED}✗ Service konnte nicht gestartet werden${NC}"
    fi
}

stop_service() {
    echo -e "${BLUE}Stoppe Service...${NC}"
    sudo systemctl stop "$SERVICE_NAME"
    sleep 1
    echo -e "${GREEN}✓ Service gestoppt${NC}"
}

restart_service() {
    echo -e "${BLUE}Starte Service neu...${NC}"
    sudo systemctl restart "$SERVICE_NAME"
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ Service neu gestartet${NC}"
    else
        echo -e "${RED}✗ Service konnte nicht gestartet werden${NC}"
    fi
}

show_logs_live() {
    echo -e "${BLUE}Zeige Live-Logs (Ctrl+C zum Beenden)...${NC}"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -f
}

show_logs_recent() {
    echo -e "${BLUE}Letzte 100 Log-Einträge:${NC}"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -n 100 --no-pager
}

show_error_logs() {
    echo -e "${RED}Fehler-Logs:${NC}"
    echo ""
    if [ -f "$LOG_DIR/backend.error.log" ]; then
        tail -n 50 "$LOG_DIR/backend.error.log"
    else
        echo "Keine Fehler-Logs gefunden"
    fi
}

backup_database() {
    echo -e "${BLUE}Erstelle Datenbank-Backup...${NC}"
    BACKUP_FILE="$DATABASE_DIR/database.backup.$(date +%Y%m%d_%H%M%S).db"
    if [ -f "$DATABASE_DIR/database.db" ]; then
        cp "$DATABASE_DIR/database.db" "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backup erstellt: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}✗ Datenbank nicht gefunden${NC}"
    fi
}

restart_nginx() {
    echo -e "${BLUE}Starte nginx neu...${NC}"
    sudo systemctl restart nginx
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✓ nginx neu gestartet${NC}"
    else
        echo -e "${RED}✗ nginx konnte nicht gestartet werden${NC}"
    fi
}

show_system_info() {
    echo -e "${CYAN}═══ System-Informationen ═══${NC}"
    echo ""
    echo -e "${BLUE}Hostname:${NC} $(hostname)"
    echo -e "${BLUE}IP-Adresse:${NC} $(hostname -I | awk '{print $1}')"
    echo -e "${BLUE}Betriebssystem:${NC} $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"

    if [ -f /proc/device-tree/model ]; then
        echo -e "${BLUE}Hardware:${NC} $(cat /proc/device-tree/model)"
    fi

    echo -e "${BLUE}Python-Version:${NC} $($INSTALL_DIR/venv/bin/python --version)"
    echo -e "${BLUE}Node.js-Version:${NC} $(node --version 2>/dev/null || echo 'nicht installiert')"
    echo ""
    echo -e "${BLUE}Speicher:${NC}"
    free -h
    echo ""
    echo -e "${BLUE}Festplatte:${NC}"
    df -h / | tail -n 1
    echo ""
    echo -e "${BLUE}Temperatur:${NC}"
    if command -v vcgencmd &> /dev/null; then
        vcgencmd measure_temp
    else
        echo "Nicht verfügbar (kein Raspberry Pi)"
    fi
}

# Hauptschleife
while true; do
    show_header
    show_status
    show_menu

    case $choice in
        1) start_service ;;
        2) stop_service ;;
        3) restart_service ;;
        4) show_status ;;
        5) show_logs_live ;;
        6) show_logs_recent ;;
        7) show_error_logs ;;
        8) backup_database ;;
        9) restart_nginx ;;
        10) show_system_info ;;
        0) echo -e "${GREEN}Auf Wiedersehen!${NC}"; exit 0 ;;
        *) echo -e "${RED}Ungültige Auswahl!${NC}" ;;
    esac

    echo ""
    read -p "Drücken Sie Enter um fortzufahren..."
done
