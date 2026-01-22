# OGIMET Manual Download Guide

## Step-by-Step Instructions

### Step 1: Open OGIMET in your browser

Click this link or copy it to your browser:
```
https://www.ogimet.com/display_metars2.php?lang=en
```

### Step 2: Enter Search Criteria

Fill in the form with these values:

**Station ICAO code or name:**
```
GCGM
```

**Date Range:**
- Start Date: `2024-01-01` (or any date you want)
- Start Time: `00:00`
- End Date: `2024-12-24` (today)
- End Time: `23:59`

**Important:** OGIMET only allows 31 days per request, so you'll need to:
- Request Jan 1-31
- Then Feb 1-28
- Then Mar 1-31
- etc.

**Format:** Select `Text format` or `Decoded format`

### Step 3: Submit and Download

1. Click **"Submit"** or **"Get METARs"** button
2. You'll see a page full of METAR reports
3. **Select all text** (Cmd+A on Mac, Ctrl+A on Windows)
4. **Copy** (Cmd+C or Ctrl+C)
5. **Paste** into a text file and save as `gcgm_metars_jan.txt`

### Step 4: Repeat for Each Month

Repeat Step 2-3 for each month:
- Save as: `gcgm_metars_jan.txt`
- Save as: `gcgm_metars_feb.txt`
- Save as: `gcgm_metars_mar.txt`
- ... and so on

### Step 5: Combine All Files

In your terminal, combine all files:

```bash
cd /Users/edu/claude/metar
cat gcgm_metars_*.txt > gcgm_all_metars.txt
```

### Step 6: Process the Data

Run the processing script:

```bash
python3 process_manual_metars.py gcgm_all_metars.txt
```

This will create `la_gomera_wind_data.json` with all your historical data!

### Step 7: View Your Visualization

```bash
./run_visualization.sh
```

Or open: http://localhost:8000/wind_visualization.html

---

## Alternative: Quick URLs for Each Month

Here are direct links for each month of 2024 (31-day chunks):

**January 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=01&day=01&hora=00&anof=2024&mesf=01&dayf=31&horaf=23&minf=59&send=send
```

**February 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=02&day=01&hora=00&anof=2024&mesf=02&dayf=29&horaf=23&minf=59&send=send
```

**March 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=03&day=01&hora=00&anof=2024&mesf=03&dayf=31&horaf=23&minf=59&send=send
```

**April 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=04&day=01&hora=00&anof=2024&mesf=04&dayf=30&horaf=23&minf=59&send=send
```

**May 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=05&day=01&hora=00&anof=2024&mesf=05&dayf=31&horaf=23&minf=59&send=send
```

**June 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=06&day=01&hora=00&anof=2024&mesf=06&dayf=30&horaf=23&minf=59&send=send
```

**July 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=07&day=01&hora=00&anof=2024&mesf=07&dayf=31&horaf=23&minf=59&send=send
```

**August 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=08&day=01&hora=00&anof=2024&mesf=08&dayf=31&horaf=23&minf=59&send=send
```

**September 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=09&day=01&hora=00&anof=2024&mesf=09&dayf=30&horaf=23&minf=59&send=send
```

**October 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=10&day=01&hora=00&anof=2024&mesf=10&dayf=31&horaf=23&minf=59&send=send
```

**November 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=11&day=01&hora=00&anof=2024&mesf=11&dayf=30&horaf=23&minf=59&send=send
```

**December 2024:**
```
https://www.ogimet.com/display_metars2.php?lang=en&lugar=GCGM&tipo=ALL&ord=REV&nil=SI&fmt=txt&ano=2024&mes=12&day=01&hora=00&anof=2024&mesf=12&dayf=24&horaf=23&minf=59&send=send
```

---

## Quick Process

1. Open each URL above in your browser
2. Copy all the METAR text
3. Paste into files: `jan.txt`, `feb.txt`, `mar.txt`, etc.
4. Combine: `cat *.txt > all_metars.txt`
5. Process: `python3 process_manual_metars.py all_metars.txt`
6. View: `./run_visualization.sh`

---

## Troubleshooting

**Q: I see "No data available" or empty pages**
A: OGIMET might not have comprehensive data for La Gomera (small airport). This is unfortunately common for smaller airports in their historical archive.

**Q: The dates I want don't work**
A: Remember the 31-day limit. Break your request into smaller chunks.

**Q: Can I automate this?**
A: OGIMET blocks most automation. Manual download is the most reliable method.
