import pandas as pd
import numpy as np
import re
from collections import Counter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def extract_advanced_features(df, user_name="Rahul"):
    """
    Per‑contact advanced features:
    - conflict score (negative sentiment bursts)
    - life events (keywords)
    - celebration moments (positive events)
    - topic distribution (simple keyword matching)
    - time‑of‑day patterns
    - initiation ratio over time
    - commitment follow‑through rate
    """
    features = {}
    for contact in df['contact'].unique():
        contact_df = df[df['contact'] == contact].copy()
        if len(contact_df) < 3:
            continue
        # Conflict detection: consecutive negative messages from both sides
        neg_thresh = -0.3
        contact_df['is_neg'] = contact_df['sentiment'] < neg_thresh
        # mark arguments: at least 3 messages in a row where both sides have negative sentiment
        contact_df['neg_block'] = (contact_df['is_neg'] != contact_df['is_neg'].shift()).cumsum()
        arg_blocks = contact_df.groupby('neg_block').filter(lambda g: len(g) >= 3 and g['is_neg'].all())
        conflict_count = len(arg_blocks) if not arg_blocks.empty else 0
        # Life events
        life_keywords = {
            'exam': ['exam', 'test', 'grades'],
            'thesis': ['thesis', 'dissertation', 'defense'],
            'deadline': ['deadline', 'due', 'submit by'],
            'sick': ['sick', 'fever', 'cough', 'hospital'],
            'stress': ['stress', 'crazy', 'overthinking', 'tired']
        }
        life_events = {}
        for event, kws in life_keywords.items():
            count = contact_df['message'].str.lower().apply(lambda x: any(kw in x for kw in kws) if pd.notna(x) else False).sum()
            life_events[event] = count
        # Celebration: positive sentiment + keywords
        celeb_keywords = ['happy', 'congratulations', 'birthday', 'anniversary', 'achievement', 'passed']
        celebration_count = contact_df[
            (contact_df['sentiment'] > 0.5) &
            (contact_df['message'].str.lower().apply(lambda x: any(kw in x for kw in celeb_keywords) if pd.notna(x) else False))
        ].shape[0]
        # Topic distribution (simplified)
        topics = {
            'work': ['work', 'job', 'office', 'meeting', 'project', 'deadline'],
            'personal': ['feel', 'love', 'miss', 'sorry', 'angry', 'happy'],
            'plans': ['meet', 'tonight', 'tomorrow', 'weekend', 'movie', 'dinner'],
            'casual': ['lol', 'haha', 'stfu', 'bro', 'valo', 'game']
        }
        topic_counts = Counter()
        for msg in contact_df['message'].dropna():
            msg_low = msg.lower()
            for topic, kws in topics.items():
                if any(kw in msg_low for kw in kws):
                    topic_counts[topic] += 1
                    break  # simple assignment
        # Time‑of‑day: late night (22‑4) messages
        contact_df['hour'] = contact_df['timestamp'].dt.hour
        late_night = ((contact_df['hour'] >= 22) | (contact_df['hour'] <= 4)).sum()
        # Initiation ratio over last 10 messages
        last_10 = contact_df.iloc[-10:]
        from_user = (last_10['sender'] == user_name).sum()
        from_contact = (last_10['sender'] == contact).sum()
        init_ratio = from_contact / (from_contact + from_user) if (from_contact + from_user) > 0 else 0.5
        # Commitment follow‑through: count commitments made by contact, count replies from user within 3 days
        commitments_made = contact_df[contact_df['commitments'].apply(len) > 0]
        followed = 0
        for idx, row in commitments_made.iterrows():
            future = contact_df[(contact_df['timestamp'] > row['timestamp']) &
                                (contact_df['timestamp'] <= row['timestamp'] + pd.Timedelta(days=3)) &
                                (contact_df['sender'] == user_name)]
            if not future.empty:
                followed += 1
        follow_rate = followed / len(commitments_made) if len(commitments_made) > 0 else 1.0

        features[contact] = {
            'conflict_count': conflict_count,
            'life_events': life_events,
            'celebration_count': celebration_count,
            'topic_counts': dict(topic_counts),
            'late_night_msg': late_night,
            'initiation_ratio_recent': init_ratio,
            'commitment_follow_rate': follow_rate
        }
    return features