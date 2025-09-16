#!/programming/gtk4-hyprland-dashboard/.venv/bin/python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="GTK4 Test")
        self.set_default_size(400, 300)

win = MyWindow()
win.present()

# Use GLib main loop instead of Gtk.main()
from gi.repository import GLib
loop = GLib.MainLoop()
loop.run()
