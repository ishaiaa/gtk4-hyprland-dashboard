from gi.repository import Gtk, Gtk4LayerShell, Gdk
from ui.widgets import Calendar, Clock, Power, Weather, Perf, ProcessMonitor
from .utils import make_tile, global_click_manager


import sys

DEBUG = "--debug" in sys.argv

class OverlayPanel(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Glass Panel")
        self.set_decorated(False)
        self.set_default_size(1200, 800)

        grid = Gtk.Grid()
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(30)
        grid.set_column_spacing(30)
        grid.set_margin_top(30)
        grid.set_margin_bottom(30)
        grid.set_margin_start(30)
        grid.set_margin_end(30)
        self.set_child(grid)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        click_controller = Gtk.GestureClick()
        click_controller.connect("pressed", self.on_click)
        self.add_controller(click_controller)

        # tiles
        grid.attach(Clock(), 0, 0, 1, 2)
        grid.attach(Weather(), 0, 2, 1, 2)
        grid.attach(Calendar(), 0, 4, 1, 4)
        grid.attach(Power(), 0, 8, 1, 2)
        grid.attach(make_tile("Music Player"), 1, 0, 1, 4)
        grid.attach(make_tile("Settings"), 1, 4, 1, 6)
        # grid.attach(make_tile("Settings Icons"), 1, 9, 1, 1)
        grid.attach(make_tile("Workspaces"), 2, 0, 2, 2)
        grid.attach(make_tile("AppLauncher"), 2, 2, 2, 8)
        # grid.attach(make_tile("Pinned Apps"), 2, 8, 2, 2 nb nvvvvnn)
        grid.attach(Perf(), 4, 0, 1, 4)
        grid.attach(ProcessMonitor(), 4, 4, 1, 6)
        grid.attach(make_tile("Notifications"), 5, 0, 1, 10)

        self.connect("realize", self.on_realize)

    def on_realize(self, *args):
        if not DEBUG:
            Gtk4LayerShell.init_for_window(self)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
            for edge in (Gtk4LayerShell.Edge.TOP,
                         Gtk4LayerShell.Edge.RIGHT,
                         Gtk4LayerShell.Edge.BOTTOM,
                         Gtk4LayerShell.Edge.LEFT):
                Gtk4LayerShell.set_anchor(self, edge, True)
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)
            Gtk4LayerShell.set_exclusive_zone(self, 0)

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            print("Escape pressed → closing panel")
            self.close()
            return True
        return False

    def on_click(self, controller, n_press, x, y):
        pass