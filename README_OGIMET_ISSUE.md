# OGIMET Data Fetching - Current Status

## Issue Discovered
When attempting to fetch 2025 wind data for station GCGM from OGIMET, several API endpoints were tested:

1. `https://www.ogimet.com/cgi-bin/getmetar` - Returns error: "La fecha de inicio no es correcta"
2. `https://www.ogimet.com/display_metars2.php` - Returns empty results
3. `https://www.ogimet.com/cgi-bin/query_metars.php` - Returns 404 Not Found

## What This Means
- OGIMET may have changed their API structure
- The service may be temporarily unavailable
- There may be access restrictions or rate limiting

## Your Options

### Option 1: Use the Prepared Script (export_wind_data.py)
The script `export_wind_data.py` has been updated to:
- Fetch METAR data from OGIMET for the year 2025
- Parse wind information (sustained and gusts)
- Convert times to Canary Islands local time
- Export to CSV with both knots and km/h

**To use it when OGIMET is accessible:**
```bash
source venv/bin/activate
python export_wind_data.py
```

### Option 2: Use Alternative Data Sources
You already have working scripts for other data sources:

1. **CheckWX API** (`fetch_checkwx_data.py`)
   - Requires free API key from https://www.checkwx.com/
   - 50 requests/day on free tier
   - Excellent reliability

2. **Aviation Weather** (export_wind_data.py original version)
   - Limited to 7 days of historical data
   - No API key required

### Option 3: Manual OGIMET Web Interface
Visit https://www.ogimet.com/ and manually download METAR data for GCGM.

## CSV Output Format
The export_wind_data.py script creates a CSV with:
- `datetime_local` - Canary Islands time (WET/WEST with DST)
- `datetime_utc` - UTC time
- `wind_direction` - Direction in degrees or VRB
- `sustained_speed_kt` - Sustained wind speed in knots
- `sustained_speed_kmh` - Sustained wind speed in km/h
- `gust_speed_kt` - Gust speed in knots (if present)
- `gust_speed_kmh` - Gust speed in km/h (if present)
- `metar` - Full METAR string

## Next Steps
1. Try running the script periodically to check if OGIMET becomes available
2. Consider using CheckWX API for reliable historical data
3. Check OGIMET's website for any announcements about API changes
