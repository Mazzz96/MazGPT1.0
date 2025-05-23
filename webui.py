import gradio as gr
import uuid
from model.memory import ChatMemory
from model.llm import LocalLLM
from model.semantic_memory import SemanticMemory
from model.router import SkillRouter
import importlib.util
import os

# Dynamically load all plugins from the plugins directory
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), 'plugins')
plugins = {}
for fname in os.listdir(PLUGINS_DIR):
    if fname.endswith('.py') and not fname.startswith('_'):
        mod_name = fname[:-3]
        spec = importlib.util.spec_from_file_location(mod_name, os.path.join(PLUGINS_DIR, fname))
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                plugins[mod_name] = module.register()
        except Exception as e:
            print(f"Error loading plugin {mod_name}: {e}")

memory = ChatMemory()
llm = LocalLLM(model_name="microsoft/phi-2")
semantic_memory = SemanticMemory()
router = SkillRouter("model/model_config.yaml")

def get_project_list():
    # In a real app, this could be loaded from disk or DB
    return [
        {"id": "default", "name": "Default"}
    ]

def chat_fn(user_input, history, project_id="default", preferences=None):
    msg_id = str(uuid.uuid4())
    semantic_memory.add_message(msg_id, user_input, {"user": "user"}, project_id=project_id)
    memory.add('user', user_input, project_id=project_id)
    history = history or []
    # Try plugins first
    for name, plugin in plugins.items():
        if hasattr(plugin, 'handle'):
            response = plugin.handle(user_input)
            if response:
                msg_id = str(uuid.uuid4())
                semantic_memory.add_message(msg_id, response, {"user": name}, project_id=project_id)
                memory.add(name, response, project_id=project_id)
                history.append((user_input, f"{name}: {response}"))
                return history
    # Otherwise, use SkillRouter with semantic context
    context = memory.get_context_window(max_turns=10, max_chars=2000, project_id=project_id)
    semantic_results = semantic_memory.query(
        " ".join([entry['message'] for entry in context]), n_results=3, project_id=project_id
    )
    semantic_context = [doc for doc, meta, score in semantic_results]
    prompt = "\n".join(semantic_context + [f"{entry['user']}: {entry['message']}" for entry in context])
    # Advanced reasoning: if user_input contains certain keywords, add reasoning instruction
    reasoning_instruction = ""
    if any(word in user_input.lower() for word in ["explain", "why", "how", "step by step", "summarize", "reasoning", "logic", "analyze", "analyze this", "break down"]):
        reasoning_instruction = "\nExplain your reasoning step by step."
    # Route to best model
    prefs = preferences or {"language": "en", "tone": "friendly"}
    router_response = router.route((prompt + f"\nuser: {user_input}\nMazGPT:" + reasoning_instruction) if prompt else user_input, preferences=prefs)
    if isinstance(router_response, dict):
        model_name = router_response.get("model_name", "LLM")
        output = router_response.get("output", "")
    else:
        model_name = getattr(router_response, "model_name", "LLM") if hasattr(router_response, "model_name") else "LLM"
        output = router_response if isinstance(router_response, str) else str(router_response)
    # Actually call the LLM with language/tone
    llm_output = llm.generate(prompt + f"\nuser: {user_input}\nMazGPT:" + reasoning_instruction, language=prefs.get("language", "en"), tone=prefs.get("tone", "friendly"))
    msg_id = str(uuid.uuid4())
    semantic_memory.add_message(msg_id, llm_output, {"user": model_name}, project_id=project_id)
    memory.add(model_name, llm_output, project_id=project_id)
    history.append((user_input, f"{model_name}: {llm_output}"))
    return history

def recall_fn(query, project_id="default"):
    results = semantic_memory.query(query, project_id=project_id)
    return "\n".join([f"[{meta.get('user','?')}] {doc} (score: {score:.3f})" for doc, meta, score in results])

def upload_file(file):
    plugin = plugins.get('file_plugin')
    if plugin:
        return plugin.handle(f"/upload {file.name}")
    return "File plugin not available."

def upload_image(image):
    plugin = plugins.get('image_plugin')
    if plugin:
        return plugin.handle(f"/imgupload {image.name}")
    return "Image plugin not available."

def launch_gradio():
    with gr.Blocks(theme=gr.themes.Base(), css=".gradio-container {max-width: 100vw !important; width: 100vw !important;} .gr-chatbot {height: 70vh !important;}") as demo:
        gr.Markdown("# MazGPT Web UI\n\n**Built with Meta Llama 3 and 4** :rocket:")
        with gr.Row():
            chatbot = gr.Chatbot(elem_id="chatbot")
            with gr.Column():
                project_list = gr.State(get_project_list())
                current_project = gr.State("default")
                gr.Markdown("**Current Project:** ").style(font_weight="bold")
                project_dropdown = gr.Dropdown(
                    choices=["default"],
                    value="default",
                    label="Select Project"
                )
                recall_box = gr.Textbox(label="Semantic Recall Query")
                recall_btn = gr.Button("Recall")
                recall_output = gr.Textbox(label="Recall Results")
                file_upload = gr.File(label="Upload File")
                file_output = gr.Textbox(label="File Upload Result")
                image_upload = gr.Image(type="filepath", label="Upload Image")
                image_output = gr.Textbox(label="Image Upload Result")
        state = gr.State([])
        msg = gr.Textbox(label="Your message", placeholder="Type a message and press Enter...")
        # Wire up project selection to chat/recall
        msg.submit(lambda m, h, p: chat_fn(m, h, p), [msg, state, project_dropdown], chatbot, queue=False).then(lambda h: h, None, state)
        recall_btn.click(lambda q, p: recall_fn(q, p), [recall_box, project_dropdown], recall_output)
        file_upload.change(upload_file, file_upload, file_output)
        image_upload.change(upload_image, image_upload, image_output)
        gr.Markdown("""
---
<center><sub><b>Powered by AI</b> &mdash; MazGPT is an AI assistant—responses are AI-generated.<br>
See <a href='https://ai.meta.com/resources/models-and-libraries/llama-acceptable-use-policy/' target='_blank'>Meta Llama Acceptable Use Policy</a>.</sub></center>
""")
    demo.launch()

if __name__ == "__main__":
    launch_gradio()
