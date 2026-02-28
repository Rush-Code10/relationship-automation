import pandas as pd
import glob
import os
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

EXPECTED_HEADER = ['timestamp', 'sender', 'receiver', 'platform', 'message']

def parse_timestamp(ts_str):
    """
    Try multiple common datetime formats.
    Returns pandas Timestamp or NaT if all fail.
    """
    if pd.isna(ts_str) or not isinstance(ts_str, str):
        return pd.NaT
    ts_str = ts_str.strip()
    # List of possible formats in order of likelihood
    formats = [
        "%Y-%m-%d %H:%M",      # 2026-02-01 09:00
        "%d-%m-%Y %H:%M",      # 01-02-2026 09:00
        "%Y-%m-%d %H:%M:%S",   # 2026-02-01 09:00:00
        "%d-%m-%Y %H:%M:%S",   # 01-02-2026 09:00:00
        "%m/%d/%Y %H:%M",      # 02/01/2026 09:00
        "%d/%m/%Y %H:%M",      # 01/02/2026 09:00
    ]
    for fmt in formats:
        try:
            return pd.to_datetime(ts_str, format=fmt)
        except (ValueError, TypeError):
            continue
    # Final fallback: let pandas infer (may be slow but works)
    try:
        return pd.to_datetime(ts_str, errors='coerce')
    except:
        return pd.NaT

def load_all_data(raw_data_path):
    all_files = glob.glob(os.path.join(raw_data_path, "*.csv"))
    if not all_files:
        logger.error(f"No CSV files found in {raw_data_path}")
        return pd.DataFrame()

    df_list = []
    for file_path in all_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            logger.warning(f"File {file_path} is empty. Skipping.")
            continue

        # Check if first line is a valid header
        first_line = lines[0].strip()
        parts = first_line.split(',')
        if len(parts) == 5 and all(p in EXPECTED_HEADER for p in parts):
            header = parts
            data_start = 1
        else:
            # No valid header found; assume file is data-only
            logger.info(f"File {file_path} has no header. Using default header.")
            header = EXPECTED_HEADER
            data_start = 0

        data = []
        for line_num, line in enumerate(lines[data_start:], start=data_start+1):
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) == 5:
                data.append(parts)
            else:
                # Message contains commas – combine extra parts
                timestamp = parts[0]
                sender = parts[1]
                receiver = parts[2]
                platform = parts[3]
                message = ','.join(parts[4:])
                data.append([timestamp, sender, receiver, platform, message])

        df = pd.DataFrame(data, columns=header)

        # Parse timestamps per file
        df['timestamp'] = df['timestamp'].apply(parse_timestamp)
        # Drop rows where timestamp could not be parsed
        initial_len = len(df)
        df = df.dropna(subset=['timestamp'])
        if len(df) < initial_len:
            logger.warning(f"Dropped {initial_len - len(df)} rows in {os.path.basename(file_path)} due to unparseable timestamps.")

        if not df.empty:
            df_list.append(df)
            logger.info(f"Loaded {len(df)} messages from {os.path.basename(file_path)}")

    if not df_list:
        logger.error("No valid data loaded.")
        return pd.DataFrame()

    combined = pd.concat(df_list, ignore_index=True)
    combined.sort_values('timestamp', inplace=True)
    logger.info(f"Total: {len(combined)} messages from {len(all_files)} files.")
    return combined