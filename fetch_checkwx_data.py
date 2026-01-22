#!/usr/bin/env python3
"""
Fetch historical METAR data using CheckWX API
CheckWX has excellent coverage and reliability

Get your free API key at: https://www.checkwx.com/
Free tier: 50 requests/day, perfect for fetching historical data
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import time


def fetch_checkwx_metar(api_key, station='GCGM', days_back=30):
    """
    Fetch historical METAR data from CheckWX

    Args:
        api_key: Your CheckWX API key
        station: ICAO code (default: GCGM)
        days_back: How many days of history to fetch (default: 30)

    Returns:
        List of wind data records
    """

    print("=" * 70)
    print("CheckWX METAR Data Fetcher")
    print("=" * 70)
    print(f"Airport: {station} (La Gomera)")
    print(f"Fetching last {days_back} days of data")
    print()

    base_url = "https://api.checkwx.com/metar"
    headers = {
        'X-API-Key': api_key
    }

    all_wind_data = []

    # CheckWX allows fetching by date range
    # We'll fetch in chunks to stay within rate limits
    end_date = datetime.utcnow()

    # Calculate how many chunks we need (fetch 7 days at a time)
    chunk_size = 7
    num_chunks = (days_back + chunk_size - 1) // chunk_size

    print(f"Will fetch data in {num_chunks} chunks...")
    print()

    for i in range(num_chunks):
        chunk_end = end_date - timedelta(days=i * chunk_size)
        chunk_start = chunk_end - timedelta(days=chunk_size)

        # Don't go back further than requested
        if (end_date - chunk_start).days > days_back:
            chunk_start = end_date - timedelta(days=days_back)

        start_str = chunk_start.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = chunk_end.strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"Chunk {i+1}/{num_chunks}: {chunk_start.date()} to {chunk_end.date()}...", end=' ')

        try:
            # CheckWX URL format
            url = f"{base_url}/{station}/{start_str}/{end_str}"

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if data.get('results') and data.get('results') > 0:
                    metars = data.get('data', [])

                    # Parse each METAR
                    for metar_text in metars:
                        wind_record = parse_checkwx_metar(metar_text)
                        if wind_record:
                            all_wind_data.append(wind_record)

                    print(f"✓ {len(metars)} reports")
                else:
                    print("✓ No reports")

            elif response.status_code == 401:
                print("✗ Invalid API key")
                print("\nGet your free API key at: https://www.checkwx.com/")
                return None

            elif response.status_code == 429:
                print("✗ Rate limit exceeded")
                print("Free tier allows 50 requests/day. Try again tomorrow.")
                return None

            else:
                print(f"✗ HTTP {response.status_code}")

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")

        # Be nice to the API - small delay between requests
        if i < num_chunks - 1:
            time.sleep(1)

    print()
    print(f"Total observations fetched: {len(all_wind_data)}")

    return all_wind_data


def parse_checkwx_metar(metar_text):
    """
    Parse wind data from METAR text
    """
    import re

    if not metar_text:
        return None

    # Wind pattern
    wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS)'

    match = re.search(wind_pattern, metar_text)
    if not match:
        return None

    direction = match.group(1)
    speed = int(match.group(2))
    gust = int(match.group(3)) if match.group(3) else None
    unit = match.group(4)

    # Extract observation time
    time_pattern = r'\b(\d{6}Z)\b'
    time_match = re.search(time_pattern, metar_text)
    obs_time = time_match.group(1) if time_match else None

    # Parse datetime
    parsed_datetime = None
    if obs_time:
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


def save_to_json(wind_data, output_file='la_gomera_wind_data.json'):
    """
    Save wind data to JSON file
    """
    if not wind_data:
        print("No wind data to save")
        return

    # Sort by datetime
    wind_data.sort(key=lambda x: x.get('datetime', ''))

    # Save
    with open(output_file, 'w') as f:
        json.dump(wind_data, f, indent=2)

    print(f"✓ Saved {len(wind_data)} observations to {output_file}")

    # Display stats
    speeds = [d['wind_speed'] for d in wind_data]
    gusts = [d['wind_gust'] for d in wind_data if d['wind_gust']]

    print()
    print("Wind Data Summary:")
    print(f"  First observation: {wind_data[0]['date']}")
    print(f"  Last observation:  {wind_data[-1]['date']}")
    print(f"  Avg wind speed: {sum(speeds)/len(speeds):.1f} kt")
    print(f"  Max wind speed: {max(speeds)} kt")
    if gusts:
        print(f"  Observations with gusts: {len(gusts)}")
        print(f"  Max gust: {max(gusts)} kt")


def main():
    """
    Main function
    """

    if len(sys.argv) < 2:
        print("=" * 70)
        print("CheckWX METAR Data Fetcher")
        print("=" * 70)
        print()
        print("Usage:")
        print(f"  python3 {sys.argv[0]} YOUR_API_KEY [days_back]")
        print()
        print("Example:")
        print(f"  python3 {sys.argv[0]} abc123xyz456 365")
        print()
        print("Get your FREE API key at: https://www.checkwx.com/")
        print("  - Sign up (free)")
        print("  - Go to your dashboard")
        print("  - Copy your API key")
        print()
        print("Optional:")
        print("  days_back: Number of days of history (default: 30)")
        print("             Free tier works well up to ~365 days")
        return

    api_key = sys.argv[1]
    days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    # Fetch data
    wind_data = fetch_checkwx_metar(
        api_key=api_key,
        station='GCGM',
        days_back=days_back
    )

    if wind_data:
        # Save to file
        save_to_json(wind_data)

        print()
        print("=" * 70)
        print("SUCCESS! Data ready for visualization")
        print("=" * 70)
        print()
        print("Next: View your data")
        print("  → Run: ./run_visualization.sh")
        print("  → Or open: http://localhost:8000/wind_visualization.html")


if __name__ == "__main__":
    main()
