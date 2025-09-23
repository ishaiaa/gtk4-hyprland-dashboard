import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".local" / "share" / "hyperdash" / "pinned.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)  # ensure directory exists

MAX_PINS = 16

def read_pinned():
    """Return the list of pinned apps as strings (ordered)."""
    if not CONFIG_PATH.exists():
        return []
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError):
        return []

def pin_unpin(app_name: str):
    """
    Toggle pin/unpin for an app.
    Returns True if pinned after the call, False if unpinned.
    """
    pinned = read_pinned()
    if app_name in pinned:
        pinned.remove(app_name)
        result = False
    else:
        if len(pinned) >= MAX_PINS:
            result = False
        else:
            pinned.append(app_name)
            result = True

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(pinned, f, indent=2)
    except IOError:
        pass
    return result

def overwrite_pins(new_list):
    try:
        to_write = list(new_list)[:MAX_PINS]
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(to_write, f, indent=2)
    except IOError:
        pass