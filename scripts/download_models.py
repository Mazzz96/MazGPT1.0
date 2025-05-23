import os
import yaml
from huggingface_hub import snapshot_download

CONFIG_PATH = os.path.join('model', 'model_config.yaml')
MODELS_DIR = 'models'

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

os.makedirs(MODELS_DIR, exist_ok=True)

for model in config['models']:
    repo_id = model['path']
    # Use the last part of the repo_id as the local dir name (e.g., Meta-Llama-3-8B-Instruct)
    local_dir_name = repo_id.split('/')[-1]
    local_dir = os.path.join(MODELS_DIR, local_dir_name)
    if not os.path.exists(local_dir):
        print(f"Downloading {repo_id} to {local_dir}...")
        snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)
    else:
        print(f"Model already exists: {local_dir}")
    # Update model_config.yaml to use the local path
    model['path'] = local_dir

# Save the updated config
with open(CONFIG_PATH, 'w') as f:
    yaml.safe_dump(config, f)

print("All models are downloaded and model_config.yaml is updated with local paths.")
