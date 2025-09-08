#!.venv/bin/python3
import os

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

import ctypes
ctypes.CDLL("libgtk4-layer-shell.so")


from ui.utils import load_css
from ui.app import MyApp

if __name__ == "__main__":
    load_css("./styles/style.css")
    load_css("./styles/calendar.css")
    load_css("./styles/power.css")
    load_css("./styles/clock.css")
    app = MyApp()
    app.run()