#!.venv/bin/python3
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

import ctypes
ctypes.CDLL("libgtk4-layer-shell.so")


from ui.utils import load_css
from ui.app import MyApp

import psutil
import json
import subprocess

def get_hyprland_programs():
    # grab clients from Hyprland
    raw = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
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
            "name": name,
            "class": c.get("class"),
            "title": c.get("title"),
            "workspace": c["workspace"]["name"]
        }

    return programs

if __name__ == "__main__":
    for pid, prog in get_hyprland_programs().items():
        print(f"{pid}: {prog}")
    load_css("./styles/style.css")
    load_css("./styles/calendar.css")
    load_css("./styles/power.css")
    load_css("./styles/clock.css")
    load_css("./styles/weather.css")
    load_css("./styles/perf.css")
    app = MyApp()
    app.run()