# METAR Collector Project - Development Context

## Project Overview

Automated METAR data collection service for Canary Islands airports that stores weather observation data in SQLite database with daily collection via systemd timer on Ubuntu.

Supported airports:
- **GCGM**: La Gomera Airport
- **GCLA**: La Palma Airport

## What We Built

### Core Components

1. **metar_collector.py** - Main collection service
   - Fetches METAR data from CheckWX API
   - Stores in SQLite with duplicate prevention
   - Fetches last 48 hours with overlap to prevent gaps
   - Runs as `edu` user
   - Full logging to systemd journal

2. **export_data.py** - Data export utility
   - Interactive menu for CSV/JSON exports
   - Daily summary aggregations
   - Date range filtering

3. **Systemd Integration**
   - `metar-collector.service` - Service unit (runs as edu user)
   - `metar-collector.timer` - Daily at 02:00 UTC with randomized delay
   - Security hardened (NoNewPrivileges, ProtectSystem, etc.)

4. **install.sh** - Automated Ubuntu installer
   - Uses existing edu user
   - Sets up /home/edu/metar-collector
   - Creates Python venv
   - Installs dependencies
   - Configures systemd
   - Runs initial collection

5. **Deployment Package**
   - `create_package.sh` - Bundles everything into tarball
   - `metar-collector-package.tar.gz` - Ready to deploy (9.2KB)

### Database Schema

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

## Architecture Decisions

### Why SQLite?
- Simple, serverless
- Automatic duplicate prevention via UNIQUE constraint
- Easy to backup (single file)
- No additional services needed
- ~1MB per year of data

### Why 48-hour fetch window?
- Ensures no gaps if service misses a run
- Duplicates automatically filtered by database constraint
- CheckWX free tier allows this (50 requests/day)

### Why systemd timer vs cron?
- Better logging integration (journalctl)
- Persistent (runs on boot if missed)
- RandomizedDelaySec to avoid API hammering
- Modern Ubuntu standard

### Security Design
- Runs as existing edu user
- No dedicated service user needed
- systemd hardening (ProtectSystem, ProtectHome, NoNewPrivileges)
- Minimal file permissions
- API key in systemd environment (not in code)

## Prerequisites

### Ubuntu Server
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sqlite3
```

### CheckWX API Key
- Free at https://www.checkwx.com/
- 50 requests/day (sufficient for daily collection)

## Deployment

```bash
# 1. Upload package
scp metar-collector-package.tar.gz root@SERVER:/tmp/

# 2. Install
ssh root@SERVER
cd /tmp
tar -xzf metar-collector-package.tar.gz
cd metar-collector-package
sudo ./install.sh
# Enter CheckWX API key when prompted
```

## File Locations After Install

```
/home/edu/metar-collector/
├── metar_collector.py       # Main script
├── export_data.py            # Export tool
├── requirements.txt          # Dependencies (requests, pandas, pytz)
├── metar_data.db            # SQLite database
├── metar_collector.log      # Application logs
└── venv/                    # Python virtual environment

/etc/systemd/system/
├── metar-collector.service  # Service definition
└── metar-collector.timer    # Timer (daily at 02:00 UTC)
```

## Common Tasks

```bash
# Check status
systemctl status metar-collector.timer

# View logs
journalctl -u metar-collector -f

# Manual collection
sudo systemctl start metar-collector.service

# Export data
cd /home/edu/metar-collector
./venv/bin/python3 export_data.py

# Query database
sqlite3 /home/edu/metar-collector/metar_data.db "SELECT COUNT(*) FROM metar_observations;"

# Download data
scp root@SERVER:/home/edu/metar-collector/metar_data.db .
```

## Current Status

- Package created and tested locally
- Ready for deployment to DigitalOcean Ubuntu instance
- User reported installation error on first run (needs troubleshooting)
- Error was during initial collection: "Job for metar-collector.service failed"
- Need to check logs: `journalctl -u metar-collector.service -n 50`

## Known Issues to Debug

1. Initial service run failed - need to check:
   - API key validity
   - Virtual environment setup
   - Python dependencies installation
   - Network connectivity to CheckWX API
   - Permissions on /home/edu/metar-collector

## Next Steps

1. Debug the service failure (check journalctl logs)
2. Verify API key is correct
3. Test manual run: `/home/edu/metar-collector/venv/bin/python3 /home/edu/metar-collector/metar_collector.py`
4. Once working, verify daily timer
5. Let data collect for a few days
6. Export and analyze

## Development Context

This project evolved from existing METAR visualization work:
- Already had `fetch_checkwx_data.py` for manual fetching
- Already had visualization tools (wind_explorer.html)
- User wanted automated daily collection on cloud server
- Needed packaging for DigitalOcean deployment
- Preferred CheckWX API (easier than OGIMET)

## API Details

### CheckWX Endpoint
```
GET https://api.checkwx.com/metar/{station}/{start_time}/{end_time}
Headers: X-API-Key: YOUR_KEY
```

### METAR Parsing
Wind pattern: `(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS)`
- Example: `27015G25KT` = 270° at 15kt gusting to 25kt
- Time pattern: `(\d{6}Z)` = DDHHmmZ format

## Resources

- CheckWX API: https://www.checkwx.com/api/
- METAR format: https://www.weather.gov/media/wrh/mesowest/metar_decode_key.pdf
- Systemd timers: `man systemd.timer`
- Project docs: QUICKSTART.md, DEPLOYMENT.md
