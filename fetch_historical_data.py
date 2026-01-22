#!/usr/bin/env python3
"""
Fetch historical METAR data from Iowa State ASOS Archive
This can get months or years of data for La Gomera Airport
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json

def fetch_iowa_state_metar(station='GCGM', start_date=None, end_date=None):
    """
    Fetch historical METAR data from Iowa State ASOS Archive

    Args:
        station: ICAO code (default: GCGM for La Gomera)
        start_date: Start date as datetime or string 'YYYY-MM-DD'
        end_date: End date as datetime or string 'YYYY-MM-DD'

    Returns:
        DataFrame with METAR data
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

    print(f"Fetching METAR data for {station}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Duration: {(end_date - start_date).days} days")
    print()

    # Iowa State ASOS Archive API
    base_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

    params = {
        'station': station,
        'data': 'all',  # Get all available data
        'year1': start_date.year,
        'month1': start_date.month,
        'day1': start_date.day,
        'year2': end_date.year,
        'month2': end_date.month,
        'day2': end_date.day,
        'tz': 'Etc/UTC',
        'format': 'onlycomma',  # CSV format
        'latlon': 'no',
        'elev': 'no',
        'missing': 'null',
        'trace': 'null',
        'direct': 'no',
        'report_type': '3'  # METAR only
    }

    try:
        print("Downloading data from Iowa State ASOS Archive...")
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()

        # Save raw CSV
        csv_file = f'{station}_historical_{start_date.date()}_to_{end_date.date()}.csv'
        with open(csv_file, 'w') as f:
            f.write(response.text)

        print(f"✓ Downloaded raw data to {csv_file}")

        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), low_memory=False)

        print(f"✓ Found {len(df)} observations")
        print()

        # Display summary
        if len(df) > 0:
            print("Data Summary:")
            print(f"  First observation: {df['valid'].iloc[0] if 'valid' in df else 'Unknown'}")
            print(f"  Last observation:  {df['valid'].iloc[-1] if 'valid' in df else 'Unknown'}")

            # Check for wind data
            if 'drct' in df and 'sknt' in df:
                wind_obs = df[df['sknt'].notna()]
                print(f"  Wind observations: {len(wind_obs)} ({len(wind_obs)/len(df)*100:.1f}%)")
                print(f"  Avg wind speed: {wind_obs['sknt'].mean():.1f} kt")
                print(f"  Max wind speed: {wind_obs['sknt'].max():.0f} kt")

                if 'gust' in df:
                    gust_obs = df[df['gust'].notna()]
                    print(f"  Gust observations: {len(gust_obs)} ({len(gust_obs)/len(df)*100:.1f}%)")
                    if len(gust_obs) > 0:
                        print(f"  Max gust: {gust_obs['gust'].max():.0f} kt")

        return df

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return None


def convert_to_visualization_format(df, output_file='la_gomera_wind_data.json'):
    """
    Convert Iowa State data to the format expected by our visualization
    """

    if df is None or len(df) == 0:
        print("No data to convert")
        return

    print()
    print("Converting to visualization format...")

    data = []
    for idx, row in df.iterrows():
        try:
            # Parse timestamp
            obs_time = pd.to_datetime(row['valid'])

            # Get wind data (Iowa State uses 'drct' for direction, 'sknt' for speed knots)
            direction = row.get('drct')
            speed = row.get('sknt')
            gust = row.get('gust')

            # Skip if no wind data
            if pd.isna(speed):
                continue

            # Format direction
            if pd.isna(direction) or direction == 0:
                direction_str = 'VRB'
            else:
                direction_str = f"{int(direction):03d}"

            record = {
                'observation_time': obs_time.strftime('%d%H%MZ'),
                'datetime': obs_time.isoformat(),
                'date': obs_time.strftime('%Y-%m-%d'),
                'wind_direction': direction_str,
                'wind_speed': int(speed),
                'wind_gust': int(gust) if pd.notna(gust) else None,
                'unit': 'KT',
                'timestamp': datetime.utcnow().isoformat(),
                'metar': row.get('metar', '')
            }

            data.append(record)

        except Exception as e:
            # Skip problematic rows
            continue

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Converted {len(data)} observations to {output_file}")
    print()
    print("✓ Ready to visualize! Open wind_visualization.html in your browser")

    return data


def main():
    """
    Fetch last 12 months of data for La Gomera Airport
    """

    print("=" * 70)
    print("METAR Historical Data Fetcher - Iowa State ASOS Archive")
    print("=" * 70)
    print()

    # Fetch last 12 months
    df = fetch_iowa_state_metar(
        station='GCGM',
        start_date=datetime.utcnow() - timedelta(days=365),
        end_date=datetime.utcnow()
    )

    if df is not None:
        # Convert to our visualization format
        convert_to_visualization_format(df)

        print()
        print("=" * 70)
        print("Done! You can now view the visualization with 12 months of data.")
        print("=" * 70)


if __name__ == "__main__":
    main()
