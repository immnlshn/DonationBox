#!/usr/bin/env bash
set -euo pipefail

################################################################################
# Fix Permissions Script
#
# Run this if you get "unable to open database file" errors
################################################################################

APP_NAME="donationbox"
APP_USER="donationbox"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
ENV_DIR="/etc/${APP_NAME}"
WWW_DIR="/var/www/${APP_NAME}"

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[1;33m"
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

log_info "Fixing permissions for DonationBox..."

# Application files owned by root
log_info "Setting application directory permissions..."
chown -R root:root "${APP_DIR}" "${WWW_DIR}"

# Data directory owned by app user (must be writable for database)
log_info "Setting data directory permissions..."
chown -R "${APP_USER}:${APP_USER}" "${DATA_DIR}"
chmod 750 "${DATA_DIR}"

# Environment directory and .env file readable by app user
log_info "Setting environment directory permissions..."
chown root:"${APP_USER}" "${ENV_DIR}"
chmod 750 "${ENV_DIR}"

if [[ -f "${ENV_DIR}/.env" ]]; then
    chown root:"${APP_USER}" "${ENV_DIR}/.env"
    chmod 640 "${ENV_DIR}/.env"
    log_info "✓ .env file is now readable by ${APP_USER}"
else
    log_error "✗ .env file not found at ${ENV_DIR}/.env"
    exit 1
fi

# Test if donationbox user can read .env
log_info "Testing .env access..."
if sudo -u "${APP_USER}" cat "${ENV_DIR}/.env" > /dev/null 2>&1; then
    log_info "✓ ${APP_USER} can read .env file"
else
    log_error "✗ ${APP_USER} cannot read .env file"
    exit 1
fi

# Test if donationbox user can write to data directory
log_info "Testing data directory access..."
if sudo -u "${APP_USER}" touch "${DATA_DIR}/test.tmp" 2>/dev/null; then
    rm "${DATA_DIR}/test.tmp"
    log_info "✓ ${APP_USER} can write to data directory"
else
    log_error "✗ ${APP_USER} cannot write to data directory"
    exit 1
fi

log_info "✓ All permissions fixed!"
log_info ""
log_info "Restarting service..."
systemctl restart "${APP_NAME}"

sleep 2

if systemctl is-active --quiet "${APP_NAME}"; then
    log_info "✓ Service is running"
    log_info ""
    log_info "Check logs with: journalctl -u ${APP_NAME} -f"
else
    log_error "✗ Service failed to start"
    log_error "Check logs with: journalctl -u ${APP_NAME} -n 50"
    exit 1
fi
