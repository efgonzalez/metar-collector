import requests
import re
import csv
from datetime import datetime, timedelta, timezone

# -----------------------
# CONFIG
# -----------------------
ICAO = "GCGM"
DAYS_BACK = 7
START_HOUR = 3   # 03:00 local Canary time
END_HOUR = 11    # 11:00 local Canary time
OUTPUT_CSV = "gcgm_wind_03_11_last7days.csv"

# -----------------------
# DATE RANGE (UTC = Canary)
# -----------------------
end_dt = datetime.now(timezone.utc)
start_dt = end_dt - timedelta(days=DAYS_BACK)

def ogimet_dt(dt):
    return dt.strftime("%Y%m%d%H%M")

url = (
    "https://www.ogimet.com/cgi-bin/query_metars.php"
    f"?icao={ICAO}"
    f"&begin={ogimet_dt(start_dt)}"
    f"&end={ogimet_dt(end_dt)}"
    "&ord=REV"
    "&fmt=txt"
)

# -----------------------
# DOWNLOAD METARS
# -----------------------
resp = requests.get(url, timeout=30)
resp.raise_for_status()
lines = resp.text.splitlines()

# -----------------------
# REGEXES
# -----------------------
time_re = re.compile(r"(\d{6}Z)")           # DDHHMMZ
wind_re = re.compile(
    r"(VRB|\d{3})(\d{2})(G(\d{2}))?KT"
)

rows = []

for line in lines:
    if ICAO not in line:
        continue

    t_match = time_re.search(line)
    w_match = wind_re.search(line)

    if not t_match or not w_match:
        continue

    # Parse time (UTC = Canary)
    obs_time = datetime.strptime(
        t_match.group(1), "%d%H%MZ"
    ).replace(
        year=end_dt.year,
        tzinfo=timezone.utc
    )

    # Fix month/year rollover if needed
    if obs_time > end_dt:
        obs_time = obs_time.replace(year=end_dt.year - 1)

    hour = obs_time.hour
    if not (START_HOUR <= hour <= END_HOUR):
        continue

    direction = w_match.group(1)
    sustained = int(w_match.group(2))
    gust = int(w_match.group(4)) if w_match.group(4) else None

    rows.append([
        obs_time.strftime("%Y-%m-%d"),
        obs_time.strftime("%H:%M"),
        direction,
        sustained,
        gust
    ])

# -----------------------
# WRITE CSV
# -----------------------
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "date",
        "time_canary",
        "wind_direction",
        "wind_speed_kt",
        "wind_gust_kt"
    ])
    writer.writerows(sorted(rows))

print(f"Saved {len(rows)} rows to {OUTPUT_CSV}")

