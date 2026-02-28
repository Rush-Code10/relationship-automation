import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Add project root to path so we can import src modules
sys.path.append(os.path.dirname(__file__))

from src.pipeline import run_pipeline
from src.state.tracker import StateTracker
from src.automation.notifier import print_actions, print_feedback_summary
from src.utils.config import load_config

st.set_page_config(page_title="Relationship Automation AI", layout="wide")
st.title("🤖 Relationship Automation AI")
st.markdown("An intelligent system that analyzes communication logs and proactively maintains relationships.")

# Sidebar for configuration
st.sidebar.header("Configuration")
config_path = st.sidebar.text_input("Config file path", "config/config.yaml")
run_button = st.sidebar.button("🚀 Run Pipeline")

# Initialize session state for results
if "pipeline_run" not in st.session_state:
    st.session_state.pipeline_run = False
if "df" not in st.session_state:
    st.session_state.df = None
if "scores_df" not in st.session_state:
    st.session_state.scores_df = None
if "actions" not in st.session_state:
    st.session_state.actions = None
if "tracker" not in st.session_state:
    st.session_state.tracker = None
if "contact_anomalies" not in st.session_state:
    st.session_state.contact_anomalies = None

# Run pipeline when button clicked
if run_button:
    with st.spinner("Running pipeline... This may take a moment."):
        config = load_config(config_path)
        df, scores_df, actions, tracker = run_pipeline(config_path)
        # Collect anomalies again for display (pipeline already has them, but we can recompute quickly)
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
        st.session_state.df = df
        st.session_state.scores_df = scores_df
        st.session_state.actions = actions
        st.session_state.tracker = tracker
        st.session_state.contact_anomalies = contact_anomalies
        st.session_state.pipeline_run = True
        st.success("Pipeline executed successfully!")

# If results exist, display them
if st.session_state.pipeline_run:
    scores_df = st.session_state.scores_df
    actions = st.session_state.actions
    tracker = st.session_state.tracker
    contact_anomalies = st.session_state.contact_anomalies

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Scores", "📈 Trends", "⚡ Actions", "🔁 Feedback"])

    with tab1:
        st.subheader("Latest Relationship Scores")
        # Get latest scores per contact
        latest = scores_df.sort_values('week_start').groupby('contact').last().reset_index()
        latest = latest.sort_values('score', ascending=False)
        # Format for display
        display_df = latest[['contact', 'score', 'freq', 'avg_sentiment', 'reciprocity', 'current_streak']].copy()
        display_df.columns = ['Contact', 'Score', 'Messages/day', 'Avg Sentiment', 'Reciprocity', 'Streak (days)']
        display_df['Score'] = display_df['Score'].round(3)
        display_df['Messages/day'] = display_df['Messages/day'].round(2)
        display_df['Avg Sentiment'] = display_df['Avg Sentiment'].round(2)
        display_df['Reciprocity'] = display_df['Reciprocity'].round(2)
        st.dataframe(display_df, use_container_width=True)

        # Optional: bar chart of scores
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(display_df['Contact'], display_df['Score'], color='skyblue')
        ax.set_xlabel('Score')
        ax.set_title('Relationship Health Scores')
        st.pyplot(fig)

    with tab2:
        st.subheader("Trend Analysis")
        from src.analysis.patterns import detect_trends
        trends = detect_trends(scores_df)
        increasing = [c for c, t in trends.items() if t == 'increasing']
        decreasing = [c for c, t in trends.items() if t == 'decreasing']
        stable = [c for c, t in trends.items() if t == 'stable']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🔺 Increasing**")
            for c in increasing:
                st.write(f"- {c}")
        with col2:
            st.markdown("**🔻 Decreasing**")
            for c in decreasing:
                st.write(f"- {c}")
        with col3:
            st.markdown("**➖ Stable**")
            for c in stable:
                st.write(f"- {c}")

        # Plot score over time for selected contact
        st.subheader("Score Over Time")
        selected_contact = st.selectbox("Select contact", scores_df['contact'].unique())
        contact_scores = scores_df[scores_df['contact'] == selected_contact].sort_values('week_start')
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(contact_scores['week_start'], contact_scores['score'], marker='o')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Score')
        ax2.set_title(f'{selected_contact} - Score Trend')
        plt.xticks(rotation=45)
        st.pyplot(fig2)

    with tab3:
        st.subheader("Automated Actions")
        if not actions:
            st.info("No actions generated.")
        else:
            for i, action in enumerate(actions):
                with st.expander(f"{i+1}. {action['type'].replace('_',' ').title()} for {action['contact']}"):
                    st.write(f"**Reason:** {action['reason']}")
                    if action.get('details'):
                        st.write(f"**Details:** {', '.join(str(d) for d in action['details'][:2])}")
                    if contact_anomalies and action['contact'] in contact_anomalies:
                        anom = contact_anomalies[action['contact']]
                        if anom['response_time_anomalies']:
                            st.write(f"⚠️ Response time anomalies: {len(anom['response_time_anomalies'])} instances")
                        if anom['inactivity']:
                            days = anom['inactivity'][-1][2]
                            st.write(f"⏳ Inactivity: {days} days since last message")
                    # Simulate feedback buttons (in real app, you'd store user response)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Accept", key=f"accept_{i}"):
                            # In a real app, you'd record feedback to tracker
                            st.success("Feedback recorded (accepted)")
                    with col2:
                        if st.button(f"❌ Dismiss", key=f"dismiss_{i}"):
                            st.info("Feedback recorded (dismissed)")

    with tab4:
        st.subheader("Feedback & Adaptation")
        st.write("The system learns from your feedback. Below are the current sensitivity multipliers per contact and action type.")
        sens = tracker.sensitivity
        if sens:
            # Convert to DataFrame for display
            rows = []
            for contact, actions_dict in sens.items():
                for atype, val in actions_dict.items():
                    rows.append({'Contact': contact, 'Action Type': atype, 'Sensitivity': round(val, 2)})
            sens_df = pd.DataFrame(rows)
            st.dataframe(sens_df, use_container_width=True)
        else:
            st.write("No feedback recorded yet.")

        # Show action stats (accepted/dismissed counts)
        st.subheader("Action Statistics")
        stats = tracker.action_stats
        if stats:
            rows2 = []
            for contact, actions_dict in stats.items():
                for atype, counts in actions_dict.items():
                    rows2.append({
                        'Contact': contact,
                        'Action Type': atype,
                        'Accepted': counts['accepted'],
                        'Dismissed': counts['dismissed']
                    })
            stats_df = pd.DataFrame(rows2)
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.write("No action statistics yet.")

else:
    st.info("Click 'Run Pipeline' in the sidebar to start.")