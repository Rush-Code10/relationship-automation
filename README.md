# Relationship Automation AI

An AI‑powered system that analyzes communication logs and proactively maintains relationships by generating intelligent reminders and suggestions.

## Features
- Loads and processes multi‑platform chat logs (CSV)
- Computes relationship health scores (frequency, reciprocity, sentiment, response time)
- Detects anomalies: inactivity, delayed replies, missed follow‑ups
- Rule‑based decision engine with adaptive thresholds via user feedback
- Generates automated actions (catch‑up, reach‑out, follow‑up reminders)
- State management and feedback simulation

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Download NLTK VADER lexicon:  
   `python -c "import nltk; nltk.download('vader_lexicon')"`
3. Place your CSV chat logs in `data/raw/` (sample files provided)
4. Run the pipeline: `python scripts/run_pipeline.py`

## Configuration
Edit `config/config.yaml` to adjust thresholds, weights, and keywords.