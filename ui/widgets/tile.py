from gi.repository import Gtk

class Tile(Gtk.Box):
    def __init__(self, classname: str, title: str, show_label: bool = False, transparent: bool = False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.classes = ["tile", classname]
        if(not transparent):
            self.classes.append("tile-bg")
        
        self.set_css_classes(self.classes)

        if(show_label):
            lbl = Gtk.Label(label=title)
            lbl.set_xalign(0.5)
            self.append(lbl)