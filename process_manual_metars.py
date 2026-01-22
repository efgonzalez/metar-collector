#!/usr/bin/env python3
"""
Process manually downloaded METAR data from OGIMET or other sources
Converts raw METAR text to our visualization format
"""

import re
import json
from datetime import datetime
import sys


def parse_wind_data(metar_text):
    """
    Parse wind information from METAR text
    """
    # Wind pattern: dddssGggKT or dddssKT
    wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KPH)'

    match = re.search(wind_pattern, metar_text)
    if not match:
        return None

    direction = match.group(1)
    speed = int(match.group(2))
    gust = int(match.group(3)) if match.group(3) else None
    unit = match.group(4)

    # Extract observation time (DDHHmmZ)
    time_pattern = r'\b(\d{6}Z)\b'
    time_match = re.search(time_pattern, metar_text)
    obs_time = time_match.group(1) if time_match else None

    # Extract year-month if present in METAR
    # Some formats include full date: YYYY/MM/DD HH:MM
    full_date_pattern = r'(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})'
    full_date_match = re.search(full_date_pattern, metar_text)

    parsed_datetime = None

    if full_date_match:
        # Full date format found
        year = int(full_date_match.group(1))
        month = int(full_date_match.group(2))
        day = int(full_date_match.group(3))
        hour = int(full_date_match.group(4))
        minute = int(full_date_match.group(5))

        try:
            parsed_datetime = datetime(year, month, day, hour, minute)
        except ValueError:
            pass

    elif obs_time:
        # Parse from DDHHmmZ format
        day = int(obs_time[0:2])
        hour = int(obs_time[2:4])
        minute = int(obs_time[4:6])

        # Try to infer year/month from context or use current
        now = datetime.utcnow()

        # Look for year in the METAR text
        year_match = re.search(r'\b(20\d{2})\b', metar_text)
        if year_match:
            year = int(year_match.group(1))
            # Try to find month
            month_match = re.search(r'\b(0[1-9]|1[0-2])\b', metar_text)
            if month_match:
                month = int(month_match.group(1))
            else:
                month = now.month
        else:
            # Default to current year/month with adjustment for day
            if day > now.day:
                if now.month == 1:
                    year = now.year - 1
                    month = 12
                else:
                    year = now.year
                    month = now.month - 1
            else:
                year = now.year
                month = now.month

        try:
            parsed_datetime = datetime(year, month, day, hour, minute)
        except ValueError:
            pass

    return {
        'metar': metar_text.strip(),
        'observation_time': obs_time,
        'datetime': parsed_datetime.isoformat() if parsed_datetime else None,
        'date': parsed_datetime.strftime('%Y-%m-%d') if parsed_datetime else None,
        'wind_direction': direction,
        'wind_speed': speed,
        'wind_gust': gust,
        'unit': unit,
        'timestamp': datetime.utcnow().isoformat()
    }


def extract_metars_from_text(text):
    """
    Extract METAR reports from raw text file
    Handles various OGIMET formats
    """
    metars = []

    # Split by lines first
    lines = text.split('\n')

    current_metar = []

    for line in lines:
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith('===') or line.startswith('---'):
            continue

        # Skip HTML tags
        if '<' in line and '>' in line:
            continue

        # Check if line contains GCGM and a date pattern
        if 'GCGM' in line or 'METAR' in line or re.search(r'\d{6}Z', line):
            # If we have accumulated a METAR, save it
            if current_metar and 'GCGM' in ' '.join(current_metar):
                metar_text = ' '.join(current_metar)
                metars.append(metar_text)
                current_metar = []

            current_metar.append(line)
        elif current_metar:
            # Continue accumulating lines for current METAR
            current_metar.append(line)

    # Don't forget the last METAR
    if current_metar and 'GCGM' in ' '.join(current_metar):
        metar_text = ' '.join(current_metar)
        metars.append(metar_text)

    # Clean up METARs
    cleaned_metars = []
    for metar in metars:
        # Remove multiple spaces
        metar = ' '.join(metar.split())

        # Must contain both GCGM and a time pattern
        if 'GCGM' in metar and re.search(r'\d{6}Z', metar):
            cleaned_metars.append(metar)

    # Remove duplicates while preserving order
    seen = set()
    unique_metars = []
    for metar in cleaned_metars:
        if metar not in seen:
            seen.add(metar)
            unique_metars.append(metar)

    return unique_metars


def process_metar_file(input_file, output_file='la_gomera_wind_data.json'):
    """
    Process a file containing raw METAR data
    """
    print("=" * 70)
    print("METAR Data Processor")
    print("=" * 70)
    print(f"Input file: {input_file}")
    print()

    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return

    print("Extracting METAR reports from file...")
    metars = extract_metars_from_text(text)

    print(f"✓ Found {len(metars)} METAR reports")
    print()

    if len(metars) == 0:
        print("⚠ No METAR reports found in file")
        print()
        print("Expected format examples:")
        print("  METAR GCGM 241630Z 24007KT 9999 FEW030 21/11 Q1015")
        print("  GCGM 241630Z 24007KT ...")
        return

    # Show sample
    print("Sample METARs found:")
    for i, metar in enumerate(metars[:3], 1):
        print(f"  {i}. {metar[:80]}...")
    print()

    print("Parsing wind data...")
    wind_data = []

    for metar in metars:
        parsed = parse_wind_data(metar)
        if parsed:
            wind_data.append(parsed)

    print(f"✓ Parsed {len(wind_data)} observations with wind data")
    print()

    if len(wind_data) == 0:
        print("⚠ No wind data could be parsed")
        return

    # Sort by datetime
    wind_data.sort(key=lambda x: x.get('datetime', '') if x.get('datetime') else 'zzz')

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(wind_data, f, indent=2)

    print(f"✓ Saved to {output_file}")
    print()

    # Display statistics
    speeds = [d['wind_speed'] for d in wind_data]
    gusts = [d['wind_gust'] for d in wind_data if d['wind_gust']]

    dates_with_data = [d['date'] for d in wind_data if d.get('date')]
    if dates_with_data:
        print("Wind Data Summary:")
        print(f"  Total observations: {len(wind_data)}")
        print(f"  Date range: {min(dates_with_data)} to {max(dates_with_data)}")
        print(f"  Avg wind speed: {sum(speeds)/len(speeds):.1f} kt")
        print(f"  Max wind speed: {max(speeds)} kt")
        if gusts:
            print(f"  Observations with gusts: {len(gusts)} ({len(gusts)/len(wind_data)*100:.1f}%)")
            print(f"  Max gust: {max(gusts)} kt")

    print()
    print("=" * 70)
    print("SUCCESS! Data ready for visualization")
    print("=" * 70)
    print()
    print("View your data:")
    print("  → Open: http://localhost:8000/wind_visualization.html")
    print("  (Make sure the local server is running)")


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("METAR Data Processor")
        print("=" * 70)
        print()
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <input_file>")
        print()
        print("Example:")
        print(f"  python3 {sys.argv[0]} gcgm_metars.txt")
        print()
        print("The input file should contain raw METAR data.")
        print("Supports various formats including OGIMET output.")
        return

    input_file = sys.argv[1]
    process_metar_file(input_file)


if __name__ == "__main__":
    main()
