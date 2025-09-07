from gi.repository import Gtk
from .panel import OverlayPanel

class MyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.ishaia.overlaypanel")

    def do_activate(self, *args):
        win = OverlayPanel(self)
        win.present()