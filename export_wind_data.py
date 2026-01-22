#!/usr/bin/env python3
"""
Export wind data from METAR information for La Gomera Airport (GCGM)
Fetches data from OGIMET for the year 2025 with Canary Islands local time
"""

import requests
import csv
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import defaultdict
import re
import pytz


class METARWindExtractor:
    """Extract wind data from METAR reports"""

    def __init__(self, icao_code: str = "GCGM", synop_block: str = "60007"):
        self.icao_code = icao_code
        self.synop_block = synop_block  # GCGM synop code is 60007
        self.base_url = "http://www.ogimet.com/cgi-bin/getsynop"

    def fetch_metar(self, start_date: datetime, end_date: datetime) -> List[tuple]:
        """
        Fetch SYNOP data from OGIMET (contains wind information)

        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            List of tuples (synop_line, year, month)
        """
        all_data = []
        max_days_per_request = 31  # Fetch one month at a time
        current_start = start_date

        print(f"Fetching SYNOP data for {self.icao_code} (block {self.synop_block}) from {start_date.date()} to {end_date.date()}")
        print(f"Note: OGIMET rate limit is 1 request per 20 seconds")
        print()

        request_count = 0
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=max_days_per_request), end_date)

            print(f"  Fetching {current_start.date()} to {current_end.date()}...", end=' ')

            # Rate limiting: wait 21 seconds between requests (OGIMET limit is 20s)
            if request_count > 0:
                print("(waiting 21s for rate limit)...", end=' ')
                time.sleep(21)

            try:
                # Format: YYYYMMDDHHMM
                begin_str = current_start.strftime('%Y%m%d%H%M')
                end_str = current_end.strftime('%Y%m%d%H%M')

                params = {
                    'begin': begin_str,
                    'end': end_str,
                    'block': self.synop_block
                }

                response = requests.get(self.base_url, params=params, timeout=30)

                # Check for rate limiting
                if 'quota limit' in response.text.lower():
                    print("Rate limit hit, waiting 30s...")
                    time.sleep(30)
                    response = requests.get(self.base_url, params=params, timeout=30)

                response.raise_for_status()

                synop_lines = self._parse_synop_response(response.text)

                # Tag each line with year and month
                for line in synop_lines:
                    all_data.append((line, current_start.year, current_start.month))

                print(f"✓ {len(synop_lines)} observations")
                request_count += 1

            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")

            current_start = current_end

        print()
        print(f"Total observations fetched: {len(all_data)}")
        return all_data

    def _parse_synop_response(self, text: str) -> List[Dict]:
        """
        Parse SYNOP data from OGIMET response

        Format: block,year,month,day,hour,minute,synop_message
        Example: 60007,2025,01,01,06,00,AAXX 01064 60007 02/// /1105 10163...

        Returns list of dictionaries with parsed data
        """
        synop_observations = []
        lines = text.split('\n')

        for line in lines:
            if not line.strip() or line.startswith('Status:'):
                continue

            parts = line.split(',', 6)
            if len(parts) >= 7 and parts[0] == self.synop_block:
                try:
                    obs = {
                        'block': parts[0],
                        'year': int(parts[1]),
                        'month': int(parts[2]),
                        'day': int(parts[3]),
                        'hour': int(parts[4]),
                        'minute': int(parts[5]),
                        'synop': parts[6].strip()
                    }

                    # Skip NIL reports
                    if 'NIL' not in obs['synop']:
                        synop_observations.append(obs)
                except (ValueError, IndexError):
                    continue

        return synop_observations

    def parse_wind_data(self, synop_obs: Dict, year: int, month: int) -> Optional[Dict]:
        """
        Parse wind information from SYNOP observation

        SYNOP Format: AAXX YYGGiw IIiii iihVV Nddff 1sTTT 2sTTT... 333 [Section 3 groups]

        Where:
        - iihVV: ii=precipitation indicator, h=wind unit (0=calm, 1=m/s, 3=kt estimated, 4=kt measured)
        - Nddff or /ddff: N=cloud cover (or / if vis missing), dd=wind dir (tens of degrees), ff=wind speed
        - Section 3 may contain:
          - 910ff: Max wind gust in last 10 min
          - 911ff: Max wind gust in last hour

        Example: AAXX 01064 60007 02/// /1105 10163...
        - 02///: surface obs, wind in knots, visibility missing
        - /1105: wind from 110° at 5 kt
        """
        synop_text = synop_obs['synop']
        groups = synop_text.split()

        # Find station ID position
        station_idx = -1
        for i, group in enumerate(groups):
            if group == self.synop_block:
                station_idx = i
                break

        if station_idx == -1:
            return None

        # Determine wind unit from iihVV group (first group after station)
        wind_unit_code = None
        if station_idx + 1 < len(groups):
            iihvv_group = groups[station_idx + 1]
            if len(iihvv_group) >= 2 and iihvv_group[1].isdigit():
                wind_unit_code = int(iihvv_group[1])

        # Decode wind unit: 0=calm, 1=m/s, 3=kt estimated, 4=kt measured
        wind_in_mps = (wind_unit_code == 1)
        wind_unit = 'MPS' if wind_in_mps else 'KT'

        # Parse wind direction and speed from Nddff or /ddff group
        wind_direction = None
        wind_speed = None

        # Wind group is the FIRST group after station ID (after iihVV)
        # Two possible formats:
        # 1. /ddff - visibility missing, wind direction/speed
        # 2. Nddff - cloud cover N, wind direction/speed

        # The wind group should be at position station_idx + 2 (after station block and iihVV)
        if station_idx + 2 < len(groups):
            wind_group = groups[station_idx + 2]

            # Format 1: /ddff (visibility missing)
            if wind_group.startswith('/') and len(wind_group) == 5:
                try:
                    wind_part = wind_group[1:]  # Remove leading /
                    dir_tens = int(wind_part[0:2])
                    speed = int(wind_part[2:4])
                    if 0 <= dir_tens <= 36 and 0 <= speed <= 99:
                        wind_direction = dir_tens * 10 if dir_tens > 0 else 0
                        wind_speed = speed
                except ValueError:
                    pass

            # Format 2: Nddff (cloud cover present)
            elif len(wind_group) == 5 and wind_group.isdigit():
                try:
                    cloud_cover = int(wind_group[0])
                    dir_tens = int(wind_group[1:3])
                    speed = int(wind_group[3:5])
                    # Validate: cloud cover 0-9, direction 00-36 (in tens), speed 00-99
                    if 0 <= cloud_cover <= 9 and 0 <= dir_tens <= 36 and 0 <= speed <= 99:
                        wind_direction = dir_tens * 10 if dir_tens > 0 else 0
                        wind_speed = speed
                except ValueError:
                    pass

        if wind_direction is None or wind_speed is None:
            return None

        # Look for wind gust in Section 3 (after "333" group)
        wind_gust = None
        try:
            section3_idx = groups.index('333')
            # Look for gust groups: 910ff (10-min max) or 911ff (1-hr max)
            for i in range(section3_idx + 1, len(groups)):
                group = groups[i]
                if len(group) == 5 and group.startswith('91'):
                    gust_type = group[2]  # 0=10min, 1=1hr
                    gust_value = int(group[3:5])
                    if 0 <= gust_value <= 99:
                        wind_gust = gust_value
                        break
        except (ValueError, IndexError):
            pass  # Section 3 not found or no gust data

        # Create UTC datetime from observation
        try:
            utc_tz = pytz.UTC
            parsed_datetime_utc = utc_tz.localize(datetime(
                synop_obs['year'],
                synop_obs['month'],
                synop_obs['day'],
                synop_obs['hour'],
                synop_obs['minute']
            ))

            # Convert to Canary Islands time
            canary_tz = pytz.timezone('Atlantic/Canary')
            parsed_datetime_canary = parsed_datetime_utc.astimezone(canary_tz)

        except ValueError:
            return None

        # Convert to knots and km/h based on wind unit
        if wind_in_mps:
            # Convert m/s to knots (1 m/s = 1.94384 kt)
            speed_kt = round(wind_speed * 1.94384, 1)
            gust_kt = round(wind_gust * 1.94384, 1) if wind_gust else None
        else:
            # Already in knots
            speed_kt = wind_speed
            gust_kt = wind_gust

        # Convert to km/h (1 knot = 1.852 km/h)
        speed_kmh = round(speed_kt * 1.852, 1)
        gust_kmh = round(gust_kt * 1.852, 1) if gust_kt else None

        return {
            'synop': synop_text,
            'datetime_utc': parsed_datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'datetime_local': parsed_datetime_canary.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'wind_direction': wind_direction if wind_direction != 0 else 'VRB',
            'sustained_speed_kt': speed_kt,
            'sustained_speed_kmh': speed_kmh,
            'gust_speed_kt': gust_kt,
            'gust_speed_kmh': gust_kmh,
            'unit': wind_unit
        }

    def export_to_csv(self, wind_data: List[Dict], filename: str = 'wind_data.csv'):
        """Export wind data to CSV file"""
        if not wind_data:
            print("No wind data to export")
            return

        fieldnames = ['datetime_local', 'datetime_utc', 'wind_direction',
                      'sustained_speed_kt', 'sustained_speed_kmh',
                      'gust_speed_kt', 'gust_speed_kmh', 'unit', 'synop']

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(wind_data)

        print(f"Exported {len(wind_data)} records to {filename}")

    def export_to_json(self, wind_data: List[Dict], filename: str = 'wind_data.json'):
        """Export wind data to JSON file"""
        if not wind_data:
            print("No wind data to export")
            return

        with open(filename, 'w') as jsonfile:
            json.dump(wind_data, jsonfile, indent=2)

        print(f"Exported {len(wind_data)} records to {filename}")


def aggregate_by_day(wind_data: List[Dict]) -> List[Dict]:
    """Aggregate wind data by day with min/max/avg values"""
    daily_data = defaultdict(lambda: {
        'speeds': [],
        'gusts': [],
        'dates': []
    })

    for record in wind_data:
        if record.get('date'):
            date = record['date']
            daily_data[date]['speeds'].append(record['wind_speed'])
            if record['wind_gust']:
                daily_data[date]['gusts'].append(record['wind_gust'])

    aggregated = []
    for date in sorted(daily_data.keys()):
        data = daily_data[date]
        speeds = data['speeds']
        gusts = data['gusts']

        aggregated.append({
            'date': date,
            'avg_speed': round(sum(speeds) / len(speeds), 1) if speeds else 0,
            'max_speed': max(speeds) if speeds else 0,
            'min_speed': min(speeds) if speeds else 0,
            'avg_gust': round(sum(gusts) / len(gusts), 1) if gusts else None,
            'max_gust': max(gusts) if gusts else None,
            'observations': len(speeds)
        })

    return aggregated


def main():
    """Main execution function"""
    print("=" * 70)
    print("GCGM Wind Data Exporter - Year 2025 (SYNOP)")
    print("=" * 70)
    print()

    extractor = METARWindExtractor("GCGM", synop_block="60007")

    # Fetch data for the entire year 2025
    start_date = datetime(2025, 1, 1, 0, 0)
    end_date = datetime(2025, 12, 31, 23, 59)

    synop_data = extractor.fetch_metar(start_date, end_date)

    if not synop_data:
        print("Failed to fetch SYNOP data")
        return

    print(f"\nParsing wind data from {len(synop_data)} observations...")

    # Parse wind data from each SYNOP observation
    wind_data = []
    for synop_obs, year, month in synop_data:
        parsed = extractor.parse_wind_data(synop_obs, year, month)
        if parsed and parsed.get('datetime_utc'):
            wind_data.append(parsed)

    if not wind_data:
        print("No wind data found in SYNOP observations")
        return

    # Sort by datetime
    wind_data.sort(key=lambda x: x['datetime_utc'] if x['datetime_utc'] else '')

    # Remove duplicates based on datetime
    seen_datetimes = set()
    unique_wind_data = []
    for record in wind_data:
        dt = record['datetime_utc']
        if dt and dt not in seen_datetimes:
            seen_datetimes.add(dt)
            unique_wind_data.append(record)

    print(f"Parsed {len(unique_wind_data)} unique observations with wind data")

    # Display statistics
    if unique_wind_data:
        speeds = [d['sustained_speed_kt'] for d in unique_wind_data if d['sustained_speed_kt']]
        gusts = [d['gust_speed_kt'] for d in unique_wind_data if d['gust_speed_kt']]

        print()
        print("Wind Data Summary:")
        print(f"  Total observations: {len(unique_wind_data)}")
        if unique_wind_data[0]['datetime_local']:
            print(f"  First: {unique_wind_data[0]['datetime_local']}")
            print(f"  Last: {unique_wind_data[-1]['datetime_local']}")
        if speeds:
            print(f"  Avg sustained wind: {sum(speeds)/len(speeds):.1f} kt ({sum(speeds)/len(speeds)*1.852:.1f} km/h)")
            print(f"  Max sustained wind: {max(speeds)} kt ({max(speeds)*1.852:.1f} km/h)")
            print(f"  Min sustained wind: {min(speeds)} kt ({min(speeds)*1.852:.1f} km/h)")
        if gusts:
            print(f"  Observations with gusts: {len(gusts)}")
            print(f"  Max gust: {max(gusts)} kt ({max(gusts)*1.852:.1f} km/h)")
            print(f"  Avg gust: {sum(gusts)/len(gusts):.1f} kt ({sum(gusts)/len(gusts)*1.852:.1f} km/h)")

    # Export to CSV
    output_filename = 'gcgm_wind_data_2025.csv'
    extractor.export_to_csv(unique_wind_data, output_filename)

    print()
    print("=" * 70)
    print("Export complete!")
    print("=" * 70)
    print()
    print(f"Note: SYNOP observations are typically every 3 hours (00, 03, 06, 09, 12, 15, 18, 21 UTC)")
    print(f"      Wind gusts are included when available in Section 3 (groups 910/911)")


if __name__ == "__main__":
    main()
