import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def detect_response_time_anomalies(df, contact, std_multiplier=2.0):
    """Find unusually slow responses."""
    contact_df = df[df['contact'] == contact].copy()
    resp_times = contact_df['response_time_seconds'].dropna()
    if len(resp_times) < 2:
        return []
    mean = resp_times.mean()
    std = resp_times.std()
    threshold = mean + std_multiplier * std
    anomalies = contact_df[contact_df['response_time_seconds'] > threshold]
    return anomalies[['timestamp', 'message', 'response_time_seconds']].to_dict('records')

def detect_inactivity_periods(df, contact, threshold_days=7, current_date=None):
    """Find gaps in conversation longer than threshold."""
    if current_date is None:
        current_date = pd.Timestamp.now()
    contact_df = df[df['contact'] == contact].sort_values('timestamp')
    if contact_df.empty:
        return []
    gaps = []
    prev_time = contact_df['timestamp'].iloc[0]
    for i, row in contact_df.iloc[1:].iterrows():
        gap = (row['timestamp'] - prev_time).days
        if gap > threshold_days:
            gaps.append((prev_time, row['timestamp'], gap))
        prev_time = row['timestamp']
    last_msg = contact_df['timestamp'].iloc[-1]
    days_since_last = (current_date - last_msg).days
    if days_since_last > threshold_days:
        gaps.append((last_msg, current_date, days_since_last))
    return gaps

def detect_unanswered_questions(df, contact, followup_days=2):
    """
    Find messages that are questions but received no reply from 'Rahul' within followup_days.
    Simple heuristic: message contains '?' and is from the contact.
    """
    contact_df = df[df['contact'] == contact].sort_values('timestamp')
    questions = []
    for idx, row in contact_df[contact_df['sender'] == contact].iterrows():
        if '?' in row['message']:
            # look for a reply from Rahul within followup_days
            future = contact_df[(contact_df['timestamp'] > row['timestamp']) &
                                (contact_df['timestamp'] <= row['timestamp'] + pd.Timedelta(days=followup_days)) &
                                (contact_df['sender'] == 'Rahul')]
            if future.empty:
                questions.append(row)
    return questions

def detect_sentiment_drop(df, contact, window=3, drop_threshold=0.3):
    """Detect if recent sentiment has dropped significantly compared to previous window."""
    contact_df = df[df['contact'] == contact].sort_values('timestamp')
    if len(contact_df) < window*2:
        return None
    recent = contact_df['sentiment'].iloc[-window:].mean()
    previous = contact_df['sentiment'].iloc[-2*window:-window].mean()
    if previous - recent > drop_threshold:
        return {'previous': previous, 'recent': recent, 'drop': previous - recent}
    return None

def detect_one_sided_conversation(df, contact, ratio_threshold=0.7):
    """
    Detect if conversation is one-sided (mostly from one person) in last N messages.
    Returns ratio or False.
    """
    contact_df = df[df['contact'] == contact].sort_values('timestamp')
    if len(contact_df) < 5:
        return False
    last_10 = contact_df.iloc[-10:]
    from_contact = len(last_10[last_10['sender'] == contact])
    total = len(last_10)
    ratio = from_contact / total if total > 0 else 0
    if ratio > ratio_threshold or ratio < (1 - ratio_threshold):
        return ratio
    return False

def detect_missed_commitments(df, contact, commitment_keywords, followup_days=3):
    """
    Find commitments (e.g., "let's meet") made by contact that Rahul hasn't followed up on.
    """
    contact_df = df[df['contact'] == contact].sort_values('timestamp')
    missed = []
    for idx, row in contact_df[contact_df['sender'] == contact].iterrows():
        if row['commitments']:   # list of matched keywords
            # look for any response from Rahul after this message
            future = contact_df[(contact_df['timestamp'] > row['timestamp']) &
                                (contact_df['timestamp'] <= row['timestamp'] + pd.Timedelta(days=followup_days)) &
                                (contact_df['sender'] == 'Rahul')]
            if future.empty:
                missed.append(row)
    return missed