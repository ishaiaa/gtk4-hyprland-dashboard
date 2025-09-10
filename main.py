#!.venv/bin/python3
import os
import pynvml
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

import ctypes
ctypes.CDLL("libgtk4-layer-shell.so")

from ui.utils import load_css
from ui.app import MyApp

if __name__ == "__main__":
    pynvml.nvmlInit()

    load_css("./styles/style.css")
    load_css("./styles/calendar.css")
    load_css("./styles/power.css")
    load_css("./styles/clock.css")
    load_css("./styles/weather.css")
    load_css("./styles/perf.css")
    load_css("./styles/processmonitor.css")
    app = MyApp()
    app.run()