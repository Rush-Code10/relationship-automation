import re

def classify_contact(contact_name, df_contact=None, features=None):
    """
    Infer relationship type based on name and conversation patterns.
    Returns one of: 'family', 'romantic', 'friend', 'academic', 'other'
    """
    name_lower = contact_name.lower()
    # Explicit mappings from our dataset
    if contact_name in ['Mom', 'Dad', 'Sister', 'Brother']:
        return 'family'
    if contact_name in ['Anjali', 'Priya']:
        return 'romantic'
    if contact_name in ['Varun', 'Sahil', 'Sneha', 'Riya', 'Aryan']:
        return 'friend'
    if contact_name == 'Dr. Sharma':
        return 'academic'
    # Fallback: use features if available
    if features:
        if features.get('late_night_msg', 0) > 10:
            return 'romantic'
        if features.get('topic_counts', {}).get('work', 0) > 5:
            return 'academic'
    return 'other'