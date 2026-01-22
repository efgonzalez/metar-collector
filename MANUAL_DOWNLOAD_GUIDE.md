# Manual Download Guide - Getting 12 Months of Wind Data

Since automated fetching from OGIMET/Iowa State can be hit-or-miss for smaller airports like La Gomera, here's a **reliable manual approach** that takes just 5-10 minutes:

## Option 1: OGIMET Manual Download (Best for European airports)

### Step 1: Visit OGIMET
Go to: **https://www.ogimet.com/metars.phtml.en**

### Step 2: Search for La Gomera
1. In the search box, enter: `GCGM` (La Gomera ICAO code)
2. Or search by name: "La Gomera"

### Step 3: Select Date Range
1. Choose start date (e.g., 12 months ago)
2. Choose end date (today)
3. Select "Text format" or "Decoded format"

### Step 4: Download
1. Click "Get METARs"
2. Copy all the text
3. Save to a file: `gcgm_metars.txt`

### Step 5: Process the Data
Run this command in your terminal:

```bash
python3 process_manual_metars.py gcgm_metars.txt
```

This will convert the METAR data to our visualization format.

---

## Option 2: CheckWX API (Most Reliable)

CheckWX has excellent coverage and is free for personal use.

### Step 1: Get API Key
1. Visit: **https://www.checkwx.com/**
2. Click "Sign Up" (free account)
3. Get your API key from your dashboard

### Step 2: Use the Script

```bash
python3 fetch_checkwx_data.py YOUR_API_KEY_HERE
```

This will fetch up to 12 months of data automatically.

---

## Option 3: Continue with Current 8-Day Data

The visualization already works perfectly with 8 days of data!

**For a full 12-month dataset:**
Set up daily data collection:

```bash
# Add to crontab (run daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * cd /Users/edu/claude/metar && ./run_visualization.sh >> cron.log 2>&1
```

After 12 months, you'll have a complete year of data!

---

## Quick Comparison

| Method | Time | Data Coverage | Difficulty |
|--------|------|---------------|------------|
| **Current (8 days)** | 0 min | Excellent | ✅ Easy |
| **OGIMET Manual** | 5-10 min | Good | ⚠️ Medium |
| **CheckWX API** | 2 min | Excellent | ✅ Easy |
| **Daily Collection** | 1 min setup | Perfect (over time) | ✅ Easy |

---

## My Recommendation

**Start with what you have** (8 days of perfect data), then either:

1. **Set up daily collection** for future data
2. **Use CheckWX API** if you need historical data now

The current visualization shows hour-by-hour wind patterns beautifully with the 8 days you have!
