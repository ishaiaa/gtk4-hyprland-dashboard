from gi.repository import Gtk
from .tile import Tile

class Clock(Tile):
    def __init__(self):
        super().__init__("clock", "Clock")
        # (later: update a label every second)
        self.clock_label = Gtk.Label(label="12:34")
        self.append(self.clock_label)