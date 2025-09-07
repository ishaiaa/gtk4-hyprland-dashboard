#!.venv/bin/python3
import ctypes
ctypes.CDLL("libgtk4-layer-shell.so")

from ui.utils import load_css
from ui.app import MyApp

if __name__ == "__main__":
    load_css("style.css")
    load_css("calendar.css")
    load_css("power.css")
    app = MyApp()
    app.run()