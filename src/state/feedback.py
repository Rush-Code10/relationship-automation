import random

def simulate_feedback_loop(tracker, actions):
    print("\n=== SIMULATING USER FEEDBACK ===")
    for action in actions:
        action_id = tracker.add_action(action)
        feedback = random.choices(['accepted', 'dismissed'], weights=[0.3, 0.7])[0]
        tracker.record_feedback(action_id, feedback)
        print(f"Action {action_id} for {action['contact']} ({action['type']}) was {feedback}.")
    print("=================================\n")