import pandas as pd
from src.preprocessing.loader import load_all_data
from src.preprocessing.features import preprocess_pipeline
from src.analysis.scoring import compute_relationship_scores
from src.analysis.patterns import detect_trends
from src.decision_engine.engine import run_decision_engine
from src.automation.notifier import print_scores, print_trends, print_actions, print_feedback_summary
from src.state.tracker import StateTracker
from src.state.feedback import simulate_feedback_loop
from src.utils.config import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def run_pipeline(config_path="config/config.yaml"):
    logger.info("Starting relationship automation pipeline.")
    config = load_config(config_path)

    df = load_all_data(config['data']['raw_data_path'])
    if df.empty:
        logger.error("No data loaded. Exiting.")
        return

    df = preprocess_pipeline(df, user_name="Rahul", config=config)
    scores_df = compute_relationship_scores(df, user_name="Rahul", weights=config['weights'])
    trends = detect_trends(scores_df)

    # ---- Print analysis results ----
    print_scores(scores_df)
    print_trends(trends)

    # ---- Advanced features and classification ----
    from src.analysis.features_advanced import extract_advanced_features
    from src.decision_engine.classify_contact import classify_contact

    advanced_features = extract_advanced_features(df, user_name="Rahul")
    contact_types = {}
    for contact in df['contact'].unique():
        contact_df = df[df['contact'] == contact]
        contact_types[contact] = classify_contact(contact, contact_df, advanced_features.get(contact, {}))

    # ---- Anomaly collection for display ----
    from src.analysis.anomalies import detect_response_time_anomalies, detect_inactivity_periods
    contact_anomalies = {}
    for contact in df['contact'].unique():
        contact_df = df[df['contact'] == contact]
        resp_anom = detect_response_time_anomalies(df, contact, config['thresholds']['max_response_time_std_multiplier'])
        inact = detect_inactivity_periods(df, contact, config['thresholds']['inactivity_days'], pd.Timestamp.now())
        contact_anomalies[contact] = {
            'response_time_anomalies': resp_anom,
            'inactivity': inact
        }

    tracker = StateTracker(state_file="output/actions_log.json")
    actions = run_decision_engine(df, scores_df, config, tracker,
                                  advanced_features=advanced_features,
                                  contact_types=contact_types)
    print_actions(actions, contact_anomalies)

    if actions:
        simulate_feedback_loop(tracker, actions)
        print_feedback_summary(tracker)

    logger.info("Pipeline finished.")
    return df, scores_df, actions, tracker