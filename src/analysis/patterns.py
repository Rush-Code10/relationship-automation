import numpy as np

def detect_trends(scores_df, window=3):
    trends = {}
    for contact, group in scores_df.groupby('contact'):
        group = group.sort_values('week_start')
        if len(group) < 2:
            trends[contact] = 'stable'
            continue
        x = np.arange(len(group))
        y = group['score'].values
        slope = np.polyfit(x, y, 1)[0]
        if slope > 0.01:
            trends[contact] = 'increasing'
        elif slope < -0.01:
            trends[contact] = 'decreasing'
        else:
            trends[contact] = 'stable'
    return trends