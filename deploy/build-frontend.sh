#!/usr/bin/env bash
set -euo pipefail

################################################################################
# Frontend Build Script
#
# This script prepares and builds the frontend with the correct environment
################################################################################

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

# Check if we're in the project root
if [[ ! -d "frontend" ]] || [[ ! -d "deploy" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_info "Preparing to build frontend..."

# Check for frontend environment configuration
if [[ -f "deploy/frontend.env" ]]; then
    log_info "Using deploy/frontend.env"
    cp "deploy/frontend.env" "frontend/.env"
elif [[ -f "deploy/frontend.env.example" ]]; then
    log_warn "deploy/frontend.env not found, using deploy/frontend.env.example"
    log_warn "For production, copy and configure deploy/frontend.env.example to deploy/frontend.env first!"
    cp "deploy/frontend.env.example" "frontend/.env"
else
    log_error "No frontend environment file found!"
    log_error "Please create deploy/frontend.env.example or deploy/frontend.env"
    exit 1
fi

# Show current configuration
log_info "Frontend will be built with the following configuration:"
echo ""
grep -E "^VITE_" frontend/.env || echo "No VITE_ variables found"
echo ""

# Install dependencies if needed
cd frontend
if [[ ! -d "node_modules" ]]; then
    log_info "Installing npm dependencies..."
    npm install
else
    log_info "npm dependencies already installed"
fi

# Build
log_info "Building frontend..."
npm run build

cd ..

log_info "✓ Frontend build completed!"
log_info "  Build output: frontend/dist/"
log_info ""
log_info "Next step: Run installation"
log_info "  sudo ./deploy/install.sh"
