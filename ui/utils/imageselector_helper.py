import os
import json

APP_DATA_DIR = os.path.join(os.path.expanduser("~/.local/share/hyperdash"))
STATE_FILE = os.path.join(APP_DATA_DIR, "state.json")
os.makedirs(APP_DATA_DIR, exist_ok=True)    


def save_image_path(selected_file):
    data = {"used_image": selected_file}
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def load_image_path():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        return data.get("used_image")
