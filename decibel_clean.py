import pandas as pd
import os

# List of files (excluding Sound Ordinance)
csv_files = [
    "7pm_food_truck.csv",
    "21st_littlefield_fountain.csv",
    "22nd_street_construction.csv",
    "SZB_back_area.csv",
    "target_section.csv"
]

from datetime import datetime, timedelta

def load_custom_csv(file_path):
    metadata = {}
    with open(file_path, 'r') as f:
        for _ in range(8):
            line = f.readline()
            if ':' in line:
                key, value = line.strip().split(":", 1)
                metadata[key.strip()] = value.strip()

    df = pd.read_csv(file_path, skiprows=8)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    if "target_section" in file_path:
        df = df.rename(columns={
            'Recorded Value (dBA)': 'Recorded.Value..dBA.',
            'Time Stamp (yyyy-MM-dd HH:mm:ss.SSS)': 'Offset'
        })

        # Parse Start Time as datetime
        start_time_str = metadata.get("Start Time", "")
        start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")

        # Convert offset like "29:14.1" to seconds and add to start_dt
        def compute_full_time(offset_str):
            try:
                minutes, seconds = map(float, offset_str.split(":"))
                return start_dt + timedelta(minutes=minutes, seconds=seconds % 60)
            except:
                return None

        df['FullDatetime'] = df['Offset'].apply(compute_full_time)
        df['Date'] = df['FullDatetime'].dt.strftime("%Y-%m-%d")
        df['Time'] = df['FullDatetime'].dt.strftime("%H:%M:%S.%f").str[:-3]

        df = df[['Recorded.Value..dBA.', 'Date', 'Time']]

    else:
        timestamp_col = 'Time Stamp (yyyy-MM-dd HH:mm:ss.SSS)'
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
            df['Date'] = df[timestamp_col].dt.strftime("%Y-%m-%d")
            df['Time'] = df[timestamp_col].dt.strftime("%H:%M:%S.%f").str[:-3]
            df = df[['Recorded Value (dBA)', 'Date', 'Time']]
            df = df.rename(columns={'Recorded Value (dBA)': 'Recorded.Value..dBA.'})

    return metadata, df





all_meta_rows = []
all_raw_data = []

for file in csv_files:
    if not os.path.exists(file):
        print(f"[⚠] File not found: {file}")
        continue

    meta, raw = load_custom_csv(file)
    base = os.path.splitext(file)[0]

    # Add location to metadata and raw
    meta["location"] = base
    raw["location"] = base

    all_meta_rows.append(meta)
    all_raw_data.append(raw)

    print(f"[✓] Processed: {file}")

# Export metadata CSV
meta_df = pd.DataFrame(all_meta_rows)
meta_df.to_csv("all_locations_metadata.csv", index=False)
print("[✓] Exported all metadata → all_locations_metadata.csv")

# Export combined raw data CSV
combined_raw_df = pd.concat(all_raw_data, ignore_index=True)
combined_raw_df.to_csv("all_locations_raw_data.csv", index=False)
print("[✓] Exported combined raw data → all_locations_raw_data.csv")
