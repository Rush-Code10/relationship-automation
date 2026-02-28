import pandas as pd
from src.analysis.anomalies import (
    detect_inactivity_periods,
    detect_unanswered_questions,
    detect_sentiment_drop,
    detect_one_sided_conversation,
    detect_missed_commitments,
    detect_response_time_anomalies
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def apply_rules(contact, latest_score, df_contact, config, state_sensitivity=None, contact_features=None, contact_type=None):
    """
    Evaluate multiple signals and generate a list of possible actions with priority.
    """
    actions = []
    thresholds = config['thresholds']
    keywords = config['nlp']['commitment_keywords']
    current_date = pd.Timestamp.now()

    # ----- 1. Low relationship score -----
    if latest_score < thresholds['low_score']:
        actions.append({
            'type': 'catch_up',
            'contact': contact,
            'reason': f"Relationship score is low ({latest_score:.2f})",
            'priority': 1,
            'details': []
        })

    # ----- 2. Inactivity -----
    inactivity_gaps = detect_inactivity_periods(df_contact, contact, thresholds['inactivity_days'], current_date)
    if inactivity_gaps:
        last_gap = inactivity_gaps[-1]
        if last_gap[1] == current_date:
            days = last_gap[2]
            actions.append({
                'type': 'reach_out',
                'contact': contact,
                'reason': f"No messages for {days} days",
                'priority': 2,
                'details': [f"Last message: {last_gap[0].strftime('%Y-%m-%d')}"]
            })

    # ----- 3. Unanswered questions -----
    unanswered = detect_unanswered_questions(df_contact, contact, followup_days=2)
    for q in unanswered[:2]:
        actions.append({
            'type': 'follow_up_reminder',
            'contact': contact,
            'reason': f"Unanswered question from {q['timestamp'].strftime('%Y-%m-%d')}",
            'priority': 3,
            'details': [q['message']]
        })

    # ----- 4. Missed commitments -----
    missed = detect_missed_commitments(df_contact, contact, keywords, thresholds['commitment_followup_days'])
    for m in missed[:2]:
        actions.append({
            'type': 'follow_up_reminder',
            'contact': contact,
            'reason': f"Missed commitment: '{m['message']}'",
            'priority': 3,
            'details': [m['message']]
        })

    # ----- 5. Sentiment drop -----
    sent_drop = detect_sentiment_drop(df_contact, contact, window=3, drop_threshold=0.3)
    if sent_drop:
        actions.append({
            'type': 'check_in',
            'contact': contact,
            'reason': f"Sentiment dropped from {sent_drop['previous']:.2f} to {sent_drop['recent']:.2f}",
            'priority': 4,
            'details': []
        })

    # ----- 6. One-sided conversation -----
    one_sided_ratio = detect_one_sided_conversation(df_contact, contact)
    if one_sided_ratio:
        direction = "from you" if one_sided_ratio < 0.3 else "from them"
        actions.append({
            'type': 'balance_conversation',
            'contact': contact,
            'reason': f"Conversation is one-sided ({direction})",
            'priority': 5,
            'details': []
        })

    # ----- 7. Response time anomalies -----
    resp_anomalies = detect_response_time_anomalies(df_contact, contact, thresholds['max_response_time_std_multiplier'])
    if resp_anomalies:
        actions.append({
            'type': 'response_time_alert',
            'contact': contact,
            'reason': f"Unusually slow replies detected ({len(resp_anomalies)} instances)",
            'priority': 6,
            'details': [f"Slow reply: {a['message']}" for a in resp_anomalies[:2]]
        })

    # ----- ADVANCED RULES (using features and type) -----
    if contact_features and contact_type:
        feat = contact_features.get(contact, {})
        # 8. Conflict detected
        if feat.get('conflict_count', 0) > 0:
            actions.append({
                'type': 'suggest_apology',
                'contact': contact,
                'reason': f"Possible conflict detected ({feat['conflict_count']} argument periods)",
                'priority': 4,
                'details': []
            })
        # 9. Life event: stress / sick
        life = feat.get('life_events', {})
        if life.get('stress', 0) > 0 or life.get('sick', 0) > 0:
            actions.append({
                'type': 'support_checkin',
                'contact': contact,
                'reason': "Contact mentioned stress or illness",
                'priority': 3,
                'details': []
            })
        if life.get('exam', 0) > 0 or life.get('thesis', 0) > 0:
            actions.append({
                'type': 'support_checkin',
                'contact': contact,
                'reason': "Contact has exams/thesis deadlines",
                'priority': 3,
                'details': []
            })
        # 10. Celebration
        if feat.get('celebration_count', 0) > 0:
            actions.append({
                'type': 'congratulate',
                'contact': contact,
                'reason': "Positive event detected (birthday/achievement)",
                'priority': 4,
                'details': []
            })
        # 11. Commitment follow-through low
        if feat.get('commitment_follow_rate', 1.0) < 0.5:
            actions.append({
                'type': 'improve_followup',
                'contact': contact,
                'reason': f"Low follow-through on commitments ({feat['commitment_follow_rate']:.0%})",
                'priority': 5,
                'details': []
            })
        # 12. Plan proposal
        if len(missed) > 0:
            actions.append({
                'type': 'propose_plan',
                'contact': contact,
                'reason': "Turn missed commitment into a concrete plan",
                'priority': 3,
                'details': [m['message'] for m in missed[:1]]
            })
        # 13. Late night chats (romantic)
        if contact_type == 'romantic' and feat.get('late_night_msg', 0) > 5:
            actions.append({
                'type': 'romantic_checkin',
                'contact': contact,
                'reason': "Late night conversations suggest closeness",
                'priority': 4,
                'details': []
            })
        # 14. Topic-based: share meme
        if contact_type == 'friend' and feat.get('topic_counts', {}).get('casual', 0) > 5:
            actions.append({
                'type': 'share_meme',
                'contact': contact,
                'reason': "Frequent casual chats – share a meme",
                'priority': 6,
                'details': []
            })
        # 15. Academic reminder
        if contact_type == 'academic' and feat.get('topic_counts', {}).get('work', 0) > 5:
            actions.append({
                'type': 'academic_reminder',
                'contact': contact,
                'reason': "Work-related conversations – remind about deadlines",
                'priority': 5,
                'details': []
            })

    # Apply state sensitivity
    if state_sensitivity:
        for action in actions:
            sens = state_sensitivity.get(contact, {}).get(action['type'], 1.0)
            action['priority'] = action['priority'] * sens

    actions.sort(key=lambda x: x['priority'])
    return actions