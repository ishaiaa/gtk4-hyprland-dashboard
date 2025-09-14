from gi.repository import Gtk, Gtk4LayerShell, Gdk, GLib
from ui.widgets import Calendar, Clock, Power, Weather, Perf, ProcessMonitor, Notifications
from .utils import make_tile, global_click_manager, global_state


import sys


class OverlayPanel(Gtk.ApplicationWindow):
    def __init__(self, app, debug=False):
        super().__init__(application=app, title="Glass Panel")
        self.debug = debug
        self.anchor_state = False
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
        grid.attach(Notifications(), 5, 0, 1, 10)

        self.connect("realize", self.on_realize)

    def on_realize(self, *args):
        print("REALIZE CALLED, DEBUG=", self.debug)
        if not self.debug:
            Gtk4LayerShell.init_for_window(self)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
            for edge in (Gtk4LayerShell.Edge.TOP,
                         Gtk4LayerShell.Edge.RIGHT,
                         Gtk4LayerShell.Edge.BOTTOM,
                         Gtk4LayerShell.Edge.LEFT):
                Gtk4LayerShell.set_anchor(self, edge, True)
            self.toggle_anchors(True)
            Gtk4LayerShell.set_exclusive_zone(self, 0)
            

    def toggle_anchors(self, state):
        print(f'TOGGLE {state}')
        self.anchor_state = state
        
        if self.anchor_state:
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
        else:
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.BACKGROUND)

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.toggle_dashboard()
            return True
        return False

    def on_click(self, controller, n_press, x, y):
        global_click_manager.call_callback("process-deselect-detect-parent", x, y)

    # --------------------------
    # Dashboard fade
    # --------------------------
    
    def show_dashboard(self):
        self.toggle_anchors(True)
        self.remove_css_class("window-hidden")
        self.set_sensitive(True)
        
        global_state.set_visible(True)
        # self.present()
        # self.fade_to(1.0, 300)

    def hide_dashboard(self):
        self.add_css_class("window-hidden")
        # self.set_sensitive(False)
        # self.fade_to(0.0, 300, True)
        
        # global_state.set_visible(False)
        GLib.timeout_add(500, self.hide_timeout)

    def hide_timeout(self):
        self.toggle_anchors(False)
        self.set_sensitive(False)
        global_click_manager.call_callback("process-deselect-detect")
        global_state.set_visible(False)

    def toggle_dashboard(self):
        if self.anchor_state:
            self.hide_dashboard()
        else:
            self.show_dashboard()