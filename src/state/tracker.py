import json
import os
from datetime import datetime

class StateTracker:
    def __init__(self, state_file="output/actions_log.json"):
        self.state_file = state_file
        self.actions = []
        self.sensitivity = {}       # nested: {contact: {action_type: sensitivity}}
        self.action_stats = {}       # nested: {contact: {action_type: {'accepted': int, 'dismissed': int}}}
        self.load()

    def load(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        self.actions = []
                        self.sensitivity = {}
                        self.action_stats = {}
                        return
                    f.seek(0)
                    data = json.load(f)
                    self.actions = data.get('actions', [])
                    self.sensitivity = data.get('sensitivity', {})
                    self.action_stats = data.get('action_stats', {})
            except json.JSONDecodeError:
                print(f"Warning: {self.state_file} is corrupt. Starting fresh.")
                self.actions = []
                self.sensitivity = {}
                self.action_stats = {}
        else:
            self.actions = []
            self.sensitivity = {}
            self.action_stats = {}

    def save(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'actions': self.actions,
                'sensitivity': self.sensitivity,
                'action_stats': self.action_stats
            }, f, indent=2)

    def add_action(self, action):
        action_id = len(self.actions) + 1
        new_action = {
            'id': action_id,
            'contact': action['contact'],
            'type': action['type'],
            'timestamp': datetime.now().isoformat(),
            'feedback': None
        }
        self.actions.append(new_action)
        self.save()
        return action_id

    def record_feedback(self, action_id, feedback):
        for act in self.actions:
            if act['id'] == action_id:
                act['feedback'] = feedback
                self._update_sensitivity(act['contact'], act['type'], feedback)
                self._update_action_stats(act['contact'], act['type'], feedback)
                self.save()
                return True
        return False

    def _update_sensitivity(self, contact, action_type, feedback):
        if contact not in self.sensitivity:
            self.sensitivity[contact] = {}
        current = self.sensitivity[contact].get(action_type, 1.0)
        if feedback == 'accepted':
            new = min(current * 1.1, 2.0)
        elif feedback == 'dismissed':
            new = max(current * 0.9, 0.1)
        else:
            return
        self.sensitivity[contact][action_type] = new

    def _update_action_stats(self, contact, action_type, feedback):
        if contact not in self.action_stats:
            self.action_stats[contact] = {}
        if action_type not in self.action_stats[contact]:
            self.action_stats[contact][action_type] = {'accepted': 0, 'dismissed': 0}
        if feedback == 'accepted':
            self.action_stats[contact][action_type]['accepted'] += 1
        elif feedback == 'dismissed':
            self.action_stats[contact][action_type]['dismissed'] += 1

    def get_action_stats(self, contact, action_type):
        if contact in self.action_stats and action_type in self.action_stats[contact]:
            stats = self.action_stats[contact][action_type]
            return stats['accepted'], stats['dismissed']
        else:
            return 0, 0

    def get_contact_sensitivity(self, contact):
        return self.sensitivity.get(contact, {})