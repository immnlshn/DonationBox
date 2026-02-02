#!/usr/bin/env bash
set -euo pipefail

################################################################################
# DonationBox Quick Update Script
#
# Fast update without backup - use for quick deployments
# For production updates, use update.sh instead
################################################################################

APP_NAME="donationbox"
APP_DIR="/opt/${APP_NAME}"
WWW_DIR="/var/www/${APP_NAME}"

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_RED="\033[0;31m"

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if frontend build exists
if [[ ! -d "./frontend/dist" ]]; then
    log_error "Frontend build not found. Run 'npm run build' first."
    exit 1
fi

log_info "Stopping service..."
systemctl stop "${APP_NAME}"

log_info "Updating backend..."
rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='database.db' \
    ./backend/ "${APP_DIR}/backend/"

log_info "Updating frontend..."
rsync -a --delete ./frontend/dist/ "${WWW_DIR}/"

log_info "Starting service..."
systemctl start "${APP_NAME}"

log_info "Testing nginx..."
nginx -t

log_info "Reloading nginx..."
systemctl reload nginx

log_info "✓ Quick update completed!"
log_info "Check status: systemctl status ${APP_NAME}"
log_info "View logs: journalctl -u ${APP_NAME} -f"
