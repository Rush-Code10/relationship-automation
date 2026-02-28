import re
import pandas as pd

def extract_commitments(text, keywords):
    if pd.isna(text) or not isinstance(text, str):
        return []
    text_lower = text.lower()
    found = [kw for kw in keywords if kw in text_lower]
    return found

def detect_important_mentions(text):
    patterns = [
        r'\b(tomorrow|today|tonight|next week|this weekend)\b',
        r'\b\d{1,2}:\d{2}\s*(am|pm)?\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{1,2}\b'
    ]
    mentions = []
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            mentions.append(p)
    return mentions