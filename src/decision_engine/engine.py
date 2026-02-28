import random
import pandas as pd
from src.decision_engine.rules import apply_rules
from src.decision_engine.prioritization import prioritize_contacts
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def select_action_with_rl(actions, contact, state, epsilon=0.2):
    """
    Use epsilon-greedy to choose one action from the list (or None).
    If no actions, return None.
    If random < epsilon, explore: pick random action.
    Else exploit: pick action with highest estimated reward.
    """
    if not actions:
        return None
    if random.random() < epsilon:
        # explore
        chosen = random.choice(actions)
        logger.debug(f"Exploring: selected {chosen['type']} for {contact}")
        return chosen
    else:
        # exploit: compute reward estimate for each action type
        best_action = None
        best_value = -float('inf')
        for action in actions:
            atype = action['type']
            accepted, dismissed = state.get_action_stats(contact, atype)
            total = accepted + dismissed
            if total == 0:
                est_reward = 0.5  # neutral
            else:
                est_reward = accepted / total
            # Adjust by base priority from rules (optional)
            base_priority = action.get('priority', 5)
            # combine: we want high reward and low priority number (more urgent)
            # normalize priority to 0-1 (1=urgent)
            urgency = 1.0 / (base_priority + 1)   # priority 1 -> 0.5, priority 5 -> 0.166
            combined = est_reward * 0.7 + urgency * 0.3
            if combined > best_value:
                best_value = combined
                best_action = action
        return best_action

def run_decision_engine(df, scores_df, config, state, advanced_features=None, contact_types=None):
    latest_scores = scores_df.sort_values('week_start').groupby('contact').last().reset_index()
    current_date = pd.Timestamp.now()
    contacts_info = []
    for contact in latest_scores['contact']:
        contact_df = df[df['contact'] == contact]
        days_since = (current_date - contact_df['timestamp'].max()).days if not contact_df.empty else 999
        contacts_info.append({
            'contact': contact,
            'latest_score': latest_scores[latest_scores['contact'] == contact]['score'].values[0],
            'days_since_last': days_since
        })
    prioritized = prioritize_contacts(contacts_info)
    all_actions = []
    for cinfo in prioritized:
        contact = cinfo['contact']
        contact_df = df[df['contact'] == contact]
        latest_score = cinfo['latest_score']
        sensitivity = state.get_contact_sensitivity(contact) if state else None
        feat = advanced_features.get(contact, {}) if advanced_features else {}
        ctype = contact_types.get(contact, 'other') if contact_types else 'other'
        # Generate candidate actions using rules
        candidates = apply_rules(contact, latest_score, contact_df, config, sensitivity, feat, ctype)
        if not candidates:
            continue
        # Use RL to select one action
        selected = select_action_with_rl(candidates, contact, state, epsilon=0.2)
        if selected:
            all_actions.append(selected)
            logger.info(f"RL selected {selected['type']} for {contact}")
        else:
            # fallback: take highest priority
            all_actions.append(candidates[0])
    logger.info(f"Decision engine generated {len(all_actions)} actions after RL selection.")
    return all_actions