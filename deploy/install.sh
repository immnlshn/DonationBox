#!/usr/bin/env bash
set -euo pipefail
################################################################################
# DonationBox Installation Script
# 
# This script installs the DonationBox application including:
# - Backend (FastAPI)
# - Frontend (React)
# - Nginx configuration
# - Systemd service
################################################################################
APP_NAME="donationbox"
APP_USER="donationbox"
APP_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
ENV_DIR="/etc/${APP_NAME}"
WWW_DIR="/var/www/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
NGINX_AVAIL="/etc/nginx/sites-available/${APP_NAME}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${APP_NAME}"
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
install_system_packages() {
    log_info "Installing system packages..."
    # Update package list
    # Install core packages (always required)
    log_info "Installing core packages..."
    apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
        python3-dev \
        build-essential \
        nginx \
        rsync \
        curl \
        git \
        swig \
        gpiod \
        liblgpio1 \
        liblgpio-dev \
        python3-lgpio \
        sqlite3 \
        libsqlite3-dev

    # Install Node.js and npm (optional, skip if already installed or conflicts exist)
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
        NPM_VERSION=$(npm --version 2>/dev/null || echo "unknown")
        log_info "✓ Node.js ${NODE_VERSION} and npm ${NPM_VERSION} are already installed"
        log_info "  Skipping nodejs/npm installation"
    else
        log_info "Attempting to install Node.js and npm..."
        if apt-get install -y nodejs npm 2>/dev/null; then
            log_info "✓ Node.js and npm installed successfully"
        else
            log_warn "⚠ Could not install nodejs/npm (package conflict or not available)"
            log_warn "  If you need to build the frontend on this server, install Node.js manually:"
            log_warn "  https://nodejs.org/ or https://github.com/nodesource/distributions"
            log_warn "  You can also build the frontend on another machine and copy dist/"
        fi
    fi

    log_info "System packages installed successfully"
}
create_user() {
    log_info "Creating application user..."
    if id -u "${APP_USER}" >/dev/null 2>&1; then
        log_warn "User ${APP_USER} already exists, skipping creation"
    else
        useradd -r -s /usr/sbin/nologin "${APP_USER}"
        log_info "User ${APP_USER} created"
    fi

    # Add user to gpio group if it exists (for GPIO access on Raspberry Pi)
    if getent group gpio > /dev/null 2>&1; then
        usermod -a -G gpio "${APP_USER}"
        log_info "User ${APP_USER} added to gpio group"
    fi

    # Add user to dialout group (for serial device access if needed)
    if getent group dialout > /dev/null 2>&1; then
        usermod -a -G dialout "${APP_USER}"
        log_info "User ${APP_USER} added to dialout group"
    fi
}
create_directories() {
    log_info "Creating application directories..."
    mkdir -p "${APP_DIR}/backend"
    mkdir -p "${DATA_DIR}"
    mkdir -p "${ENV_DIR}"
    mkdir -p "${WWW_DIR}"
    # Note: VENV_DIR will be created by python3 -m venv in install_backend()
    log_info "Directories created"
}
install_backend() {
    log_info "Installing backend..."
    # Copy backend files
    rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='database.db' \
        ./backend/ "${APP_DIR}/backend/"

    # Create virtual environment with access to system packages (for python3-lgpio)
    if [[ ! -f "${VENV_DIR}/bin/pip" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv --system-site-packages "${VENV_DIR}"
    else
        log_info "Python virtual environment already exists"
    fi

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

    log_info "Backend installed successfully"
}

validate_and_run_migrations() {
    log_info "Validating and running database migrations..."

    cd "${APP_DIR}/backend"

    # Check if alembic is installed
    if ! "${VENV_DIR}/bin/alembic" --version >/dev/null 2>&1; then
        log_error "Alembic is not installed!"
        cd - > /dev/null
        exit 1
    fi

    # Check if alembic.ini exists
    if [[ ! -f "alembic.ini" ]]; then
        log_error "alembic.ini not found in backend directory!"
        cd - > /dev/null
        exit 1
    fi

    # Check current migration status
    log_info "Checking current migration status..."
    if sudo -u "${APP_USER}" bash -c "set -a; source '${ENV_DIR}/.env'; set +a; '${VENV_DIR}/bin/alembic' current" >/dev/null 2>&1; then
        CURRENT_REV=$(sudo -u "${APP_USER}" bash -c "set -a; source '${ENV_DIR}/.env'; set +a; '${VENV_DIR}/bin/alembic' current" 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -n 1 || echo "none")
        log_info "Current revision: ${CURRENT_REV:-none}"
    else
        log_warn "Could not determine current migration state"
    fi

    # Get target revision (head)
    HEAD_REV=$(sudo -u "${APP_USER}" bash -c "set -a; source '${ENV_DIR}/.env'; set +a; '${VENV_DIR}/bin/alembic' heads" 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -n 1 || echo "unknown")
    log_info "Target revision: ${HEAD_REV:-unknown}"

    # Run migrations as app user with environment variables loaded
    log_info "Running database migrations to head..."
    # Load environment variables from .env file and pass them to alembic
    if sudo -u "${APP_USER}" bash -c "set -a; source '${ENV_DIR}/.env'; set +a; '${VENV_DIR}/bin/alembic' upgrade head" 2>&1 | tee /tmp/alembic_upgrade.log; then
        log_info "✓ Migrations completed successfully"
    else
        log_error "✗ Migration failed!"
        log_error "Check log: /tmp/alembic_upgrade.log"
        cat /tmp/alembic_upgrade.log
        cd - > /dev/null
        exit 1
    fi

    # Verify final state
    log_info "Verifying migration state..."
    FINAL_REV=$(sudo -u "${APP_USER}" bash -c "set -a; source '${ENV_DIR}/.env'; set +a; '${VENV_DIR}/bin/alembic' current" 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -n 1 || echo "none")

    if [[ -n "$FINAL_REV" ]] && [[ "$FINAL_REV" != "none" ]]; then
        log_info "✓ Database is at revision: ${FINAL_REV}"
    else
        log_warn "⚠ Could not verify final migration state"
    fi

    # Check if database file exists and is readable
    if [[ -f "${DATA_DIR}/database.db" ]]; then
        log_info "✓ Database file exists: ${DATA_DIR}/database.db"

        # Try to query database to verify it's valid
        if sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('${DATA_DIR}/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = cursor.fetchall()
    if len(tables) > 0:
        print(f'Found {len(tables)} tables in database')
        sys.exit(0)
    else:
        print('No tables found in database')
        sys.exit(1)
except Exception as e:
    print(f'Database validation failed: {e}')
    sys.exit(1)
" 2>&1; then
            log_info "✓ Database structure is valid"
        else
            log_error "✗ Database validation failed!"
            cd - > /dev/null
            exit 1
        fi
    else
        log_error "✗ Database file not found at ${DATA_DIR}/database.db"
        cd - > /dev/null
        exit 1
    fi

    cd - > /dev/null
    log_info "Database migration and validation completed successfully"
}
install_frontend() {
    log_info "Installing frontend..."

    # Check if frontend/dist exists
    if [[ ! -d "./frontend/dist" ]]; then
        log_warn "Frontend build not found at ./frontend/dist"
        log_info "Attempting to build frontend automatically..."

        # Check if Node.js and npm are available
        if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
            log_error "Node.js and npm are required to build the frontend"
            log_error "Please install Node.js manually or build the frontend on another machine"
            exit 1
        fi

        # Copy environment file to frontend directory
        if [[ -f "./deploy/frontend.env" ]]; then
            log_info "Using deploy/frontend.env for build"
            cp "./deploy/frontend.env" "./frontend/.env"
        elif [[ -f "./deploy/frontend.env.example" ]]; then
            log_info "Using deploy/frontend.env.example for build"
            cp "./deploy/frontend.env.example" "./frontend/.env"
        else
            log_warn "No frontend environment file found, using defaults"
        fi

        # Build frontend
        log_info "Installing frontend dependencies..."
        cd frontend
        npm install

        log_info "Building frontend..."
        npm run build
        cd ..

        if [[ ! -d "./frontend/dist" ]]; then
            log_error "Frontend build failed - dist directory not created"
            exit 1
        fi

        log_info "✓ Frontend built successfully"
    else
        log_info "Frontend build found at ./frontend/dist"

        # Check if frontend was built with environment variables
        if [[ ! -f "./frontend/.env" ]] && [[ ! -f "./deploy/frontend.env" ]]; then
            log_warn "⚠ No frontend environment file found!"
            log_warn "  The frontend may use default values"
        fi
    fi

    # Copy frontend build
    rsync -a --delete ./frontend/dist/ "${WWW_DIR}/"

    log_info "Frontend installed successfully"
}
setup_environment() {
    log_info "Setting up environment configuration..."

    # Setup Backend environment
    if [[ ! -f "${ENV_DIR}/.env" ]]; then
        # Try backend.env first, then backend.env.example
        if [[ -f "./deploy/backend.env" ]]; then
            cp "./deploy/backend.env" "${ENV_DIR}/.env"
            log_info "Backend environment file copied from deploy/backend.env"
        elif [[ -f "./deploy/backend.env.example" ]]; then
            cp "./deploy/backend.env.example" "${ENV_DIR}/.env"
            log_warn "Backend environment file created from template at ${ENV_DIR}/.env"
            log_warn "Please edit ${ENV_DIR}/.env and update the SECRET_KEY and other settings"
        else
            log_error "No backend.env or backend.env.example found in deploy/"
            exit 1
        fi
    else
        log_info "Backend environment file already exists at ${ENV_DIR}/.env"
    fi
}
set_permissions() {
    log_info "Setting file permissions..."

    # Application directory - donationbox user needs write access for lgpio temp files
    chown -R root:"${APP_USER}" "${APP_DIR}"
    chmod -R 750 "${APP_DIR}"

    # Frontend files owned by root
    chown -R root:root "${WWW_DIR}"

    # Data directory owned by app user (must be writable for database)
    chown -R "${APP_USER}:${APP_USER}" "${DATA_DIR}"
    chmod 750 "${DATA_DIR}"

    # Environment directory and .env file readable by app user
    chown root:"${APP_USER}" "${ENV_DIR}"
    chmod 750 "${ENV_DIR}"

    if [[ -f "${ENV_DIR}/.env" ]]; then
        chown root:"${APP_USER}" "${ENV_DIR}/.env"
        chmod 640 "${ENV_DIR}/.env"
    fi

    log_info "Permissions set successfully"
}
install_systemd_service() {
    log_info "Installing systemd service..."
    if [[ ! -f "./deploy/${APP_NAME}.service" ]]; then
        log_error "Service file not found at ./deploy/${APP_NAME}.service"
        exit 1
    fi
    cp "./deploy/${APP_NAME}.service" "/etc/systemd/system/${APP_NAME}.service"
    systemctl daemon-reload
    systemctl enable "${APP_NAME}"
    log_info "Systemd service installed and enabled"
}
install_nginx_config() {
    log_info "Installing nginx configuration..."
    if [[ ! -f "./deploy/nginx.conf" ]]; then
        log_error "Nginx config not found at ./deploy/nginx.conf"
        exit 1
    fi
    cp "./deploy/nginx.conf" "${NGINX_AVAIL}"
    # Enable site
    ln -sf "${NGINX_AVAIL}" "${NGINX_ENABLED}"
    # Test nginx configuration
    log_info "Testing nginx configuration..."
    if nginx -t; then
        log_info "Nginx configuration is valid"
    else
        log_error "Nginx configuration test failed"
        exit 1
    fi
    log_info "Nginx configuration installed"
}
start_services() {
    log_info "Starting services..."
    # Restart application
    systemctl restart "${APP_NAME}"
    # Reload nginx
    systemctl reload nginx
    log_info "Services started"
}
check_service_status() {
    log_info "Checking service status..."
    # Check application service
    if systemctl is-active --quiet "${APP_NAME}"; then
        log_info "✓ ${APP_NAME} service is running"
    else
        log_error "✗ ${APP_NAME} service is not running"
        log_error "Check logs with: journalctl -u ${APP_NAME} -n 50"
    fi
    # Check nginx
    if systemctl is-active --quiet nginx; then
        log_info "✓ nginx is running"
    else
        log_error "✗ nginx is not running"
    fi
}
print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    log_info "Installation completed!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "  1. Edit configuration: ${ENV_DIR}/.env"
    echo "  2. Update SECRET_KEY and other settings"
    echo "  3. Restart service: systemctl restart ${APP_NAME}"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:     journalctl -u ${APP_NAME} -f"
    echo "  - Restart:       systemctl restart ${APP_NAME}"
    echo "  - Status:        systemctl status ${APP_NAME}"
    echo "  - Stop:          systemctl stop ${APP_NAME}"
    echo ""
    echo "Application directories:"
    echo "  - Backend:       ${APP_DIR}/backend"
    echo "  - Frontend:      ${WWW_DIR}"
    echo "  - Data:          ${DATA_DIR}"
    echo "  - Config:        ${ENV_DIR}"
    echo ""
}
main() {
    log_info "Starting DonationBox installation..."
    echo ""

    check_root
    install_system_packages
    create_user
    create_directories
    install_backend
    setup_environment
    set_permissions
    validate_and_run_migrations
    install_frontend
    install_systemd_service
    install_nginx_config
    start_services
    check_service_status
    print_summary
}

main "$@"
