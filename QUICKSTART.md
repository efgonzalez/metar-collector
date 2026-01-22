# METAR Collector - Quick Start Guide

Get your METAR data collection service running on Ubuntu DigitalOcean in 5 minutes!

## What This Does

- Automatically fetches METAR data for Canary Islands airports daily:
  - **GCGM**: La Gomera Airport
  - **GCLA**: La Palma Airport
- Stores data in SQLite database with duplicate prevention
- Runs as a systemd service on your Ubuntu server
- Provides export tools for CSV/JSON formats
- Fetches highest time resolution available (typically every 30-60 minutes)

## Prerequisites

1. **CheckWX API Key** (Free)
   - Go to https://www.checkwx.com/
   - Sign up (free, no credit card needed)
   - Get your API key from the dashboard
   - Free tier: 50 requests/day (perfect for this use case)

2. **Ubuntu DigitalOcean Droplet**
   - Ubuntu 20.04 LTS or newer
   - Minimum 512MB RAM (1GB recommended)
   - You need root/sudo access

## Installation Steps

### 1. Create the Package (On Your Local Machine)

```bash
cd /Users/edu/claude/metar
./create_package.sh
```

This creates `metar-collector-package.tar.gz` (about 12KB)

### 2. Upload to Your DigitalOcean Droplet

```bash
# Replace YOUR_DROPLET_IP with your server's IP address
scp metar-collector-package.tar.gz root@YOUR_DROPLET_IP:/tmp/
```

### 3. Install on Server

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Extract and run installer
cd /tmp
tar -xzf metar-collector-package.tar.gz
cd metar-collector-package
sudo ./install.sh
```

The installer will:
- Ask for your CheckWX API key
- Set up everything automatically
- Run the first data collection
- Enable daily automatic collection at 02:00 UTC

**That's it!** The service is now running.

## Verify It's Working

```bash
# Check service status
systemctl status metar-collector.timer

# View recent logs
journalctl -u metar-collector -n 20

# Check database
sqlite3 /opt/metar-collector/metar_data.db "SELECT COUNT(*) FROM metar_observations;"
```

## Export Your Data

```bash
# Run export tool
cd /opt/metar-collector
sudo -u metar ./venv/bin/python3 export_data.py
```

Choose from:
1. Export all data to CSV
2. Export all data to JSON
3. Export daily summary
4. Export last 7 days
5. Export last 30 days
6. Export all formats

### Download Exported Data to Your Computer

```bash
# From your local machine
scp root@YOUR_DROPLET_IP:/opt/metar-collector/metar_*.csv .
```

## Common Tasks

### Trigger Manual Collection

```bash
sudo systemctl start metar-collector.service
```

### View Logs

```bash
# Live log tail
journalctl -u metar-collector -f

# Last 24 hours
journalctl -u metar-collector --since "24 hours ago"
```

### Check How Much Data You Have

```bash
sqlite3 /opt/metar-collector/metar_data.db << EOF
SELECT
    COUNT(*) as observations,
    MIN(date) as first_date,
    MAX(date) as last_date
FROM metar_observations;
EOF
```

### Download Entire Database

```bash
# From your local machine
scp root@YOUR_DROPLET_IP:/opt/metar-collector/metar_data.db .
```

## Data Collection Details

- **When**: Daily at 02:00 UTC (automatic)
- **What**: Last 48 hours of METAR data (with overlap to prevent gaps)
- **Storage**: SQLite database at `/opt/metar-collector/metar_data.db`
- **Duplicates**: Automatically prevented by unique constraint
- **Logs**: Available via `journalctl -u metar-collector`

## Expected Data

- **Frequency**: METARs are typically issued every 30-60 minutes
- **Per Day**: ~10-24 observations (depending on airport activity)
- **Data Fields**:
  - Observation time
  - Wind direction (degrees or VRB for variable)
  - Wind speed (knots)
  - Wind gusts (when present)
  - Full METAR text

## Troubleshooting

### No data appearing?

```bash
# Check if service ran successfully
systemctl status metar-collector.service

# Check logs for errors
journalctl -u metar-collector -n 50

# Try manual run
sudo systemctl start metar-collector.service
```

### API key issues?

```bash
# Update API key
sudo nano /etc/systemd/system/metar-collector.service
# Find: Environment="CHECKWX_API_KEY=..."
# Update with your key

sudo systemctl daemon-reload
sudo systemctl start metar-collector.service
```

## What Gets Stored

For each METAR observation:
```
- Station: GCGM or GCLA
- Date/Time: 2026-01-21 14:30:00
- Wind Direction: 270 (degrees) or VRB
- Wind Speed: 15 (knots)
- Wind Gust: 25 (knots, if present)
- Full METAR: GCGM 211430Z 27015G25KT...
```

## Cost

- **CheckWX API**: Free (50 requests/day)
- **Storage**: ~1 MB per year of data
- **DigitalOcean**: Use your existing droplet (minimal resource usage)

## Next Steps

After collecting data for a while:
1. Export to CSV for analysis in Excel/Python
2. Create visualizations with your existing wind_visualization.html
3. Set up automated backups (see DEPLOYMENT.md)
4. Download database periodically to your local machine

## Support

- Full documentation: See `DEPLOYMENT.md`
- CheckWX API docs: https://www.checkwx.com/api/
- METAR format: https://www.weather.gov/media/wrh/mesowest/metar_decode_key.pdf

## File Locations

All files are in `/opt/metar-collector/`:
- `metar_data.db` - Your data
- `metar_collector.log` - Application logs
- `export_data.py` - Export tool
- `venv/` - Python environment

Service logs are in systemd journal (use `journalctl`)

---

**You're all set!** The service will collect data daily automatically. Check back in a few days to export and analyze your data.
