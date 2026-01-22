#!/usr/bin/env python3
"""
Fetch multiple months of METAR data from OGIMET
by making multiple requests and combining them
"""

import requests
import time
import json
from datetime import datetime, timedelta
import re


def fetch_ogimet_day(station='GCGM'):
    """
    Fetch the default OGIMET data (last 24 hours)
    """
    url = "https://www.ogimet.com/display_metars2.php"
    params = {
        'lugar': station,
        'tipo': 'ALL',
        'ord': 'REV',
        'nil': 'SI',
        'fmt': 'txt'
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.text
    except:
        pass

    return None


def parse_wind_data(metar_text):
    """Parse wind information from METAR text"""
    wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KPH)'
    match = re.search(wind_pattern, metar_text)

    if not match:
        return None

    direction = match.group(1)
    speed = int(match.group(2))
    gust = int(match.group(3)) if match.group(3) else None
    unit = match.group(4)

    # Extract date/time from the METAR
    # Format: YYYYMMDDHHM M at start of line
    datetime_pattern = r'^(\d{12})\s+'
    datetime_match = re.search(datetime_pattern, metar_text)

    parsed_datetime = None
    obs_time = None

    if datetime_match:
        dt_str = datetime_match.group(1)
        try:
            year = int(dt_str[0:4])
            month = int(dt_str[4:6])
            day = int(dt_str[6:8])
            hour = int(dt_str[8:10])
            minute = int(dt_str[10:12])

            parsed_datetime = datetime(year, month, day, hour, minute)
            obs_time = f"{day:02d}{hour:02d}{minute:02d}Z"
        except:
            pass

    # Fallback: extract from DDHHmmZ pattern
    if not parsed_datetime:
        time_pattern = r'\b(\d{6}Z)\b'
        time_match = re.search(time_pattern, metar_text)

        if time_match:
            obs_time = time_match.group(1)
            day = int(obs_time[0:2])
            hour = int(obs_time[2:4])
            minute = int(obs_time[4:6])

            now = datetime.utcnow()
            if day > now.day:
                month = now.month - 1 if now.month > 1 else 12
                year = now.year if now.month > 1 else now.year - 1
            else:
                month = now.month
                year = now.year

            try:
                parsed_datetime = datetime(year, month, day, hour, minute)
            except:
                pass

    if not parsed_datetime:
        return None

    return {
        'metar': metar_text.strip(),
        'observation_time': obs_time,
        'datetime': parsed_datetime.isoformat(),
        'date': parsed_datetime.strftime('%Y-%m-%d'),
        'wind_direction': direction,
        'wind_speed': speed,
        'wind_gust': gust,
        'unit': unit,
        'timestamp': datetime.utcnow().isoformat()
    }


def extract_metars(text):
    """Extract METAR reports from OGIMET response"""
    metars = []

    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # Skip comments, headers, and empty lines
        if not line or line.startswith('#') or '<' in line:
            continue

        # Line starts with timestamp and contains GCGM
        if re.match(r'^\d{12}\s+METAR\s+GCGM', line):
            metars.append(line)

    return metars


def main():
    """
    Fetch OGIMET data
    Note: OGIMET only provides ~24 hours in the simple endpoint
    For more data, you need to download manually
    """

    print("=" * 70)
    print("OGIMET METAR Fetcher")
    print("=" * 70)
    print()
    print("Note: OGIMET's simple API only provides ~24 hours of data.")
    print("For longer periods, please use the manual download guide.")
    print()

    print("Fetching current OGIMET data...")

    text = fetch_ogimet_day('GCGM')

    if not text:
        print("✗ Failed to fetch data from OGIMET")
        return

    # Extract METARs
    metars = extract_metars(text)

    print(f"✓ Found {len(metars)} METAR reports")
    print()

    if len(metars) == 0:
        print("⚠ No METAR data available")
        print()
        print("This could mean:")
        print("  - OGIMET doesn't archive data for GCGM")
        print("  - The airport isn't reporting to OGIMET")
        print("  - Try the manual download guide instead")
        return

    # Parse wind data
    wind_data = []
    for metar in metars:
        parsed = parse_wind_data(metar)
        if parsed:
            wind_data.append(parsed)

    print(f"✓ Parsed {len(wind_data)} observations with wind data")
    print()

    if wind_data:
        # Sort by datetime
        wind_data.sort(key=lambda x: x['datetime'])

        # Save
        output_file = 'ogimet_wind_data.json'
        with open(output_file, 'w') as f:
            json.dump(wind_data, f, indent=2)

        print(f"✓ Saved to {output_file}")
        print()

        # Stats
        speeds = [d['wind_speed'] for d in wind_data]
        gusts = [d['wind_gust'] for d in wind_data if d['wind_gust']]

        print("Wind Data Summary:")
        print(f"  Date range: {wind_data[0]['date']} to {wind_data[-1]['date']}")
        print(f"  Total observations: {len(wind_data)}")
        print(f"  Avg wind speed: {sum(speeds)/len(speeds):.1f} kt")
        print(f"  Max wind speed: {max(speeds)} kt")
        if gusts:
            print(f"  Observations with gusts: {len(gusts)}")
            print(f"  Max gust: {max(gusts)} kt")

        print()
        print("=" * 70)
        print("To get this into your visualization:")
        print("=" * 70)
        print()
        print(f"  cp {output_file} la_gomera_wind_data.json")
        print("  ./run_visualization.sh")
        print()
        print("Or merge with existing data if you want to combine sources.")


if __name__ == "__main__":
    main()
