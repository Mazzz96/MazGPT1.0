import os
import json
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'chat_memory.json')

class ChatMemory:
    def __init__(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'w') as f:
                json.dump([], f)
        self.load()

    def load(self):
        with open(MEMORY_FILE, 'r') as f:
            self.history = json.load(f)

    def save(self):
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)

    def add(self, user, message, project_id="default"):
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'message': message,
            'project_id': project_id
        })
        self.save()

    def get_recent(self, n=10, project_id="default"):
        filtered = [h for h in self.history if h.get('project_id', 'default') == project_id]
        return filtered[-n:]

    def clear(self, project_id=None):
        if project_id is None:
            self.history = []
        else:
            self.history = [h for h in self.history if h.get('project_id', 'default') != project_id]
        self.save()

    def get_context_window(self, max_turns=10, max_chars=2000, project_id="default"):
        """
        Returns a list of messages (dicts) for the given project that fit within the max_turns and max_chars constraints.
        """
        filtered = [h for h in self.history if h.get('project_id', 'default') == project_id]
        context = []
        total_chars = 0
        for entry in reversed(filtered):
            msg = f"{entry['user']}: {entry['message']}"
            if len(context) >= max_turns or total_chars + len(msg) > max_chars:
                break
            context.insert(0, entry)  # Insert at the beginning to maintain order
            total_chars += len(msg)
        return context
