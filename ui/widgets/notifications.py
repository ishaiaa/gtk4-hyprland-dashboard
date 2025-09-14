from gi.repository import Gtk, GLib, Pango, GdkPixbuf
from .tile import Tile
from pydbus import SessionBus
from ..utils import NotificationDaemon

class Notifications(Tile):
    def __init__(self):
        super().__init__("notifications", "Notifications")
        
        self.daemon = NotificationDaemon.get_instance()
        self.daemon.add_callback(self.notify)
        
        self.scroll_window = Gtk.ScrolledWindow(
            overlay_scrolling=True,
            kinetic_scrolling=True, 
            valign=Gtk.Align.FILL, 
            vexpand=True, 
            hexpand=True, 
            css_classes=["scroll-window"]
        )
        self.scroll_box = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            vexpand=True, 
            hexpand=True, 
            css_classes=["scroll-box"]
        )
        self.scroll_window.set_child(self.scroll_box);
            
        self.append(self.scroll_window)
        
    def notify(self, notif):
        notification = self.Toast(notif)
        self.scroll_box.prepend(notification)
        notification.reveal()
        
    class Toast(Gtk.Revealer):
        def __init__(self, n_data= {"app": "Test", "summary": "Title", "body": "This is a notification"}):
            super().__init__(
                hexpand=True,
                transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                css_classes=["toast"]
            )
            
            self.wrap_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, 
                hexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["wrap-box"]
            )
            
            self.main_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, 
                hexpand=True,
                vexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["main-box"]
            )
            
            self.header = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                hexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["header"]
            )
            
            self.body = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                hexpand=True,
                vexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["body"]
            )
            
            self.text_container = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, 
                hexpand=True,
                vexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["text-container"]
            )
            
            
            
            pixbuf = GdkPixbuf.Pixbuf.new_from_file("/programming/gtk4-hyprland-dashboard/styles/notif-icon.png")
            self.image = Gtk.Image.new_from_pixbuf(pixbuf)
            self.image.add_css_class("image")
            
            if "image" in n_data.keys():
                self.image = n_data["image"]
                
    
            self.app_name = Gtk.Label(
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD,
                ellipsize=Pango.EllipsizeMode.END,
                lines=1,
                hexpand=True,
                halign=Gtk.Align.START, 
                label=n_data["app"].capitalize(), 
                # height_request=45, 
                
                css_classes=["app-name"]
            )

            spacer = Gtk.Box(hexpand=True)
            
            self.close_button = Gtk.Button(
                label="",
                css_classes=["close-button"]
            )
            
            self.summary_text = Gtk.Label(
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD,
                ellipsize=Pango.EllipsizeMode.END,
                lines=1,
                hexpand=True,
                halign=Gtk.Align.START, 
                label=n_data["summary"], 
                # height_request=45, 
                
                css_classes=["summary"]
            )
            self.main_text = Gtk.Label(
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD_CHAR,
                ellipsize=Pango.EllipsizeMode.END,
                lines=5,
                hexpand=True,
                halign=Gtk.Align.START, 
                label=n_data["body"].replace("\n", " "), 
                # height_request=140, 
                css_classes=["main-text"]
            )
            
            self.close_button.connect("clicked", self.close)
            
            self.header.append(self.app_name)
            self.header.append(spacer)
            self.header.append(self.close_button)
            
            self.text_container.append(self.summary_text)
            self.text_container.append(self.main_text)
            
            self.body.append(self.image)
            self.body.append(self.text_container)
            
            self.main_box.append(self.header)
            self.main_box.append(self.body)
            
            self.wrap_box.append(self.main_box)
            
            self.set_child(self.wrap_box)
            
        def reveal(self):
            self.set_reveal_child(True)
            
        def close(self, *args):
            self.set_reveal_child(False)
            GLib.timeout_add(250, self.unparent)