from pathlib import Path
from gi.repository import Gtk
from .tile import Tile
from ..utils import load_css

class Calendar(Tile):
    def __init__(self):
        super().__init__("calendar", "Calendar")
        cal = Gtk.Calendar()
        cal.set_hexpand(True)
        cal.set_vexpand(True)
        self.append(cal)
        load_css("calendar.css")
        
