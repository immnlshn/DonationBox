# Raspberry Pi Debian Trixie - Package Overview

## System packages (installed by install.sh)

### Python & Build Tools
- **python3** - Python 3 interpreter
- **python3-venv** - Python Virtual Environment support
- **python3-pip** - Python package installer
- **python3-dev** - Python development headers (for compiling packages)
- **build-essential** - GCC, G++, Make and other build tools (for native Python extensions)

### GPIO Support (Raspberry Pi specific)
- **libgpiod2** - C library for GPIO control (modern alternative to RPi.GPIO)
- **libgpiod-dev** - Development headers for libgpiod
- **python3-libgpiod** - Python bindings for libgpiod
- **gpiod** - Command-line tools for GPIO (gpioinfo, gpioget, gpioset, gpiomon)

### Database
- **sqlite3** - SQLite command-line tool
- **libsqlite3-dev** - SQLite development headers (if native extensions are needed)

### Web Server & Tools
- **nginx** - Web server / reverse proxy
- **rsync** - File sync tool
- **curl** - HTTP client
- **git** - Version control

### Node.js (optional, only if frontend is built on server)
- **nodejs** - Node.js runtime
- **npm** - Node package manager

## Python packages (from requirements.txt, installed in venv)

### GPIO
- **gpiozero==2.0.1** - High-level GPIO library
- **colorzero==2.0** - Dependency of gpiozero

### Backend Framework
- **fastapi==0.127.0** - Web framework
- **uvicorn==0.40.0** - ASGI server
- **starlette==0.50.0** - ASGI framework (basis of FastAPI)

### Database & ORM
- **SQLAlchemy==2.0.45** - SQL toolkit and ORM
- **alembic==1.18.0** - Database migration tool
- **aiosqlite==0.22.1** - Async SQLite driver

### WebSocket Support
- **python-socketio==5.15.1** - Socket.IO server
- **python-engineio==4.12.3** - Engine.IO server
- **websockets==15.0.1** - WebSocket protocol implementation
- **websocket-client==1.9.0** - WebSocket client

### Security & Validation
- **pydantic==2.12.5** - Data validation
- **pydantic-settings==2.12.0** - Settings management
- **python-dotenv==1.2.1** - Environment variable management

## GPIO Pin Factory Options

The project supports different GPIO backends via gpiozero:

### 1. lgpio (Recommended for Debian Trixie)
```bash
PIN_FACTORY=lgpio
ENABLE_GPIO=true
```
- Modern C library
- Requires: `libgpiod2`, `libgpiod-dev`, `python3-libgpiod`
- Best performance, actively maintained

### 2. rpigpio (Legacy)
```bash
PIN_FACTORY=rpigpio
ENABLE_GPIO=true
```
- Based on RPi.GPIO
- Also works on newer systems
- Automatically installed via pip

### 3. native (Fallback)
```bash
PIN_FACTORY=native
ENABLE_GPIO=true
```
- Pure Python implementation
- No additional dependencies
- Slower than lgpio

### 4. mock (Development/Testing)
```bash
PIN_FACTORY=mock
ENABLE_GPIO=false
```
- Simulates GPIO without hardware
- For development on non-Raspberry-Pi systems

## User Permissions

The `donationbox` user is automatically added to the following groups:

- **gpio** - Access to GPIO pins (`/dev/gpiochip*`)
- **dialout** - Access to serial devices (`/dev/ttyS*`, `/dev/ttyUSB*`) if needed

## System Requirements

### Minimum
- Raspberry Pi 3 or newer
- Debian Trixie (Testing) or Bookworm (Stable)
- 512 MB RAM (1 GB recommended)
- 2 GB free storage

### Tested on
- Raspberry Pi 4 Model B
- Raspberry Pi 5
- Debian Trixie (Testing)

## Verification after installation

### Test GPIO access
```bash
# Show GPIO chips
gpioinfo

# Test as donationbox user
sudo -u donationbox gpioinfo

# Check GPIO groups
groups donationbox
```

### Check Python dependencies
```bash
/opt/donationbox/venv/bin/pip list | grep -E "(gpiozero|colorzero|libgpiod)"
```

### Service status
```bash
systemctl status donationbox
journalctl -u donationbox -f
```
