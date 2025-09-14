import cairo 

from gi.repository import Gtk, Gtk4LayerShell, Gdk, GLib
from ui.widgets import NotificationToast
from .utils import make_tile, global_click_manager, global_state, NotificationDaemon


class NotificationsLayer(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app, title="Glass Panel", css_classes=["notifications-layer-window"])
        self.set_decorated(False)
        self.set_default_size(480, 1440)
        self.childrencount = 0
        
        self.child_watchers = {}
        self.daemon = NotificationDaemon.get_instance()
        self.daemon.add_callback(self.notify)

        self.container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            vexpand=True,
            halign=Gtk.Align.START,
            valign=Gtk.Align.END,
            css_classes=["notifications-layer"]
        )
        
        self.container.set_direction(Gtk.TextDirection.LTR)
        self.set_direction(Gtk.TextDirection.LTR)
        
        self.set_child(self.container)

        self.connect("realize", self.on_realize)
        
    def notify(self, notif):
        notification = NotificationToast(notif, self.remove_child)
        self.childrencount += 1
        self.container.append(notification)
        # handler_id = notification.connect("notify::parent", self.on_child_parent_changed)
        # self.child_watchers[notification] = handler_id
        self.adjust_region()
        GLib.idle_add(notification.reveal)
        
        
    def remove_child(self, timeout):
        GLib.timeout_add(timeout, self.__remove_child)
        
    def __remove_child(self):
        self.childrencount -= 1
        self.adjust_region()
        
    def on_realize(self, *args):
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        for edge in (Gtk4LayerShell.Edge.BOTTOM,
                    #  Gtk4LayerShell.Edge.TOP,
                     Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(self, edge, True)
        # Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        # Gtk4LayerShell.set_exclusive_zone(self, 0)
        self.adjust_region()
        
        
        
    def adjust_region(self):
        n = self.childrencount
        print(f'Adjust n {n}')
        surface = self.get_native().get_surface()
        region = cairo.Region(cairo.RectangleInt(0, 0, 0, 0))
        if n > 0:
            region.union(cairo.RectangleInt(0, 1440-(183*n), 480, 183*n))
        GLib.idle_add(surface.set_input_region, region)