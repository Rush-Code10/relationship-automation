import pandas as pd
from src.automation.actions import generate_action_message

def print_scores(scores_df):
    """Print a formatted table of the latest relationship scores."""
    latest = scores_df.sort_values('week_start').groupby('contact').last().reset_index()
    latest = latest.sort_values('score', ascending=False)
    print("\n" + "="*70)
    print("📊 LATEST RELATIONSHIP SCORES (with streak)")
    print("="*70)
    for _, row in latest.iterrows():
        print(f"{row['contact']:<15} : {row['score']:.3f}  "
              f"(freq={row['freq']:.1f}/day, sentiment={row['avg_sentiment']:.2f}, "
              f"reciprocity={row['reciprocity']:.2f}, streak={int(row['current_streak'])} days)")
    print("-"*70)

def print_trends(trends):
    print("\n📈 TREND ANALYSIS")
    increasing = [c for c, t in trends.items() if t == 'increasing']
    decreasing = [c for c, t in trends.items() if t == 'decreasing']
    stable = [c for c, t in trends.items() if t == 'stable']
    if increasing:
        print(f"🔺 Increasing: {', '.join(increasing)}")
    if decreasing:
        print(f"🔻 Decreasing: {', '.join(decreasing)}")
    if stable:
        print(f"➖ Stable: {', '.join(stable)}")
    print("-"*70)

def print_actions(actions, contact_anomalies=None):
    """Print actions with their underlying reasons."""
    if not actions:
        print("✅ No actions needed at this time.")
        return

    print("\n" + "="*70)
    print("⚡ AUTOMATED ACTIONS GENERATED")
    print("="*70)
    for i, action in enumerate(actions, 1):
        msg = generate_action_message(action)
        print(f"{i}. [{action['type'].upper()}] {msg}")
        print(f"   🧠 Reason: {action['reason']}")
        if 'details' in action and action['details']:
            print(f"   📝 Details: {', '.join(str(d) for d in action['details'][:2])}")
        if contact_anomalies and action['contact'] in contact_anomalies:
            anom = contact_anomalies[action['contact']]
            if 'response_time_anomalies' in anom and anom['response_time_anomalies']:
                print(f"   ⚠️  Response time anomalies: {len(anom['response_time_anomalies'])} instances")
            if 'inactivity' in anom and anom['inactivity']:
                last_gap = anom['inactivity'][-1]
                # last_gap is (start, end, days)
                days = last_gap[2]
                print(f"   ⏳ Inactivity: {days} days since last message")
    print("="*70 + "\n")

def print_feedback_summary(tracker):
    """Print how feedback has adapted sensitivities."""
    sens = tracker.sensitivity
    if not sens:
        return
    print("\n🔁 ADAPTIVE SENSITIVITIES (after feedback)")
    for contact, actions in sens.items():
        print(f"{contact}:")
        for atype, val in actions.items():
            print(f"   {atype}: {val:.2f}")
    print("-"*70)