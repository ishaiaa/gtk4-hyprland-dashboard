from gi.repository import Gtk, Gdk
from .tile import Tile

class Settings(Tile):
    def __init__(self):
        super().__init__("settings", "Settings", False, True)
        self.grid = Gtk.Grid(
            row_homogeneous=True,
            column_homogeneous=True,
            row_spacing=20,
            column_spacing=20,
            css_classes=["settings-grid-main"]
        )
        
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            vexpand=True,
            css_classes=["tile-bg", "main-box"]
        )
        
        self.buttons_grid = Gtk.Grid(
            row_homogeneous=True,
            column_homogeneous=True,
            row_spacing=20,
            column_spacing=20,
            css_classes=["buttons-grid"]
        )
        
        self.toggle_buttons = []

        self.toggle_buttons.append(self.SettingsSelectButton(self, "", "wifi"))
        self.toggle_buttons.append(self.SettingsSelectButton(self, "", "bluetooth"))#
        self.toggle_buttons.append(self.SettingsSelectButton(self, "", "volume"))
        self.toggle_buttons.append(self.SettingsSelectButton(self, "", "light"))
        
        self.buttons_grid.attach(self.toggle_buttons[0], 0,0,1,1)
        self.buttons_grid.attach(self.toggle_buttons[1], 1,0,1,1) #
        self.buttons_grid.attach(self.toggle_buttons[2], 2,0,1,1)
        self.buttons_grid.attach(self.toggle_buttons[3], 3,0,1,1)
        
        
        
        #STACK
        
        self.header_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                hexpand=True,
                valign=Gtk.Align.CENTER,
                css_classes=["header"]
            )
        
        self.title = Gtk.Label(css_classes=["title"], label="Settings")
        
        self.header_box.append(self.title)
        
        self.stack = Gtk.Stack(hhomogeneous=True, vexpand=True, hexpand=True)
        
        self.stack.add_titled(Gtk.Label(label="TEMP BOX 1"), "wifi", "WIFI BOX")
        self.stack.add_titled(Gtk.Label(label="TEMP BOX 2"), "bluetooth", "BLUETOOTH BOX")
        self.stack.add_titled(Gtk.Label(label="TEMP BOX 3"), "volume", "VOLUME BOX")
        self.stack.add_titled(Gtk.Label(label="TEMP BOX 4"), "light", "LIGHT BOX")
        
        self.main_box.append(self.header_box)
        self.main_box.append(self.stack)
        
        self.grid.attach(self.main_box, 0,0,4,5)
        self.grid.attach(self.buttons_grid, 0,5,4,1)
        
        
        self.handle_toggle(self.toggle_buttons[0])
        self.append(self.grid)
        
        
    def handle_toggle(self, child):
        selected = None

        titles = {
            "wifi": "Network Settings",
            "bluetooth": "Bluetooth Settings",
            "volume": "Audio Settings",
            "light": "Lighting Settings"
        }
        title = ""
        
        for c in self.toggle_buttons:
            c.remove_css_class("active")
            if c.name == child.name:
                c.add_css_class("active")
                selected = c.name
                title = titles[c.name]
                
        self.stack.set_visible_child_name(selected)
        self.title.set_text(title)
        
        
        
    class SettingsSelectButton(Gtk.Box):
        def __init__(self, parent, icon, name, callback=None):
            super().__init__(
                vexpand=True,
                hexpand=True,
                cursor=Gdk.Cursor.new_from_name("pointer"),
                css_classes=["select-button", "tile-bg", name]
            )
            
            self.parent = parent
            self.icon = icon
            self.name = name
            self.callback = callback
        
            self.label = Gtk.Label(
                label=self.icon,
                valign=Gtk.Align.CENTER,
                halign=Gtk.Align.CENTER,
                xalign=0.5,
                hexpand=True,
                vexpand=True,
                css_classes=["icon"]
            )
            
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self.handle_press)
            self.add_controller(gesture)
            
            self.append(self.label)
        
        def handle_press(self, *args):
            self.parent.handle_toggle(self)