import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def compute_streaks(df, contact):
    """
    Compute current streak (consecutive days with at least one message)
    and max streak for a given contact.
    """
    contact_df = df[df['contact'] == contact].copy()
    if contact_df.empty:
        return 0, 0
    # Get unique dates
    dates = contact_df['timestamp'].dt.date.unique()
    dates = sorted(dates)
    if len(dates) == 0:
        return 0, 0
    # Find streaks
    max_streak = 1
    current_streak = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    # Current streak: check if last message was today or yesterday
    last_date = dates[-1]
    today = pd.Timestamp.now().date()
    days_since = (today - last_date).days
    if days_since == 0:
        # active today, streak continues
        pass
    elif days_since == 1:
        # message yesterday, still in streak
        pass
    else:
        # streak broken
        current_streak = 0
    return current_streak, max_streak

def compute_relationship_scores(df, user_name="Rahul", weights=None, window_days=7):
    if weights is None:
        weights = {'frequency': 0.25, 'reciprocity': 0.2, 'sentiment': 0.2, 'response_time': 0.2, 'streak': 0.15}
    df = df.copy()
    df['week_start'] = df['timestamp'].dt.to_period('W').dt.start_time
    scores = []
    for contact, contact_df in df.groupby('contact'):
        # Compute overall streaks (not per week, but we can compute weekly streak component)
        current_streak, max_streak = compute_streaks(df, contact)
        for week_start, week_df in contact_df.groupby('week_start'):
            if len(week_df) == 0:
                continue
            freq = len(week_df) / 7.0
            user_msgs = len(week_df[week_df['sender'] == user_name])
            total_msgs = len(week_df)
            ratio = user_msgs / total_msgs if total_msgs > 0 else 0.5
            reciprocity_score = 1 - 2 * abs(0.5 - ratio)
            avg_sentiment = week_df['sentiment'].mean()
            resp_times = week_df['response_time_seconds'].dropna()
            if len(resp_times) > 0:
                avg_resp = resp_times.mean()
                max_resp = 7 * 24 * 3600
                resp_score = np.exp(-avg_resp / max_resp)
            else:
                resp_score = 0.5
            max_freq = 10.0
            freq_score = min(freq / max_freq, 1.0)
            # Streak score: normalize current streak by max possible (say 30 days)
            streak_score = min(current_streak / 30.0, 1.0) if current_streak > 0 else 0.0
            score = (weights['frequency'] * freq_score +
                     weights['reciprocity'] * reciprocity_score +
                     weights['sentiment'] * ((avg_sentiment + 1) / 2) +
                     weights['response_time'] * resp_score +
                     weights['streak'] * streak_score)
            scores.append({
                'contact': contact,
                'week_start': week_start,
                'score': score,
                'freq': freq,
                'reciprocity': reciprocity_score,
                'avg_sentiment': avg_sentiment,
                'avg_response_time': avg_resp if len(resp_times) > 0 else None,
                'num_messages': total_msgs,
                'current_streak': current_streak,
                'max_streak': max_streak
            })
    scores_df = pd.DataFrame(scores)
    logger.info(f"Computed relationship scores for {len(scores_df)} contact-weeks.")
    return scores_df