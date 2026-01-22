#!/usr/bin/env python3
"""
Fetch historical METAR data from OGIMET
OGIMET has excellent coverage for European/Canary Islands airports
"""

import requests
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict


def fetch_ogimet_metar(station='GCGM', start_date=None, end_date=None):
    """
    Fetch METAR data from OGIMET

    Args:
        station: ICAO code (default: GCGM for La Gomera)
        start_date: Start date as datetime or string 'YYYY-MM-DD'
        end_date: End date as datetime or string 'YYYY-MM-DD'

    Returns:
        List of METAR reports
    """

    # Default to last 12 months if not specified
    if end_date is None:
        end_date = datetime.utcnow()
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    if start_date is None:
        start_date = end_date - timedelta(days=365)  # 12 months
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

    print("=" * 70)
    print("OGIMET METAR Data Fetcher")
    print("=" * 70)
    print(f"Airport: {station} (La Gomera)")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Duration: {(end_date - start_date).days} days")
    print()

    # OGIMET URL format
    base_url = "https://www.ogimet.com/cgi-bin/getmetar"

    # Format dates for OGIMET (YYYYMMDDHH format)
    begin_str = start_date.strftime('%Y%m%d%H')
    end_str = end_date.strftime('%Y%m%d%H')

    params = {
        'begin': begin_str,
        'end': end_str,
        'station': station
    }

    all_metars = []

    # OGIMET has a limit, so we'll fetch in chunks if needed
    max_days_per_request = 31
    current_start = start_date

    while current_start < end_date:
        current_end = min(current_start + timedelta(days=max_days_per_request), end_date)

        chunk_begin = current_start.strftime('%Y%m%d%H')
        chunk_end = current_end.strftime('%Y%m%d%H')

        print(f"Fetching {current_start.date()} to {current_end.date()}...", end=' ')

        try:
            params = {
                'begin': chunk_begin,
                'end': chunk_end,
                'station': station
            }

            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            # Parse METAR reports from HTML
            metars = parse_ogimet_response(response.text)
            all_metars.extend(metars)

            print(f"✓ {len(metars)} reports")

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")

        current_start = current_end

    print()
    print(f"Total METAR reports fetched: {len(all_metars)}")

    return all_metars


def parse_ogimet_response(html_text):
    """
    Parse METAR reports from OGIMET HTML response
    """
    metars = []

    # OGIMET returns METAR in <pre> tags or plain text
    # Pattern: GCGM DDHHmmZ [rest of METAR]
    metar_pattern = r'(GCGM\s+\d{6}Z.*?)(?=GCGM\s+\d{6}Z|$)'

    matches = re.findall(metar_pattern, html_text, re.DOTALL)

    for match in matches:
        # Clean up the METAR text
        metar = ' '.join(match.split())
        if metar and 'GCGM' in metar:
            metars.append(metar)

    # If the above pattern doesn't work, try line-by-line
    if len(metars) == 0:
        lines = html_text.split('\n')
        for line in lines:
            if 'GCGM' in line and re.search(r'\d{6}Z', line):
                metar = ' '.join(line.split())
                if metar:
                    metars.append(metar)

    # Remove duplicates while preserving order
    seen = set()
    unique_metars = []
    for metar in metars:
        if metar not in seen:
            seen.add(metar)
            unique_metars.append(metar)

    return unique_metars


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

    # Parse datetime
    parsed_datetime = None
    if obs_time:
        day = int(obs_time[0:2])
        hour = int(obs_time[2:4])
        minute = int(obs_time[4:6])

        # Determine correct month/year
        now = datetime.utcnow()
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


def convert_to_json(metars, output_file='la_gomera_wind_data.json'):
    """
    Convert METAR reports to JSON format for visualization
    """
    print()
    print("Parsing wind data from METAR reports...")

    wind_data = []

    for metar in metars:
        parsed = parse_wind_data(metar)
        if parsed:
            wind_data.append(parsed)

    # Sort by datetime
    wind_data.sort(key=lambda x: x['datetime'] if x['datetime'] else '')

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(wind_data, f, indent=2)

    print(f"✓ Parsed {len(wind_data)} observations with wind data")
    print(f"✓ Saved to {output_file}")

    # Display statistics
    if wind_data:
        speeds = [d['wind_speed'] for d in wind_data]
        gusts = [d['wind_gust'] for d in wind_data if d['wind_gust']]

        print()
        print("Wind Data Summary:")
        print(f"  Total observations: {len(wind_data)}")
        print(f"  First: {wind_data[0]['date']}")
        print(f"  Last: {wind_data[-1]['date']}")
        print(f"  Avg wind speed: {sum(speeds)/len(speeds):.1f} kt")
        print(f"  Max wind speed: {max(speeds)} kt")
        if gusts:
            print(f"  Observations with gusts: {len(gusts)}")
            print(f"  Max gust: {max(gusts)} kt")

    return wind_data


def main():
    """
    Main function - fetch last 12 months of data
    """

    # You can customize these dates
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)  # 12 months

    # Fetch METAR reports
    metars = fetch_ogimet_metar(
        station='GCGM',
        start_date=start_date,
        end_date=end_date
    )

    if metars:
        # Convert to JSON
        wind_data = convert_to_json(metars)

        print()
        print("=" * 70)
        print("SUCCESS! Data ready for visualization")
        print("=" * 70)
        print()
        print("Next step: Open the visualization")
        print("  → Run: open http://localhost:8000/wind_visualization.html")
        print("  (Make sure the local server is running)")
    else:
        print()
        print("⚠ No data retrieved. OGIMET might be temporarily unavailable")
        print("  or the airport might not have data for this period.")


if __name__ == "__main__":
    main()
