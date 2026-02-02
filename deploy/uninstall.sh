#!/usr/bin/env bash
set -euo pipefail

################################################################################
# DonationBox Uninstall Script
#
# This script removes the DonationBox application including:
# - Backend files
# - Frontend files
# - Systemd service
# - Nginx configuration
# - Application user
# - Optionally: data directory (database)
#
# System packages (Python, Nginx, etc.) are NOT removed
################################################################################

APP_NAME="donationbox"
APP_USER="donationbox"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
ENV_DIR="/etc/${APP_NAME}"
WWW_DIR="/var/www/${APP_NAME}"
BACKUP_DIR="/var/backups/${APP_NAME}"
NGINX_AVAIL="/etc/nginx/sites-available/${APP_NAME}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${APP_NAME}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[0;31m"

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

confirm_uninstall() {
    echo ""
    log_warn "═══════════════════════════════════════════════════════════"
    log_warn "WARNING: This will remove the DonationBox application!"
    log_warn "═══════════════════════════════════════════════════════════"
    echo ""
    echo "The following will be removed:"
    echo "  - Application files:   ${APP_DIR}"
    echo "  - Frontend files:      ${WWW_DIR}"
    echo "  - Configuration:       ${ENV_DIR}"
    echo "  - Systemd service:     ${SERVICE_FILE}"
    echo "  - Nginx configuration: ${NGINX_AVAIL}"
    echo "  - Application user:    ${APP_USER}"
    echo ""
    echo "The following will be kept (unless you choose to remove):"
    echo "  - Data directory:      ${DATA_DIR} (contains database)"
    echo "  - Backup directory:    ${BACKUP_DIR}"
    echo ""

    read -p "Do you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Uninstall cancelled"
        exit 0
    fi
}

ask_remove_data() {
    echo ""
    log_warn "Do you want to remove the data directory?"
    log_warn "This includes the database and all donation data!"
    echo ""
    read -p "Remove data directory ${DATA_DIR}? (yes/no): " -r
    echo
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        REMOVE_DATA=true
    else
        REMOVE_DATA=false
    fi
}

ask_remove_backups() {
    echo ""
    read -p "Remove backup directory ${BACKUP_DIR}? (yes/no): " -r
    echo
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        REMOVE_BACKUPS=true
    else
        REMOVE_BACKUPS=false
    fi
}

stop_and_disable_service() {
    log_info "Stopping and disabling service..."

    if systemctl is-active --quiet "${APP_NAME}" 2>/dev/null; then
        systemctl stop "${APP_NAME}"
        log_info "Service stopped"
    else
        log_info "Service was not running"
    fi

    if systemctl is-enabled --quiet "${APP_NAME}" 2>/dev/null; then
        systemctl disable "${APP_NAME}"
        log_info "Service disabled"
    fi
}

remove_systemd_service() {
    log_info "Removing systemd service..."

    if [[ -f "${SERVICE_FILE}" ]]; then
        rm -f "${SERVICE_FILE}"
        systemctl daemon-reload
        log_info "Service file removed"
    else
        log_info "Service file not found"
    fi
}

remove_nginx_config() {
    log_info "Removing nginx configuration..."

    # Remove symlink
    if [[ -L "${NGINX_ENABLED}" ]]; then
        rm -f "${NGINX_ENABLED}"
        log_info "Nginx site disabled"
    fi

    # Remove config file
    if [[ -f "${NGINX_AVAIL}" ]]; then
        rm -f "${NGINX_AVAIL}"
        log_info "Nginx config removed"
    fi

    # Test and reload nginx
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        log_info "Nginx reloaded"
    else
        log_warn "Nginx configuration test failed, skipping reload"
    fi
}

remove_application_files() {
    log_info "Removing application files..."

    if [[ -d "${APP_DIR}" ]]; then
        rm -rf "${APP_DIR}"
        log_info "Application directory removed: ${APP_DIR}"
    fi

    if [[ -d "${WWW_DIR}" ]]; then
        rm -rf "${WWW_DIR}"
        log_info "Frontend directory removed: ${WWW_DIR}"
    fi

    if [[ -d "${ENV_DIR}" ]]; then
        rm -rf "${ENV_DIR}"
        log_info "Configuration directory removed: ${ENV_DIR}"
    fi
}

remove_data_directory() {
    if [[ "${REMOVE_DATA}" == true ]]; then
        log_warn "Removing data directory..."

        if [[ -d "${DATA_DIR}" ]]; then
            rm -rf "${DATA_DIR}"
            log_warn "Data directory removed: ${DATA_DIR}"
        fi
    else
        log_info "Keeping data directory: ${DATA_DIR}"
    fi
}

remove_backup_directory() {
    if [[ "${REMOVE_BACKUPS}" == true ]]; then
        log_info "Removing backup directory..."

        if [[ -d "${BACKUP_DIR}" ]]; then
            rm -rf "${BACKUP_DIR}"
            log_info "Backup directory removed: ${BACKUP_DIR}"
        fi
    else
        log_info "Keeping backup directory: ${BACKUP_DIR}"
    fi
}

remove_user() {
    log_info "Removing application user..."

    if id -u "${APP_USER}" >/dev/null 2>&1; then
        userdel "${APP_USER}"
        log_info "User ${APP_USER} removed"
    else
        log_info "User ${APP_USER} not found"
    fi
}

print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    log_info "Uninstall completed!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Removed:"
    echo "  ✓ Application files"
    echo "  ✓ Frontend files"
    echo "  ✓ Configuration"
    echo "  ✓ Systemd service"
    echo "  ✓ Nginx configuration"
    echo "  ✓ Application user"

    if [[ "${REMOVE_DATA}" == true ]]; then
        echo "  ✓ Data directory"
    else
        echo ""
        log_warn "Data directory kept at: ${DATA_DIR}"
        log_warn "To remove manually: sudo rm -rf ${DATA_DIR}"
    fi

    if [[ "${REMOVE_BACKUPS}" == true ]]; then
        echo "  ✓ Backup directory"
    else
        echo ""
        log_info "Backup directory kept at: ${BACKUP_DIR}"
        log_info "To remove manually: sudo rm -rf ${BACKUP_DIR}"
    fi

    echo ""
    log_info "System packages (Python, Nginx, etc.) were not removed"
    echo ""
}

main() {
    log_info "Starting DonationBox uninstallation..."

    check_root
    confirm_uninstall
    ask_remove_data
    ask_remove_backups

    echo ""
    log_info "Proceeding with uninstall..."
    echo ""

    stop_and_disable_service
    remove_systemd_service
    remove_nginx_config
    remove_application_files
    remove_data_directory
    remove_backup_directory
    remove_user
    print_summary
}

main "$@"
