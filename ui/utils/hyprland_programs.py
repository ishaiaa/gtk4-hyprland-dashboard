import subprocess
import json
import psutil

def get_hyprland_programs():
    # grab clients from Hyprland
    raw = subprocess.check_output(["hyprctl", "clients", "-j"], text=True, encoding="utf-8", errors="replace")
    clients = json.loads(raw)

    programs = {}
    for c in clients:
        pid = c["pid"]
        try:
            proc = psutil.Process(pid)
            exe = proc.exe()
            name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe, name = None, None

        programs[pid] = {
            "pid": pid,
            "exe": exe,
            "class": c.get("class"),
            "title": c.get("title"),
        }

    return programs