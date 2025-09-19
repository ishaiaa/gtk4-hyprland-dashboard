from gi.repository import Gtk

class Network(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            css_classes=["network-settings"]
        )