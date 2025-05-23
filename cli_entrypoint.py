import os
import importlib
import sys
import types
import uuid
from typing import Dict, Any
from model.memory import ChatMemory
from model.llm import LocalLLM
from model.semantic_memory import SemanticMemory

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), 'plugins')

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.metadata: Dict[str, dict] = {}
        self.load_plugins()

    def load_plugins(self):
        self.plugins.clear()
        self.metadata.clear()
        sys.path.insert(0, PLUGINS_DIR)
        for fname in os.listdir(PLUGINS_DIR):
            if fname.endswith('.py') and not fname.startswith('_'):
                mod_name = fname[:-3]
                try:
                    if mod_name in sys.modules:
                        # Reload if already loaded
                        module = importlib.reload(sys.modules[mod_name])
                    else:
                        module = importlib.import_module(f'plugins.{mod_name}')
                    if hasattr(module, 'register'):
                        plugin = module.register()
                        self.plugins[mod_name] = plugin
                        # Plugin metadata: docstring or .meta attribute
                        meta = getattr(plugin, 'meta', {})
                        if not meta and hasattr(plugin, '__doc__'):
                            meta = {'description': plugin.__doc__}
                        self.metadata[mod_name] = meta
                except Exception as e:
                    print(f"Error loading plugin {mod_name}: {e}")
        sys.path.pop(0)

    def reload_plugins(self):
        self.load_plugins()

    def get_plugin(self, name):
        return self.plugins.get(name)

    def list_plugins(self):
        return list(self.plugins.keys())

    def get_metadata(self, name):
        return self.metadata.get(name, {})

def basic_ai_response(user_input):
    # Placeholder for basic AI response logic
    return None

def main():
    print('Welcome to MazGPT!')
    plugin_manager = PluginManager()
    memory = ChatMemory()
    semantic_memory = SemanticMemory()
    llm = LocalLLM(model_name="microsoft/phi-2")  # You can change to another small model if needed
    projects = {'default': 'Default'}
    current_project = 'default'
    preferences = {"language": "en", "tone": "friendly"}
    archived_projects = set()
    while True:
        user_input = input(f'[{projects.get(current_project, current_project)}] You: ')
        if user_input.lower() in ('exit', 'quit', '/bye'):
            print('MazGPT: Goodbye!')
            semantic_memory.persist()
            break
        if user_input.lower().startswith('/prefs'):
            parts = user_input.strip().split()
            if len(parts) == 2 and parts[1] == 'show':
                print('Current preferences:')
                for k, v in preferences.items():
                    print(f'- {k}: {v}')
            elif len(parts) == 4 and parts[1] == 'set':
                key, value = parts[2], parts[3]
                if key in preferences:
                    preferences[key] = value
                    print(f'Preference {key} set to {value}')
                else:
                    print(f'Unknown preference: {key}')
            else:
                print('Prefs commands: /prefs show, /prefs set <key> <value>')
            continue
        if user_input.lower().startswith('/project'):
            parts = user_input.strip().split()
            if len(parts) >= 3 and parts[1] == 'create':
                name = ' '.join(parts[2:]).strip()
                pid = name.lower().replace(' ', '-').replace('/', '-')
                if pid in projects:
                    print(f'Project "{name}" already exists.')
                else:
                    projects[pid] = name
                    print(f'Project "{name}" created.')
            elif len(parts) >= 3 and parts[1] == 'select':
                pid = ' '.join(parts[2:]).strip().lower().replace(' ', '-').replace('/', '-')
                if pid in projects:
                    current_project = pid
                    print(f'Switched to project: {projects[pid]}')
                else:
                    print(f'Project not found: {pid}')
            elif len(parts) == 3 and parts[1] == 'delete':
                pid = parts[2].strip().lower().replace(' ', '-').replace('/', '-')
                if pid == 'default':
                    print('Cannot delete the default project.')
                elif pid in projects:
                    del projects[pid]
                    if current_project == pid:
                        current_project = 'default'
                    print(f'Project deleted: {pid}')
                else:
                    print(f'Project not found: {pid}')
            elif len(parts) == 3 and parts[1] == 'archive':
                pid = parts[2].strip().lower().replace(' ', '-').replace('/', '-')
                if pid == 'default':
                    print('Cannot archive the default project.')
                elif pid in projects:
                    archived_projects.add(pid)
                    del projects[pid]
                    if current_project == pid:
                        current_project = 'default'
                    print(f'Project archived: {pid}')
                else:
                    print(f'Project not found: {pid}')
            elif len(parts) == 2 and parts[1] == 'list':
                print('Projects:')
                for pid, name in projects.items():
                    print(f'- {name} ({pid})')
                if archived_projects:
                    print('Archived:')
                    for pid in archived_projects:
                        print(f'- {pid}')
            else:
                print('Project commands: /project create <name>, /project select <name>, /project list, /project delete <name>, /project archive <name>')
            continue
        if user_input.lower() == '/newchat':
            memory.clear(project_id=current_project)
            print('Started a new chat for this project.')
            continue
        if user_input.lower().startswith('/search '):
            term = user_input[len('/search '):].strip().lower()
            results = [h for h in memory.get_recent(100, project_id=current_project) if term in h['message'].lower()]
            print(f'Search results for "{term}":')
            for entry in results:
                print(f"[{entry['timestamp']}] {entry['user']}: {entry['message']}")
            continue
        if user_input.lower().startswith('/export'):  # /export <filename.json>
            parts = user_input.strip().split()
            filename = parts[1] if len(parts) > 1 else f'{current_project}-chat.json'
            msgs = memory.get_recent(1000, project_id=current_project)
            with open(filename, 'w', encoding='utf-8') as f:
                import json
                json.dump(msgs, f, indent=2, ensure_ascii=False)
            print(f'Exported chat to {filename}')
            continue
        if user_input.lower().startswith('/import '):
            filename = user_input[len('/import '):].strip()
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    import json
                    msgs = json.load(f)
                if isinstance(msgs, list):
                    for m in msgs:
                        memory.add(m.get('user', 'user'), m.get('message', ''), project_id=current_project)
                    print(f'Imported {len(msgs)} messages into current chat.')
                else:
                    print('Invalid import file.')
            except Exception as e:
                print(f'Import failed: {e}')
            continue
        if user_input.lower() == '/plugins':
            print('Loaded plugins:')
            for name in plugin_manager.list_plugins():
                meta = plugin_manager.get_metadata(name)
                desc = meta.get('description', '(no description)')
                print(f'- {name}: {desc}')
            continue
        if user_input.lower() == '/reload':
            plugin_manager.reload_plugins()
            print('Plugins reloaded.')
            continue
        if user_input.lower() == '/history':
            print('Recent chat history:')
            for entry in memory.get_recent(10, project_id=current_project):
                print(f"[{entry['timestamp']}] {entry['user']}: {entry['message']}")
            continue
        if user_input.lower() == '/clearhistory':
            memory.clear(project_id=current_project)
            print('Chat history cleared.')
            continue
        if user_input.lower().startswith('/recall '):
            query = user_input[len('/recall '):]
            results = semantic_memory.query(query, project_id=current_project)
            print('Most relevant past messages:')
            for doc, meta, score in results:
                print(f"- [{meta.get('user', '?')}] {doc} (score: {score:.3f})")
            continue
        if user_input.lower() == '/askllm':
            context = memory.get_context_window(max_turns=10, max_chars=2000, project_id=current_project)
            semantic_results = semantic_memory.query(
                " ".join([entry['message'] for entry in context]), n_results=3, project_id=current_project
            )
            semantic_context = [doc for doc, meta, score in semantic_results]
            prompt = "\n".join(semantic_context + [f"{entry['user']}: {entry['message']}" for entry in context])
            print("MazGPT (streaming): ", end="", flush=True)
            llm.generate(prompt, stream=True, language=preferences.get("language", "en"), tone=preferences.get("tone", "friendly"))
            print()  # Newline after streaming
            continue
        msg_id = str(uuid.uuid4())
        semantic_memory.add_message(
            message_id=msg_id,
            text=user_input,
            metadata={"user": "user"},
            project_id=current_project
        )
        memory.add('user', user_input, project_id=current_project)
        # First, try built-in AI responses
        ai_response = basic_ai_response(user_input)
        if ai_response:
            msg_id = str(uuid.uuid4())
            semantic_memory.add_message(
                message_id=msg_id,
                text=ai_response,
                metadata={"user": "MazGPT"},
                project_id=current_project
            )
            memory.add('MazGPT', ai_response, project_id=current_project)
            continue
        # Then, try plugins
        for name, plugin in plugin_manager.plugins.items():
            if hasattr(plugin, 'handle'):
                response = plugin.handle(user_input)
                if response:
                    print(f'{name}: {response}')
                    msg_id = str(uuid.uuid4())
                    semantic_memory.add_message(
                        message_id=msg_id,
                        text=response,
                        metadata={"user": name},
                        project_id=current_project
                    )
                    memory.add(name, response, project_id=current_project)
                    break
        else:
            # Advanced reasoning: if user_input contains certain keywords, add reasoning instruction
            reasoning_instruction = ""
            if any(word in user_input.lower() for word in ["explain", "why", "how", "step by step", "summarize", "reasoning", "logic", "analyze", "analyze this", "break down"]):
                reasoning_instruction = "\nExplain your reasoning step by step."
            context = memory.get_context_window(max_turns=10, max_chars=2000, project_id=current_project)
            semantic_results = semantic_memory.query(
                " ".join([entry['message'] for entry in context]), n_results=3, project_id=current_project
            )
            semantic_context = [doc for doc, meta, score in semantic_results]
            prompt = "\n".join(semantic_context + [f"{entry['user']}: {entry['message']}" for entry in context])
            llm_output = llm.generate(prompt + f"\nuser: {user_input}\nMazGPT:" + reasoning_instruction, language=preferences.get("language", "en"), tone=preferences.get("tone", "friendly"))
            print(f"MazGPT: {llm_output}")
            msg_id = str(uuid.uuid4())
            semantic_memory.add_message(
                message_id=msg_id,
                text=llm_output,
                metadata={"user": "MazGPT"},
                project_id=current_project
            )
            memory.add('MazGPT', llm_output, project_id=current_project)

if __name__ == '__main__':
    main()
