templates = {
    'catch_up': "Hey {contact}, it's been a while! How have you been? Let's catch up soon.",
    'reach_out': "Hi {contact}, I noticed we haven't talked in {days} days. Hope you're doing well!",
    'follow_up_reminder': "Reminder: You had a commitment with {contact}: '{commitment}'. Maybe follow up?",
    'check_in': "Hey {contact}, I sense things might have been a bit off lately. Everything okay?",
    'balance_conversation': "The conversation with {contact} feels one-sided. Maybe reach out and share something?",
    'response_time_alert': "You've been taking longer than usual to reply to {contact}. A quick check-in might help.",
    'suggest_apology': "It seems there might have been a conflict with {contact}. Consider sending a kind message to smooth things over.",
    'support_checkin': "{contact} mentioned being stressed or unwell. A supportive message would mean a lot.",
    'congratulate': "{contact} had a positive event recently (birthday/achievement). Send your congratulations!",
    'improve_followup': "You often miss following up on commitments with {contact}. Try to be more responsive.",
    'propose_plan': "Based on the missed commitment '{commitment}', suggest a concrete time: 'How about this Friday?'",
    'romantic_checkin': "Late night chats with {contact} suggest intimacy. Send a sweet goodnight message.",
    'share_meme': "Share a funny meme with {contact} to keep the casual vibe going.",
    'academic_reminder': "Remind {contact} about upcoming deadlines or offer help with work.",
}

def get_template(action_type):
    return templates.get(action_type, "Action: {reason}")