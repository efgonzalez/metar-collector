#!/usr/bin/env python3
"""
Export METAR data from SQLite database to various formats
"""

import sqlite3
import csv
import json
import sys
from datetime import datetime
from pathlib import Path


DB_PATH = 'metar_data.db'
STATION = 'GCGM'


def export_to_csv(output_file='metar_export.csv', station=STATION, start_date=None, end_date=None):
    """Export data to CSV format"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = 'SELECT * FROM metar_observations WHERE station = ?'
    params = [station]

    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)

    query += ' ORDER BY datetime'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No data found for the specified criteria")
        conn.close()
        return 0

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    conn.close()
    print(f"✓ Exported {len(rows)} observations to {output_file}")
    return len(rows)


def export_to_json(output_file='metar_export.json', station=STATION, start_date=None, end_date=None):
    """Export data to JSON format"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = 'SELECT * FROM metar_observations WHERE station = ?'
    params = [station]

    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)

    query += ' ORDER BY datetime'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No data found for the specified criteria")
        conn.close()
        return 0

    data = [dict(row) for row in rows]

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    conn.close()
    print(f"✓ Exported {len(rows)} observations to {output_file}")
    return len(rows)


def export_daily_summary(output_file='metar_daily_summary.json', station=STATION):
    """Export daily aggregated summary"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            date,
            COUNT(*) as observation_count,
            ROUND(AVG(wind_speed), 1) as avg_wind_speed,
            MIN(wind_speed) as min_wind_speed,
            MAX(wind_speed) as max_wind_speed,
            ROUND(AVG(CASE WHEN wind_gust IS NOT NULL THEN wind_gust END), 1) as avg_gust,
            MAX(wind_gust) as max_gust,
            GROUP_CONCAT(DISTINCT wind_direction) as wind_directions
        FROM metar_observations
        WHERE station = ?
        GROUP BY date
        ORDER BY date
    ''', (station,))

    rows = cursor.fetchall()

    if not rows:
        print("No data found")
        conn.close()
        return 0

    daily_data = []
    for row in rows:
        daily_data.append({
            'date': row[0],
            'observations': row[1],
            'avg_wind_speed': row[2],
            'min_wind_speed': row[3],
            'max_wind_speed': row[4],
            'avg_gust': row[5],
            'max_gust': row[6],
            'wind_directions': row[7]
        })

    with open(output_file, 'w') as f:
        json.dump(daily_data, f, indent=2)

    conn.close()
    print(f"✓ Exported {len(daily_data)} days to {output_file}")
    return len(daily_data)


def show_statistics(station=STATION):
    """Display database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Overall stats
    cursor.execute('''
        SELECT
            COUNT(*) as total_obs,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            ROUND(AVG(wind_speed), 1) as avg_speed,
            MAX(wind_speed) as max_speed,
            MAX(wind_gust) as max_gust
        FROM metar_observations
        WHERE station = ?
    ''', (station,))

    stats = cursor.fetchone()

    # Count days with data
    cursor.execute('''
        SELECT COUNT(DISTINCT date)
        FROM metar_observations
        WHERE station = ?
    ''', (station,))

    days_count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 60)
    print(f"METAR Database Statistics for {station}")
    print("=" * 60)
    print(f"Total observations:  {stats[0]:,}")
    print(f"Days with data:      {days_count}")
    print(f"Date range:          {stats[1]} to {stats[2]}")
    print(f"Average wind speed:  {stats[3]} kt")
    print(f"Max wind speed:      {stats[4]} kt")
    print(f"Max gust recorded:   {stats[5]} kt" if stats[5] else "Max gust recorded:   N/A")
    print("=" * 60)
    print()


def main():
    """Main entry point"""
    if not Path(DB_PATH).exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run the collector first: python3 metar_collector.py YOUR_API_KEY")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("METAR Data Export Tool")
    print("=" * 60)

    # Show statistics
    show_statistics()

    # Export options
    print("Export Options:")
    print("  1. Export all data to CSV")
    print("  2. Export all data to JSON")
    print("  3. Export daily summary to JSON")
    print("  4. Export last 7 days to CSV")
    print("  5. Export last 30 days to CSV")
    print("  6. Export all formats")
    print("  7. Exit")
    print()

    choice = input("Select option (1-7): ").strip()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if choice == '1':
        export_to_csv(f'metar_all_{timestamp}.csv')

    elif choice == '2':
        export_to_json(f'metar_all_{timestamp}.json')

    elif choice == '3':
        export_daily_summary(f'metar_daily_{timestamp}.json')

    elif choice == '4':
        from datetime import timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        export_to_csv(f'metar_7days_{timestamp}.csv', start_date=start_date, end_date=end_date)

    elif choice == '5':
        from datetime import timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        export_to_csv(f'metar_30days_{timestamp}.csv', start_date=start_date, end_date=end_date)

    elif choice == '6':
        export_to_csv(f'metar_all_{timestamp}.csv')
        export_to_json(f'metar_all_{timestamp}.json')
        export_daily_summary(f'metar_daily_{timestamp}.json')
        print("\n✓ All exports completed!")

    elif choice == '7':
        print("Exiting...")
        sys.exit(0)

    else:
        print("Invalid choice")
        sys.exit(1)

    print("\nExport complete!\n")


if __name__ == "__main__":
    main()
