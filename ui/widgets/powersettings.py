import gi, time
from gi.repository import Gtk, GLib
from .tile import Tile
from .battery import Battery

class Power(Tile):
    def __init__(self):
        super().__init__("power", "Power Settings", False, True)
        grid = Gtk.Grid()
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(20)
        grid.set_column_spacing(20)
        
        grid.attach(self.ConfirmButton("shutdown", "", self.shutdown_callback), 0, 0, 1, 1);
        grid.attach(self.ConfirmButton("logout", "", self.logout_callback), 0, 1, 1, 1);
        grid.attach(self.ConfirmButton("reboot", "", self.reboot_callback), 1, 0, 1, 1);
        grid.attach(self.ConfirmButton("windows", "", self.windows_callback), 1, 1, 1, 1);
        
        big_grid = Gtk.Grid()
        big_grid.set_row_homogeneous(True)
        big_grid.set_column_homogeneous(True)
        big_grid.set_row_spacing(40)
        big_grid.set_column_spacing(40)
        self.append(big_grid)
        big_grid.attach(grid, 0,0,1,1)
        big_grid.attach(Battery(), 1,0,1,1)
        
        
    class ConfirmButton(Gtk.Frame):
        def __init__(self, type: str, icon_glyph: str, callback):
            super().__init__()
            self.set_hexpand(True)
            self.set_vexpand(True)
            
            self.clicked = False
            self.confirmed = False
            self.callback = callback
            self.hold_timeout_id = None


            # Main overlay container
            overlay = Gtk.Overlay()
            overlay.set_hexpand(True)
            overlay.set_vexpand(True)

            # Base box (your actual button contents)
            box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            box.set_css_classes(["button-box"])

            confirmtext = Gtk.Label(label="HOLD")
            confirmtext.set_css_classes(["button-confirmtext"])
            box.append(confirmtext)

            icon = Gtk.Label(label=icon_glyph)
            icon.set_css_classes(["button-icon"])
            box.append(icon)

            # Add main content to overlay
            overlay.set_child(box)

            # Overlay box (full size, for styling)
            overlay_box = Gtk.Box()
            overlay_box.set_css_classes(["button-overlay"])
            overlay_box.set_hexpand(True)
            overlay_box.set_vexpand(True)
            

            # Add overlay layer (it sits above box but doesn’t shift it)
            overlay.add_overlay(overlay_box)

            # Attach overlay to button
            self.set_child(overlay)

            self.set_css_classes(["button", type])
            # self.connect("clicked", self.on_click)
            
            gesture = Gtk.GestureClick.new()
            gesture.connect("pressed", self.on_press)
            gesture.connect("released", self.on_release)
            
            overlay.set_focusable(True)  # ensures gesture gets events
            overlay.set_can_target(True)

            overlay.add_controller(gesture)

        def on_press(self, gesture, n_press, x, y):
            print("press")
            if self.clicked and not self.confirmed:
                self.hold_timeout_id = GLib.timeout_add_seconds(1, self.callback_wrapper)
                
        def on_release(self, gesture, n_press, x, y):
            # Cancel timers
            if self.hold_timeout_id:
                GLib.source_remove(self.hold_timeout_id)
                self.hold_timeout_id = None
                
            # Toggle confirm state safely
            if not self.confirmed:
                self.clicked = not self.clicked
                if self.clicked:
                    self.add_css_class("confirm")
                else:
                    self.remove_css_class("confirm")
                
        def callback_wrapper(self):
            self.confirmed = True
            self.add_css_class("confirmed")
            self.callback()
                        
    
    def shutdown_callback(self):
        print("SHUTDOWN!")
        
    def reboot_callback(self):
        print("REBOOT!")
        
    def logout_callback(self):
        print("LOGOUT!")
        
    def windows_callback(self):
        print("BOOT TO WINDOWS!")
        
        