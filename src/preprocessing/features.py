import pandas as pd
import numpy as np
from src.preprocessing.sentiment import get_sentiment
from src.preprocessing.nlp_utils import extract_commitments, detect_important_mentions
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def compute_response_times(df, user_name="Rahul"):
    df = df.copy()
    df['response_time_seconds'] = np.nan
    df['contact'] = df.apply(lambda row: row['sender'] if row['receiver'] == user_name else row['receiver'], axis=1)
    df = df.sort_values(['contact', 'timestamp'])

    response_times = []
    for contact, group in df.groupby('contact'):
        group = group.sort_values('timestamp')
        contact_msgs = group[group['sender'] == contact].copy()
        user_msgs = group[group['sender'] == user_name].copy()
        if contact_msgs.empty or user_msgs.empty:
            continue
        contact_msgs['timestamp_next'] = pd.to_datetime(contact_msgs['timestamp'])
        user_msgs['timestamp'] = pd.to_datetime(user_msgs['timestamp'])
        merged = pd.merge_asof(
            contact_msgs.sort_values('timestamp'),
            user_msgs[['timestamp']].sort_values('timestamp').rename(columns={'timestamp': 'response_time'}),
            left_on='timestamp',
            right_on='response_time',
            direction='forward',
            allow_exact_matches=False
        )
        merged['response_time_seconds'] = (merged['response_time'] - merged['timestamp']).dt.total_seconds()
        response_times.append(merged[['timestamp', 'contact', 'response_time_seconds']])

    if response_times:
        response_df = pd.concat(response_times)
        df = df.merge(response_df[['timestamp', 'contact', 'response_time_seconds']],
                      on=['timestamp', 'contact'], how='left', suffixes=('', '_new'))
        df['response_time_seconds'] = df['response_time_seconds_new'].fillna(df['response_time_seconds'])
        df.drop(columns=['response_time_seconds_new'], inplace=True)
    return df

def add_sentiment(df):
    df['sentiment'] = df['message'].apply(get_sentiment)
    return df

def add_commitments(df, keywords):
    # Convert NaN messages to empty string to avoid errors
    df['message'] = df['message'].fillna('')
    df['commitments'] = df['message'].apply(lambda x: extract_commitments(x, keywords))
    df['important_mentions'] = df['message'].apply(detect_important_mentions)
    return df

def preprocess_pipeline(df, user_name="Rahul", config=None):
    logger.info("Starting preprocessing...")
    df = df.copy()
    df = compute_response_times(df, user_name)
    df = add_sentiment(df)
    keywords = config['nlp']['commitment_keywords'] if config else []
    df = add_commitments(df, keywords)
    logger.info("Preprocessing complete.")
    return df