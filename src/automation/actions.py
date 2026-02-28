import re
from src.automation.templates import get_template

def generate_action_message(action):
    template = get_template(action['type'])
    contact = action['contact']
    reason = action['reason']
    details = action.get('details', [])

    if action['type'] == 'catch_up':
        return template.format(contact=contact)
    elif action['type'] == 'reach_out':
        # Extract number of days from reason (e.g., "No messages for 22 days")
        match = re.search(r'\d+', reason)
        days = int(match.group()) if match else 7
        return template.format(contact=contact, days=days)
    elif action['type'] == 'follow_up_reminder':
        commitment = details[0] if details else "something"
        return template.format(contact=contact, commitment=commitment)
    elif action['type'] == 'check_in':
        return template.format(contact=contact)
    elif action['type'] == 'balance_conversation':
        return template.format(contact=contact)
    elif action['type'] == 'response_time_alert':
        return template.format(contact=contact)
    elif action['type'] == 'suggest_apology':
        return template.format(contact=contact)
    elif action['type'] == 'support_checkin':
        return template.format(contact=contact)
    elif action['type'] == 'congratulate':
        return template.format(contact=contact)
    elif action['type'] == 'improve_followup':
        return template.format(contact=contact)
    elif action['type'] == 'propose_plan':
        commitment = details[0] if details else "that"
        return template.format(contact=contact, commitment=commitment)
    elif action['type'] == 'romantic_checkin':
        return template.format(contact=contact)
    elif action['type'] == 'share_meme':
        return template.format(contact=contact)
    elif action['type'] == 'academic_reminder':
        return template.format(contact=contact)
    else:
        return f"Action for {contact}: {reason}"