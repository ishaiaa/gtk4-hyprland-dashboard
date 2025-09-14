from gi.repository import Gtk, GLib, Pango
from .tile import Tile

class NotificationToast(Gtk.Revealer):
    def __init__(self, notif_data, close_callback):
        super().__init__(transition_type=Gtk.RevealerTransitionType.SLIDE_UP)
        # self.hreveal = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SWING_RIGHT)
        self.set_reveal_child(False)
        self.close_callback = close_callback
        self.discord = False
        self.toast = None
        if(notif_data["app"]!= "discord"):
            self.toast = self.NormalToast(notif_data)
        else:
            self.toast = self.DiscordToast(notif_data)
            self.discord = True
        self.set_child(self.toast)
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self.close_popup)
        self.add_controller(gesture)
    
    class NormalToast(Gtk.Box):
        def __init__(self, n_data):
            super().__init__(
                orientation=Gtk.Orientation.HORIZONTAL, 
                # vexpand=True,
                hexpand=True,
                height_request=183, 
                width_request=480,
                css_classes=["notification-toast"]
            )
            
            self.text_container = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, 
                hexpand=True,
                vexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["text-container"]
            )
            
            if "image" in n_data.keys():
                self.append(n_data["image"])
                
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
                label=n_data["body"], 
                # height_request=140, 
                css_classes=["main-text"]
            )
            
            self.text_container.append(self.summary_text)
            self.text_container.append(self.main_text)
            
            self.append(self.text_container)
        
    class DiscordToast(Gtk.Box):
        def __init__(self, n_data):
            super().__init__(
                orientation=Gtk.Orientation.HORIZONTAL, 
                # vexpand=True,
                hexpand=True,
                height_request=175, 
                width_request=480,
                css_classes=["notification-toast-discord"]
            )            
            
            self.set_direction(Gtk.TextDirection.LTR)
            
            self.image_overlay = Gtk.Overlay(css_classes=["image-overlay"])
            self.bgbox = Gtk.Box(css_classes=["image-overlay-bgbox"])
            
            self.image = n_data["image"]
            
            self.image_overlay.set_child(self.bgbox)
            self.image_overlay.add_overlay(self.image)
                        
            
            self.text_container = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, 
                # hexpand=True,
                vexpand=True,
                halign=Gtk.Align.FILL,
                css_classes=["text-container"]
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
                lines=4,
                hexpand=True,
                halign=Gtk.Align.START, 
                label=n_data["body"].replace("\n", " "), 
                # height_request=140, 
                css_classes=["main-text"]
            )
            
            self.text_container.append(self.summary_text)
            self.text_container.append(self.main_text)
            
            
            
            self.append(self.text_container)
            self.append(self.image_overlay)
            
        
            
    def reveal(self):
        self.set_reveal_child(True)
        if(self.discord):
            GLib.timeout_add(200,self.toast.add_css_class, "shown")
        GLib.timeout_add(5000, self.close_popup)
        
        
        
    def close_popup(self, *args):
        self.toast.remove_css_class("shown")
        self.toast.add_css_class("hide")
        if(self.close_callback):
            self.close_callback(500)
        self.close_callback = None
        GLib.timeout_add(400, self.set_reveal_child, False)
        GLib.timeout_add(600, self.unparent)
        