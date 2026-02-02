# DonationBox Deployment

This directory contains all necessary files for deploying the DonationBox application.

## Files

- **install.sh** - Main installation script
- **donationbox.service** - Systemd service file
- **nginx.conf** - Nginx configuration
- **.env.example** - Example environment variables

## Prerequisites

- Ubuntu/Debian Server (tested on Ubuntu 22.04+)
- Root/Sudo access
- Frontend must be built first (`npm run build` in frontend directory)

## Installation

### 1. Build frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. Run installation

```bash
sudo ./deploy/install.sh
```

The script performs the following steps:

1. ✅ Installs system packages (Python3, Nginx, etc.)
2. ✅ Creates system user `donationbox`
3. ✅ Creates directories under `/opt`, `/var/lib`, `/etc`, `/var/www`
4. ✅ Copies backend code and installs dependencies in venv
5. ✅ Runs database migrations
6. ✅ Copies frontend build
7. ✅ Sets up environment variables
8. ✅ Sets permissions
9. ✅ Installs systemd service
10. ✅ Configures Nginx
11. ✅ Starts all services

### 3. Adjust configuration

After installation:

```bash
sudo nano /etc/donationbox/.env
```

Important to change:
- `SECRET_KEY` - Generate a secure key
- `ALLOWED_ORIGINS` - Set your domain
- `DATABASE_URL` - Adjust if necessary
- `ENABLE_GPIO` - Set to `true` when on Raspberry Pi

### 4. Restart service

```bash
sudo systemctl restart donationbox
```

## Directory structure after installation

```
/opt/donationbox/          # Application code
├── backend/               # Backend Python code
└── venv/                  # Python Virtual Environment

/var/lib/donationbox/      # Data (database, etc.)
├── database.db            # SQLite database

/etc/donationbox/          # Configuration
└── .env                   # Environment variables

/var/www/donationbox/      # Frontend static files
└── index.html
    assets/
```

## Useful commands

### Service Management

```bash
# Check status
sudo systemctl status donationbox

# View logs
sudo journalctl -u donationbox -f

# Restart service
sudo systemctl restart donationbox

# Stop service
sudo systemctl stop donationbox

# Start service
sudo systemctl start donationbox
```

### Nginx Management

```bash
# Reload nginx
sudo systemctl reload nginx

# Nginx status
sudo systemctl status nginx

# Test nginx configuration
sudo nginx -t
```

### Deploy updates

There are two update scripts:

#### 1. Full update (with backup) - RECOMMENDED

```bash
# Rebuild frontend
cd frontend
npm run build
cd ..

# Run update (automatically creates backup)
sudo ./deploy/update.sh
```

Features:
- ✅ Automatically creates backup
- ✅ Updates backend & frontend
- ✅ Runs database migrations
- ✅ Updates Python dependencies
- ✅ Health check after update
- ✅ Automatic rollback on error
- ✅ Keeps the last 5 backups

#### 2. Quick update (without backup)

```bash
# Rebuild frontend
cd frontend
npm run build
cd ..

# Quick update
sudo ./deploy/quick-update.sh
```

Features:
- ⚡ Very fast
- ⚠️ No backup
- ⚠️ No dependency updates
- ⚠️ No migrations
- Only for small frontend/backend changes

## SSL/HTTPS setup (Optional)

With Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Request certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is already configured
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u donationbox -n 100

# Start manually for debugging
cd /opt/donationbox/backend
sudo -u donationbox /opt/donationbox/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
```

### Database problems

```bash
# Re-run migrations
cd /opt/donationbox/backend
sudo -u donationbox /opt/donationbox/venv/bin/alembic upgrade head
```

### Nginx shows 502 Bad Gateway

- Backend not running → `sudo systemctl start donationbox`
- Port 8000 blocked → `sudo netstat -tulpn | grep 8000`

### Permission problems

```bash
# Reset permissions
sudo chown -R root:root /opt/donationbox /var/www/donationbox
sudo chown -R donationbox:donationbox /var/lib/donationbox
sudo chown -R root:donationbox /etc/donationbox
sudo chmod 640 /etc/donationbox/.env
```

## Uninstallation

### Automatic uninstallation (RECOMMENDED)

```bash
sudo ./deploy/uninstall.sh
```

The script guides you interactively through the uninstallation process:
- ✅ Stops and disables the service
- ✅ Removes all application files
- ✅ Removes Nginx configuration
- ✅ Removes system user
- ❓ Asks if database should be deleted
- ❓ Asks if backups should be deleted
- ℹ️ System packages (Python, Nginx, etc.) remain installed

### Manual uninstallation

```bash
# Stop and disable service
sudo systemctl stop donationbox
sudo systemctl disable donationbox

# Remove files
sudo rm /etc/systemd/system/donationbox.service
sudo rm /etc/nginx/sites-enabled/donationbox
sudo rm /etc/nginx/sites-available/donationbox
sudo rm -rf /opt/donationbox
sudo rm -rf /var/www/donationbox
sudo rm -rf /var/lib/donationbox
sudo rm -rf /etc/donationbox
sudo rm -rf /var/backups/donationbox

# Remove user
sudo userdel donationbox

# Reload nginx
sudo systemctl reload nginx
sudo systemctl daemon-reload
```

## Support

For problems:
1. Check logs: `sudo journalctl -u donationbox -f`
2. Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Service status: `sudo systemctl status donationbox`
