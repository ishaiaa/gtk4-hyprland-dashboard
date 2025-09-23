import os
import configparser
import glob
import json
from pathlib import Path

USAGE_DB = Path.home() / ".cache/hyperdash/app_usage.json"

def load_usage():
    if USAGE_DB.exists():
        try:
            with open(USAGE_DB, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_usage(usage):
    USAGE_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_DB, "w") as f:
        json.dump(usage, f)

def increment_usage(exec_name):
    usage = load_usage()
    usage[exec_name] = usage.get(exec_name, 0) + 1
    save_usage(usage)

def get_applications(keyword=None):
    # Directories to scan
    dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        str(Path.home() / ".local/share/applications"),
    ]
    desktop_files = []
    for d in dirs:
        if os.path.isdir(d):
            desktop_files.extend(glob.glob(os.path.join(d, "*.desktop")))

    apps = []
    for file in desktop_files:
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(file)
            if "Desktop Entry" not in config:
                continue
            entry = config["Desktop Entry"]

            if entry.get("NoDisplay", "false").lower() == "true":
                continue

            name = entry.get("Name")
            exec_cmd = entry.get("Exec")
            icon = entry.get("Icon")

            if not name or not exec_cmd:
                continue


            app = {
                "name": name, 
                "executable": exec_cmd, 
                "icon": icon,
                "isAbsolute": os.path.isabs(icon) if icon else False    
            }
            
            if keyword is None or keyword.lower() in name.lower():
                apps.append(app)
        except Exception:
            continue

    # Sort by usage
    usage = load_usage()
    apps.sort(key=lambda a: usage.get(a["executable"], 0), reverse=True)
    return apps