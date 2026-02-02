# DonationBox Deploy Scripts - Complete Overview

## 📦 Available Scripts

### 1. install.sh - Initial Installation
**Usage:** `sudo ./deploy/install.sh`

**Function:**
- Installs system packages (Python, Nginx, GPIO support, etc.)
- Creates system user and directories
- Installs backend with venv
- Copies frontend build
- Runs database migrations
- Configures systemd service
- Sets up Nginx reverse proxy
- Starts all services

**When to use:**
- ✅ First installation on new server
- ✅ Complete reinstallation after uninstall

---

### 2. update.sh - Full Update
**Usage:** `sudo ./deploy/update.sh`

**Function:**
- Creates automatic backup (backend, DB, frontend, config)
- Safely stops service
- Updates backend & frontend
- Updates Python dependencies
- Runs database migrations
- Starts service and performs health check
- Automatic rollback on error
- Keeps the last 5 backups

**When to use:**
- ✅ Production updates
- ✅ Updates with database schema changes
- ✅ Updates with new dependencies
- ✅ All critical updates

**Duration:** ~30-60 seconds

---

### 3. quick-update.sh - Quick Update
**Usage:** `sudo ./deploy/quick-update.sh`

**Function:**
- Stops service
- Updates backend code
- Updates frontend
- Starts service
- Reloads Nginx

**When to use:**
- ✅ Small frontend changes (CSS, JS)
- ✅ Backend bugfixes without new dependencies
- ✅ Development/Testing
- ⚠️ NOT for schema changes or new dependencies

**Duration:** ~5-10 seconds

---

### 4. uninstall.sh - Uninstallation
**Usage:** `sudo ./deploy/uninstall.sh`

**Function:**
- Interactive confirmation
- Stops and disables service
- Removes all application files
- Removes Nginx configuration
- Removes systemd service
- Removes system user
- Optional: Delete database
- Optional: Delete backups
- System packages remain installed

**When to use:**
- ✅ Complete removal of application
- ✅ Before reinstallation (with database preservation)
- ✅ Server cleanup

---

## 📊 Comparison Table

| Feature | install.sh | update.sh | quick-update.sh | uninstall.sh |
|---------|------------|-----------|-----------------|--------------|
| Install packages | ✅ | ❌ | ❌ | ❌ |
| Create venv | ✅ | ❌ | ❌ | ❌ |
| Update dependencies | ✅ | ✅ | ❌ | ❌ |
| DB migrations | ✅ | ✅ | ❌ | ❌ |
| Create backup | ❌ | ✅ | ❌ | ❌ |
| Rollback on error | ❌ | ✅ | ❌ | N/A |
| Health check | ✅ | ✅ | ❌ | N/A |
| Interactive | ❌ | ❌ | ❌ | ✅ |
| Root required | ✅ | ✅ | ✅ | ✅ |
| Duration | ~2-5 min | ~30-60s | ~5-10s | ~10-30s |

---

## 🚀 Typical Workflows

### Initial Installation
```bash
# Build frontend
cd frontend
npm install
npm run build
cd ..

# Installation
sudo ./deploy/install.sh

# Adjust configuration
sudo nano /etc/donationbox/.env

# Restart service
sudo systemctl restart donationbox
```

---

### Development Cycle
```bash
# Make changes...

# Rebuild frontend
cd frontend && npm run build && cd ..

# Quick update
sudo ./deploy/quick-update.sh

# Check logs
sudo journalctl -u donationbox -f
```

---

### Production Update
```bash
# Make changes...

# Build frontend
cd frontend && npm run build && cd ..

# Safe update with backup
sudo ./deploy/update.sh

# Check status
sudo systemctl status donationbox
```

---

### Migration / Reinstallation
```bash
# 1. Remove old installation (keep data)
sudo ./deploy/uninstall.sh
# Choose "no" for "Remove data directory"

# 2. Reinstall
sudo ./deploy/install.sh

# 3. Existing database will be used automatically
```

---

### Complete Uninstallation
```bash
sudo ./deploy/uninstall.sh
# Choose "yes" for all questions
```

---

## 📁 Directory Structure After Installation

```
/opt/donationbox/                # Application code
├── backend/                     # Backend Python code
│   ├── app.py
│   ├── core/
│   ├── models/
│   ├── routes/
│   └── ...
└── venv/                        # Python Virtual Environment

/var/lib/donationbox/            # Data (writable for app user)
└── database.db                  # SQLite database

/etc/donationbox/                # Configuration
└── .env                         # Environment variables

/var/www/donationbox/            # Frontend static files
├── index.html
└── assets/

/var/backups/donationbox/        # Backups (from update.sh)
├── 20260202_120000/
├── 20260202_150000/
└── ...

/etc/systemd/system/
└── donationbox.service          # Systemd service

/etc/nginx/sites-available/
└── donationbox                  # Nginx configuration

/etc/nginx/sites-enabled/
└── donationbox -> ../sites-available/donationbox
```

---

## 🔧 Prerequisites

### For all scripts:
- Root/Sudo access required
- Debian/Ubuntu-based system (tested on Debian Trixie)
- Frontend must be built (`npm run build`)

### For install.sh additionally:
- Internet connection (for package installation)
- At least 2 GB free storage

---

## 📋 Useful Commands

### Service Management
```bash
sudo systemctl status donationbox    # Check status
sudo systemctl start donationbox     # Start
sudo systemctl stop donationbox      # Stop
sudo systemctl restart donationbox   # Restart
sudo systemctl enable donationbox    # Enable autostart
sudo systemctl disable donationbox   # Disable autostart
```

### Logs
```bash
sudo journalctl -u donationbox -f              # Live logs
sudo journalctl -u donationbox -n 100          # Last 100 lines
sudo journalctl -u donationbox --since "1h ago" # Last hour
```

### Nginx
```bash
sudo nginx -t                        # Test configuration
sudo systemctl reload nginx          # Reload
sudo systemctl status nginx          # Status
tail -f /var/log/nginx/error.log     # Error log
```

### Database
```bash
sqlite3 /var/lib/donationbox/database.db    # Open database
.tables                                      # Show tables
.schema donations                            # Show schema
SELECT COUNT(*) FROM donations;              # Count donations
```

### Backups
```bash
ls -lh /var/backups/donationbox/             # All backups
du -sh /var/backups/donationbox/*            # Backup sizes
```

---

## 🛡️ Security

All scripts implement:
- ✅ Root rights check
- ✅ `set -euo pipefail` (exit on error)
- ✅ Secure permissions
- ✅ Separation of code and data
- ✅ Systemd security features (NoNewPrivileges, PrivateTmp, etc.)

---

## 🐛 Troubleshooting

### Installation fails
```bash
# Check logs
sudo journalctl -xe

# Test manual package installation
sudo apt-get update
sudo apt-get install python3 python3-venv nginx
```

### Update fails
```bash
# Get backup path from logs
# Manual rollback possible

# Or: Try update again
sudo ./deploy/update.sh
```

### Service won't start
```bash
# Error details
sudo journalctl -u donationbox -n 50

# Manual check
cd /opt/donationbox/backend
sudo -u donationbox /opt/donationbox/venv/bin/uvicorn app:app
```

### Permission problems
```bash
sudo chown -R root:root /opt/donationbox /var/www/donationbox
sudo chown -R donationbox:donationbox /var/lib/donationbox
sudo chmod 640 /etc/donationbox/.env
sudo chown root:donationbox /etc/donationbox/.env
```

---

## 📞 Support

For problems:
1. Check logs: `sudo journalctl -u donationbox -n 100`
2. Service status: `sudo systemctl status donationbox`
3. Nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Check permissions: `ls -la /var/lib/donationbox`

---

## 📝 License

See LICENSE in the main directory
