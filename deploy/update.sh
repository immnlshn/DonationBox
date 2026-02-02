#!/usr/bin/env bash
set -euo pipefail

################################################################################
# DonationBox Update Script
#
# This script updates the DonationBox application including:
# - Backend (FastAPI)
# - Frontend (React)
# - Python dependencies
# - Database migrations
################################################################################

APP_NAME="donationbox"
APP_USER="donationbox"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
ENV_DIR="/etc/${APP_NAME}"
WWW_DIR="/var/www/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
BACKUP_DIR="/var/backups/${APP_NAME}"

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[0;31m"
COLOR_BLUE="\033[0;34m"

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

log_step() {
    echo -e "${COLOR_BLUE}[STEP]${COLOR_RESET} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_frontend_build() {
    log_step "Checking frontend build..."

    if [[ ! -d "./frontend/dist" ]]; then
        log_error "Frontend build not found at ./frontend/dist"
        log_error "Please run 'npm run build' in the frontend directory first"
        exit 1
    fi

    log_info "Frontend build found"
}

create_backup() {
    log_step "Creating backup..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

    mkdir -p "${BACKUP_PATH}"

    # Backup backend
    if [[ -d "${APP_DIR}/backend" ]]; then
        log_info "Backing up backend..."
        cp -r "${APP_DIR}/backend" "${BACKUP_PATH}/"
    fi

    # Backup database
    if [[ -f "${DATA_DIR}/database.db" ]]; then
        log_info "Backing up database..."
        mkdir -p "${BACKUP_PATH}/data"
        cp "${DATA_DIR}/database.db" "${BACKUP_PATH}/data/"
    fi

    # Backup frontend
    if [[ -d "${WWW_DIR}" ]]; then
        log_info "Backing up frontend..."
        cp -r "${WWW_DIR}" "${BACKUP_PATH}/"
    fi

    # Backup environment config
    if [[ -f "${ENV_DIR}/.env" ]]; then
        log_info "Backing up configuration..."
        mkdir -p "${BACKUP_PATH}/config"
        cp "${ENV_DIR}/.env" "${BACKUP_PATH}/config/"
    fi

    log_info "Backup created at: ${BACKUP_PATH}"
    echo "${BACKUP_PATH}" > /tmp/donationbox_backup_path

    # Keep only last 5 backups
    log_info "Cleaning old backups (keeping last 5)..."
    cd "${BACKUP_DIR}"
    ls -t | tail -n +6 | xargs -r rm -rf
}

stop_service() {
    log_step "Stopping ${APP_NAME} service..."

    if systemctl is-active --quiet "${APP_NAME}"; then
        systemctl stop "${APP_NAME}"
        log_info "Service stopped"
    else
        log_warn "Service was not running"
    fi
}

update_backend() {
    log_step "Updating backend..."

    # Copy backend files
    log_info "Copying backend files..."
    rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='database.db' \
        ./backend/ "${APP_DIR}/backend/"

    # Update Python dependencies
    log_info "Updating Python dependencies..."
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

    log_info "Backend updated successfully"
}

update_frontend() {
    log_step "Updating frontend..."

    # Copy frontend build
    log_info "Copying frontend files..."
    rsync -a --delete ./frontend/dist/ "${WWW_DIR}/"

    log_info "Frontend updated successfully"
}

run_migrations() {
    log_step "Running database migrations..."

    cd "${APP_DIR}/backend"

    if "${VENV_DIR}/bin/alembic" upgrade head; then
        log_info "Migrations completed successfully"
    else
        log_error "Migration failed!"
        log_error "Attempting to rollback..."
        rollback_update
        exit 1
    fi

    cd - > /dev/null
}

set_permissions() {
    log_step "Setting permissions..."

    chown -R root:root "${APP_DIR}" "${WWW_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${DATA_DIR}"

    log_info "Permissions updated"
}

start_service() {
    log_step "Starting ${APP_NAME} service..."

    systemctl start "${APP_NAME}"

    # Wait a moment for service to start
    sleep 2

    if systemctl is-active --quiet "${APP_NAME}"; then
        log_info "✓ Service started successfully"
    else
        log_error "✗ Service failed to start"
        log_error "Check logs with: journalctl -u ${APP_NAME} -n 50"
        log_error "Attempting to rollback..."
        rollback_update
        exit 1
    fi
}

reload_nginx() {
    log_step "Reloading nginx..."

    # Test nginx configuration
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        log_info "Nginx reloaded successfully"
    else
        log_error "Nginx configuration test failed"
        exit 1
    fi
}

check_health() {
    log_step "Checking application health..."

    # Wait a bit for the app to fully start
    sleep 3

    # Check if service is running
    if systemctl is-active --quiet "${APP_NAME}"; then
        log_info "✓ Service is running"
    else
        log_error "✗ Service is not running"
        return 1
    fi

    # Try to reach the application
    if curl -s -f http://localhost:8000/api/hello >/dev/null 2>&1; then
        log_info "✓ Application is responding"
    else
        log_warn "⚠ Application is not responding to health check (this might be normal if route doesn't exist)"
    fi

    # Check recent logs for errors
    if journalctl -u "${APP_NAME}" --since "1 minute ago" | grep -i "error" >/dev/null 2>&1; then
        log_warn "⚠ Errors found in recent logs"
        log_warn "Check logs with: journalctl -u ${APP_NAME} -n 50"
    else
        log_info "✓ No errors in recent logs"
    fi
}

rollback_update() {
    log_error "Rolling back to previous version..."

    if [[ -f /tmp/donationbox_backup_path ]]; then
        BACKUP_PATH=$(cat /tmp/donationbox_backup_path)

        if [[ -d "${BACKUP_PATH}" ]]; then
            log_info "Restoring from backup: ${BACKUP_PATH}"

            # Stop service
            systemctl stop "${APP_NAME}" 2>/dev/null || true

            # Restore backend
            if [[ -d "${BACKUP_PATH}/backend" ]]; then
                rm -rf "${APP_DIR}/backend"
                cp -r "${BACKUP_PATH}/backend" "${APP_DIR}/"
            fi

            # Restore frontend
            if [[ -d "${BACKUP_PATH}/donationbox" ]]; then
                rm -rf "${WWW_DIR}"
                cp -r "${BACKUP_PATH}/donationbox" "${WWW_DIR}"
            fi

            # Restore database
            if [[ -f "${BACKUP_PATH}/data/database.db" ]]; then
                cp "${BACKUP_PATH}/data/database.db" "${DATA_DIR}/"
            fi

            # Restore config
            if [[ -f "${BACKUP_PATH}/config/.env" ]]; then
                cp "${BACKUP_PATH}/config/.env" "${ENV_DIR}/"
            fi

            # Set permissions
            chown -R root:root "${APP_DIR}" "${WWW_DIR}"
            chown -R "${APP_USER}:${APP_USER}" "${DATA_DIR}"

            # Start service
            systemctl start "${APP_NAME}"

            log_info "Rollback completed"
        else
            log_error "Backup not found at ${BACKUP_PATH}"
        fi

        rm -f /tmp/donationbox_backup_path
    else
        log_error "No backup information found"
    fi
}

print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    log_info "Update completed successfully!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Service status:"
    systemctl status "${APP_NAME}" --no-pager -l | head -n 10
    echo ""
    echo "Useful commands:"
    echo "  - View logs:     journalctl -u ${APP_NAME} -f"
    echo "  - Restart:       systemctl restart ${APP_NAME}"
    echo "  - Status:        systemctl status ${APP_NAME}"
    echo ""
    if [[ -f /tmp/donationbox_backup_path ]]; then
        BACKUP_PATH=$(cat /tmp/donationbox_backup_path)
        echo "Backup location: ${BACKUP_PATH}"
        echo "To rollback: sudo ${BACKUP_PATH}/rollback.sh (not implemented)"
        echo ""
        rm -f /tmp/donationbox_backup_path
    fi
}

main() {
    log_info "Starting DonationBox update..."
    echo ""

    check_root
    check_frontend_build
    create_backup
    stop_service
    update_backend
    update_frontend
    run_migrations
    set_permissions
    start_service
    reload_nginx
    check_health
    print_summary
}

# Trap errors and attempt rollback
trap 'log_error "Update failed! Check the logs above."; exit 1' ERR

main "$@"
