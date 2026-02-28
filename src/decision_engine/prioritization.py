def prioritize_contacts(contacts_with_scores):
    max_days = max([c['days_since_last'] for c in contacts_with_scores]) if contacts_with_scores else 1
    for c in contacts_with_scores:
        days_norm = min(c['days_since_last'] / max_days, 1.0) if max_days > 0 else 0
        c['urgency'] = (1 - c['latest_score']) * 0.5 + days_norm * 0.5
    sorted_contacts = sorted(contacts_with_scores, key=lambda x: x['urgency'], reverse=True)
    return sorted_contacts