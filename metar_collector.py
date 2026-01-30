#!/usr/bin/env python3
"""
METAR Data Collector Service
Fetches and stores METAR data in SQLite database with duplicate prevention

Supported airports:
- GCGM: La Gomera Airport
- GCLA: La Palma Airport
- KROW: Roswell Air Center
"""

import sqlite3
import requests
import sys
import os
import logging
from datetime import datetime, timedelta
import time
import re
from pathlib import Path


# Configuration
STATIONS = ['GCGM', 'GCLA', 'KROW']  # La Gomera, La Palma, Roswell
DB_PATH = 'metar_data.db'
HOURS_TO_FETCH = 48  # Fetch last 48 hours with overlap to ensure no gaps
LOG_LEVEL = logging.INFO


# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('metar_collector.log')
    ]
)
logger = logging.getLogger(__name__)


class METARCollector:
    def __init__(self, api_key, station, db_path=DB_PATH):
        self.api_key = api_key
        self.station = station
        self.db_path = db_path
        self.base_url = "https://api.checkwx.com/metar"
        self.headers = {'X-API-Key': api_key}

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metar_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station TEXT NOT NULL,
                observation_time TEXT NOT NULL,
                datetime TEXT NOT NULL,
                date TEXT NOT NULL,
                wind_direction TEXT,
                wind_speed INTEGER,
                wind_gust INTEGER,
                unit TEXT,
                metar_text TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                UNIQUE(station, observation_time, datetime)
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_station_date
            ON metar_observations(station, date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_datetime
            ON metar_observations(datetime)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def fetch_metar_data(self, hours_back=HOURS_TO_FETCH):
        """Fetch METAR data from CheckWX API"""
        # CheckWX free API only returns the latest METAR
        # Historical data collection happens over time with scheduled runs
        url = f"{self.base_url}/{self.station}"

        logger.info(f"Fetching current METAR data for {self.station}")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if data.get('results', 0) > 0:
                    metars = data.get('data', [])
                    logger.info(f"Fetched {len(metars)} METAR reports")
                    return metars
                else:
                    logger.warning("No METAR reports found in response")
                    return []

            elif response.status_code == 401:
                logger.error("Invalid API key - check your CheckWX credentials")
                return None

            elif response.status_code == 429:
                logger.error("Rate limit exceeded - try again later")
                return None

            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching METAR data: {str(e)}")
            return None

    def parse_metar(self, metar_text):
        """Parse METAR text and extract wind data"""
        if not metar_text:
            return None

        # Wind pattern: direction(3 digits or VRB) + speed + optional gust + unit
        wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?(KT|MPS)'
        wind_match = re.search(wind_pattern, metar_text)

        # Time pattern: DDHHmmZ
        time_pattern = r'\b(\d{6}Z)\b'
        time_match = re.search(time_pattern, metar_text)

        if not wind_match or not time_match:
            logger.debug(f"Could not parse METAR: {metar_text}")
            return None

        direction = wind_match.group(1)
        speed = int(wind_match.group(2))
        gust = int(wind_match.group(3)) if wind_match.group(3) else None
        unit = wind_match.group(4)
        obs_time = time_match.group(1)

        # Parse datetime from observation time
        parsed_datetime = self._parse_obs_datetime(obs_time)
        if not parsed_datetime:
            logger.debug(f"Could not parse datetime from: {obs_time}")
            return None

        return {
            'station': self.station,
            'observation_time': obs_time,
            'datetime': parsed_datetime.isoformat(),
            'date': parsed_datetime.strftime('%Y-%m-%d'),
            'wind_direction': direction,
            'wind_speed': speed,
            'wind_gust': gust,
            'unit': unit,
            'metar_text': metar_text.strip(),
            'fetched_at': datetime.utcnow().isoformat()
        }

    def _parse_obs_datetime(self, obs_time):
        """Parse observation time (DDHHmmZ) to datetime"""
        try:
            day = int(obs_time[0:2])
            hour = int(obs_time[2:4])
            minute = int(obs_time[4:6])

            now = datetime.utcnow()

            # Handle month rollover
            if day > now.day:
                if now.month > 1:
                    month = now.month - 1
                    year = now.year
                else:
                    month = 12
                    year = now.year - 1
            else:
                month = now.month
                year = now.year

            return datetime(year, month, day, hour, minute)

        except (ValueError, IndexError) as e:
            logger.debug(f"Error parsing observation time {obs_time}: {e}")
            return None

    def store_observations(self, observations):
        """Store observations in database (preventing duplicates)"""
        if not observations:
            logger.info("No observations to store")
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        new_count = 0
        duplicate_count = 0

        for obs in observations:
            try:
                cursor.execute('''
                    INSERT INTO metar_observations
                    (station, observation_time, datetime, date, wind_direction,
                     wind_speed, wind_gust, unit, metar_text, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    obs['station'],
                    obs['observation_time'],
                    obs['datetime'],
                    obs['date'],
                    obs['wind_direction'],
                    obs['wind_speed'],
                    obs['wind_gust'],
                    obs['unit'],
                    obs['metar_text'],
                    obs['fetched_at']
                ))
                new_count += 1

            except sqlite3.IntegrityError:
                # Duplicate - already exists
                duplicate_count += 1

        conn.commit()
        conn.close()

        logger.info(f"Stored {new_count} new observations, {duplicate_count} duplicates skipped")
        return new_count

    def get_database_stats(self):
        """Get statistics about stored data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM metar_observations WHERE station = ?', (self.station,))
        total_count = cursor.fetchone()[0]

        cursor.execute('''
            SELECT MIN(date), MAX(date)
            FROM metar_observations
            WHERE station = ?
        ''', (self.station,))
        date_range = cursor.fetchone()

        conn.close()

        return {
            'total_observations': total_count,
            'earliest_date': date_range[0],
            'latest_date': date_range[1]
        }

    def run(self):
        """Main execution - fetch and store data"""
        logger.info(f"Starting METAR collection for {self.station}")

        # Fetch data
        metars = self.fetch_metar_data()

        if metars is None:
            logger.error("Failed to fetch METAR data")
            return False

        if not metars:
            logger.warning("No METAR data available")
            return True

        # Parse observations
        observations = []
        for metar_text in metars:
            obs = self.parse_metar(metar_text)
            if obs:
                observations.append(obs)

        logger.info(f"Parsed {len(observations)} valid observations from {len(metars)} reports")

        # Store in database
        new_count = self.store_observations(observations)

        # Show stats
        stats = self.get_database_stats()
        logger.info(f"Database statistics: {stats}")

        logger.info("METAR collection completed successfully")
        return True


def main():
    """Main entry point"""

    # Get API key from environment or command line
    api_key = os.environ.get('CHECKWX_API_KEY')

    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]

    if not api_key:
        logger.error("No API key provided!")
        print("Usage:")
        print(f"  {sys.argv[0]} YOUR_API_KEY")
        print("Or set environment variable: export CHECKWX_API_KEY=your_key_here")
        print()
        print("Get your free API key at: https://www.checkwx.com/")
        sys.exit(1)

    # Run collector for all configured stations
    all_success = True
    for station in STATIONS:
        collector = METARCollector(api_key, station)
        success = collector.run()
        if not success:
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
