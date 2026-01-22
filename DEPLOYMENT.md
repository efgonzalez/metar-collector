# METAR Collector Service - Deployment Guide

Automated METAR data collection service for Canary Islands airports running on Ubuntu DigitalOcean instance.

Supported airports:
- **GCGM**: La Gomera Airport
- **GCLA**: La Palma Airport

## Features

- **Automated Daily Collection**: Runs daily at 02:00 UTC via systemd timer
- **SQLite Storage**: Efficient storage with automatic duplicate prevention
- **48-Hour Overlap**: Fetches last 48 hours to ensure no gaps in data
- **Systemd Integration**: Proper service management with logging
- **Data Export**: Multiple export formats (CSV, JSON, daily summaries)
- **High Reliability**: Persistent timer (runs on boot if missed) with randomized delay

## Prerequisites

### 1. Get CheckWX API Key

1. Visit https://www.checkwx.com/
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API key
5. Free tier: 50 requests/day (sufficient for daily collection)

### 2. DigitalOcean Droplet Requirements

- **OS**: Ubuntu 20.04 LTS or newer
- **RAM**: 512MB minimum (1GB recommended)
- **Storage**: 5GB minimum
- **Python**: 3.8 or newer (included in Ubuntu 20.04+)

## Installation

### Step 1: Create and Upload Package

On your local machine (where you have this repository):

```bash
# Create the deployment package
./create_package.sh

# This creates: metar-collector-package.tar.gz
```

### Step 2: Upload to DigitalOcean

```bash
# Upload package to your droplet
scp metar-collector-package.tar.gz root@your-droplet-ip:/tmp/

# SSH into your droplet
ssh root@your-droplet-ip
```

### Step 3: Extract and Install

On your DigitalOcean droplet:

```bash
# Extract package
cd /tmp
tar -xzf metar-collector-package.tar.gz

# Run installation script
cd metar-collector-package
sudo ./install.sh
```

The installer will:
1. Prompt for your CheckWX API key
2. Create a dedicated `metar` user
3. Install to `/opt/metar-collector`
4. Set up Python virtual environment
5. Install dependencies
6. Configure systemd service and timer
7. Run initial data collection
8. Enable automatic daily collection

## Usage

### Check Service Status

```bash
# Check if timer is running
systemctl status metar-collector.timer

# Check last service run
systemctl status metar-collector.service

# View service logs
journalctl -u metar-collector -f
```

### Manual Data Collection

```bash
# Trigger immediate collection
sudo systemctl start metar-collector.service

# Check status
sudo systemctl status metar-collector.service
```

### Export Data

```bash
# Switch to installation directory
cd /opt/metar-collector

# Run export tool (interactive)
sudo -u metar ./venv/bin/python3 export_data.py
```

Export options:
1. Export all data to CSV
2. Export all data to JSON
3. Export daily summary to JSON
4. Export last 7 days to CSV
5. Export last 30 days to CSV
6. Export all formats

### Download Data from Server

From your local machine:

```bash
# Download CSV export
scp root@your-droplet-ip:/opt/metar-collector/metar_*.csv .

# Download JSON export
scp root@your-droplet-ip:/opt/metar-collector/metar_*.json .

# Download entire database
scp root@your-droplet-ip:/opt/metar-collector/metar_data.db .
```

### Query Database Directly

```bash
# Access SQLite database
sqlite3 /opt/metar-collector/metar_data.db

# Example queries:
sqlite> SELECT COUNT(*) FROM metar_observations;
sqlite> SELECT date, COUNT(*) FROM metar_observations GROUP BY date;
sqlite> SELECT * FROM metar_observations ORDER BY datetime DESC LIMIT 10;
sqlite> .exit
```

## Service Schedule

- **Runs**: Daily at 02:00 UTC
- **Fetches**: Last 48 hours of data (with overlap to prevent gaps)
- **Persistence**: If droplet is down, runs on next boot
- **Randomization**: Random 0-5 minute delay to avoid API hammering

To change schedule, edit `/etc/systemd/system/metar-collector.timer`:

```ini
# Change this line for different schedule:
OnCalendar=*-*-* 02:00:00
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart metar-collector.timer
```

## File Locations

```
/opt/metar-collector/
├── metar_collector.py      # Main collector script
├── export_data.py           # Data export utility
├── requirements.txt         # Python dependencies
├── metar_data.db           # SQLite database (created on first run)
├── metar_collector.log     # Application log file
└── venv/                   # Python virtual environment

/etc/systemd/system/
├── metar-collector.service # Systemd service unit
└── metar-collector.timer   # Systemd timer unit
```

## Monitoring

### Check Collection is Working

```bash
# View recent logs
journalctl -u metar-collector --since "24 hours ago"

# Check database
sqlite3 /opt/metar-collector/metar_data.db \
  "SELECT COUNT(*), MIN(date), MAX(date) FROM metar_observations;"
```

### Expected Behavior

- **Daily runs**: Should see new journal entries each day
- **New observations**: 8-24 new observations per day (METAR typically every 30-60 minutes)
- **Duplicates**: Some duplicates are normal due to 48-hour overlap
- **API errors**: Rare, but logged if they occur

## Troubleshooting

### Service Not Running

```bash
# Check timer status
systemctl status metar-collector.timer

# If not active, start it
sudo systemctl start metar-collector.timer
sudo systemctl enable metar-collector.timer
```

### No New Data

```bash
# Check logs for errors
journalctl -u metar-collector -n 50

# Test manual run
sudo systemctl start metar-collector.service

# Check API key is correct
grep CHECKWX_API_KEY /etc/systemd/system/metar-collector.service
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R metar:metar /opt/metar-collector

# Fix permissions
sudo chmod 755 /opt/metar-collector
sudo chmod 644 /opt/metar-collector/*.py
```

### Update API Key

```bash
# Edit service file
sudo nano /etc/systemd/system/metar-collector.service

# Find and update this line:
Environment="CHECKWX_API_KEY=your_new_key_here"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart metar-collector.service
```

## Data Retention

The database will grow over time. Expected size:
- ~100 bytes per observation
- ~10-20 observations per day
- ~1 MB per year

No automatic cleanup is configured. To manage size:

```bash
# Remove data older than 1 year
sqlite3 /opt/metar-collector/metar_data.db \
  "DELETE FROM metar_observations WHERE date < date('now', '-1 year');"

# Vacuum to reclaim space
sqlite3 /opt/metar-collector/metar_data.db "VACUUM;"
```

## Backup

### Backup Database

```bash
# Create backup
cp /opt/metar-collector/metar_data.db \
   /opt/metar-collector/metar_data.db.backup-$(date +%Y%m%d)

# Or export to CSV for long-term storage
cd /opt/metar-collector
sudo -u metar ./venv/bin/python3 export_data.py
```

### Automated Backup

Add to crontab for weekly backups:

```bash
sudo crontab -e

# Add this line (runs every Sunday at 3 AM):
0 3 * * 0 cp /opt/metar-collector/metar_data.db /opt/metar-collector/backups/metar_data.db.$(date +\%Y\%m\%d)
```

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop metar-collector.timer
sudo systemctl disable metar-collector.timer
sudo systemctl stop metar-collector.service
sudo systemctl disable metar-collector.service

# Remove systemd files
sudo rm /etc/systemd/system/metar-collector.*

# Remove installation
sudo rm -rf /opt/metar-collector

# Remove service user (optional)
sudo userdel metar

# Reload systemd
sudo systemctl daemon-reload
```

## Support

- CheckWX API documentation: https://www.checkwx.com/api/
- METAR format reference: https://www.weather.gov/media/wrh/mesowest/metar_decode_key.pdf
- Systemd timers: `man systemd.timer`

## Database Schema

```sql
CREATE TABLE metar_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station TEXT NOT NULL,              -- ICAO code (GCGM, GCLA)
    observation_time TEXT NOT NULL,     -- DDHHmmZ format
    datetime TEXT NOT NULL,             -- ISO datetime
    date TEXT NOT NULL,                 -- YYYY-MM-DD
    wind_direction TEXT,                -- Degrees or VRB
    wind_speed INTEGER,                 -- Knots
    wind_gust INTEGER,                  -- Knots (nullable)
    unit TEXT,                          -- KT or MPS
    metar_text TEXT NOT NULL,           -- Full METAR report
    fetched_at TEXT NOT NULL,           -- When data was collected
    UNIQUE(station, observation_time, datetime)
);
```

Indexes:
- `idx_station_date` on (station, date)
- `idx_datetime` on (datetime)
