# MazGPT Plugin Template

## Plugin Manifest (plugin.json)

{
  "name": "sample_plugin",
  "version": "1.0.0",
  "description": "A sample plugin that responds to greetings.",
  "author": "Your Name",
  "entry_point": "sample_plugin.py",
  "permissions": ["none"],
  "dependencies": []
}

## Plugin Python File (sample_plugin.py)

"""

Sample Plugin

-------------

Responds to greetings like 'hello', 'hi', etc.

Manifest fields:

- name: Unique plugin name
- version: Plugin version
- description: Short description
- author: Plugin author
- entry_point: Main Python file
- permissions: List of required permissions (e.g., 'internet', 'filesystem')
- dependencies: List of required Python packages
"""

def register():
    return SamplePlugin()

class SamplePlugin:
    meta = {
        "description": "Responds to greetings like 'hello', 'hi', etc.",
        "version": "1.0.0",
        "author": "Your Name"
    }
    def handle(self, text):
        if 'hello' in text.lower():
            return 'Hi! This is a response from the sample plugin.'
        return None
