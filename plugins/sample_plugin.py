# Sample plugin for MazGPT

def register():
    return SamplePlugin()

class SamplePlugin:
    def handle(self, text):
        if 'hello' in text.lower():
            return 'Hi! This is a response from the sample plugin.'
        return None
