from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import pandas as pd

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if pd.isna(text) or not isinstance(text, str):
        return 0.0
    return sia.polarity_scores(text)['compound']