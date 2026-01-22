# METAR Wind Data Visualization for Canary Islands Airports

This project fetches METAR wind data for airports in the Canary Islands and displays it in an interactive web visualization.

Supported airports:
- **La Gomera Airport** (ICAO: GCGM)
- **La Palma Airport** (ICAO: GCLA)

## Features

- 📊 **Interactive Charts**: Beautiful line and bar charts showing wind speed and gusts
- 📈 **Daily Aggregation**: Automatic calculation of min/max/avg values per day
- 🎨 **Modern UI**: Responsive design with gradient backgrounds and smooth animations
- 📱 **Mobile Friendly**: Works on all devices

## Quick Start

### One-Command Method (Easiest!)

Simply run the automated script:

```bash
./run_visualization.sh
```

This will:
- Create a virtual environment (if needed)
- Install dependencies
- Fetch the latest METAR data
- Start a local web server
- Open the visualization in your browser

Press `Ctrl+C` when done to stop the server.

### Manual Method

### 1. Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Fetch METAR Data

Run the Python script to fetch the latest data:

```bash
python export_wind_data.py
```

This will:
- Fetch up to 7 days of METAR data (API limitation)
- Parse wind information (direction, speed, gusts)
- Export to CSV, JSON, and daily aggregated JSON formats

### 3. View Visualization

Due to browser security restrictions (CORS), you need to serve the HTML file via a local web server:

```bash
# Start a local web server
python3 -m http.server 8000
```

Then open your browser and navigate to:
```
http://localhost:8000/wind_visualization.html
```

Alternatively, you can start the server in the background:

```bash
# Start server in background
python3 -m http.server 8000 &

# Open in browser (Mac)
open http://localhost:8000/wind_visualization.html

# Open in browser (Linux)
xdg-open http://localhost:8000/wind_visualization.html

# Open in browser (Windows)
start http://localhost:8000/wind_visualization.html
```

## Output Files

- **`la_gomera_wind_data.csv`** - All observations in CSV format
- **`la_gomera_wind_data.json`** - All observations in JSON format
- **`la_gomera_wind_daily.json`** - Daily aggregated data used by the visualization

## Collecting 12 Months of Data

**Important**: The Aviation Weather API only provides up to 7 days of historical METAR data. To collect 12 months of data, you need to run the script regularly:

### Option 1: Manual Collection

Run the script daily/weekly and merge the data:

```bash
# Run daily and it will append to your dataset
python export_wind_data.py
```

### Option 2: Automated Collection (Recommended)

Set up a cron job (Linux/Mac) to run daily:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * cd /path/to/metar && source venv/bin/activate && python export_wind_data.py
```

Or use Task Scheduler on Windows.

### Option 3: Use Historical Data Services

For immediate access to historical data, consider:
- **Iowa State ASOS Archive**: https://mesonet.agron.iastate.edu/request/download.phtml
- **OGIMET**: https://www.ogimet.com/
- **Aviation Weather Database**: Commercial services with historical METAR data

## Data Fields

### Raw Data (CSV/JSON)
- `observation_time` - Time of observation (DDHHmmZ format)
- `datetime` - Full ISO datetime
- `date` - Date (YYYY-MM-DD)
- `wind_direction` - Wind direction in degrees (or VRB for variable)
- `wind_speed` - Wind speed value
- `wind_gust` - Gust speed (if present)
- `unit` - Unit of measurement (KT=knots, MPS=meters/second)
- `timestamp` - When data was fetched
- `metar` - Full METAR report text

### Daily Aggregated Data
- `date` - Date (YYYY-MM-DD)
- `avg_speed` - Average wind speed for the day
- `max_speed` - Maximum wind speed for the day
- `min_speed` - Minimum wind speed for the day
- `avg_gust` - Average gust speed (when present)
- `max_gust` - Maximum gust speed
- `observations` - Number of METAR reports that day

## Visualization Features

The HTML page includes:

1. **Statistics Cards**: Quick overview of key metrics
   - Average wind speed across all observations
   - Maximum wind speed recorded
   - Maximum gust recorded
   - Total days and observations

2. **Hour-by-Hour Wind Speed & Gusts Chart**: Line chart showing:
   - Precise wind speed measurements for each observation (blue line with area fill)
   - Wind gust measurements when present (red triangular markers)
   - Interactive tooltips with exact time, speed, and direction
   - Time-based x-axis showing actual observation times

3. **Wind Direction Over Time Chart**: Scatter plot showing:
   - Wind direction changes hour by hour
   - Color-coded by wind speed intensity:
     - Green: Light winds (< 5 kt)
     - Blue: Moderate winds (5-9 kt)
     - Orange: Strong winds (10-14 kt)
     - Red: Very strong winds (≥ 15 kt)
   - Y-axis labeled with compass directions (N, NE, E, SE, S, SW, W, NW)

## Customization

### Change Airport

Edit `export_wind_data.py` line 178:

```python
extractor = METARWindExtractor("GCGM")  # Change ICAO code here
```

### Adjust Data Fetching

Edit line 183 to change hours fetched (max 168 for 7 days):

```python
metar_data = extractor.fetch_metar(hours=168)  # Adjust hours here
```

### Customize Chart Colors

Edit the `wind_visualization.html` file and modify the color values in the datasets:

```javascript
borderColor: '#3b82f6',  // Change colors here
backgroundColor: 'rgba(59, 130, 246, 0.1)',
```

## METAR Wind Format Reference

Wind is reported as: `dddssGggKT`
- `ddd` = direction in degrees (or VRB for variable)
- `ss` = speed (2-3 digits)
- `Ggg` = gust speed (optional, preceded by G)
- `KT` = knots

Examples:
- `27015G25KT` = wind from 270° at 15 knots, gusting to 25 knots
- `VRB05KT` = variable direction at 5 knots
- `36010KT` = wind from 360° (north) at 10 knots

## Troubleshooting

**Q: The HTML page shows "Error: Could not load wind data"**
A: Make sure you've run `python export_wind_data.py` first to generate the data files.

**Q: I see deprecation warnings about datetime**
A: These are harmless warnings. The script will continue to work.

**Q: The visualization only shows a few days**
A: The Aviation Weather API limits data to 7 days. For longer periods, you need to collect data over time.

**Q: Can I get data for multiple airports?**
A: Yes! Modify the script to use different ICAO codes and create separate visualizations.

## License

This project is open source and available for personal and educational use.
