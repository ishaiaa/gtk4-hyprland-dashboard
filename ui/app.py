from gi.repository import Gtk
from .panel import OverlayPanel
from .utils import NotificationDaemon
from .notiflayer import NotificationsLayer

class MyApp(Gtk.Application):
    def __init__(self, debug):
        super().__init__(application_id="dev.ishaia.overlaypanel")
        self.debug = debug
        self.panel = None
        self.notifications_layer = None
        
        

    def do_activate(self, *args):
        if not self.panel:
            self.panel = OverlayPanel(self, self.debug)
        self.panel.present()  # ensures window is on top
        
        if not self.notifications_layer:
            self.notifications_layer = NotificationsLayer(self)
        self.notifications_layer.present()  # ensures window is on top

    def toggle_visibility(self):
        if self.panel:
            self.panel.toggle_dashboard()
            
    def notify_test(self, notif):
        print("NOTIFICATION GO BRR")
        print(notif)