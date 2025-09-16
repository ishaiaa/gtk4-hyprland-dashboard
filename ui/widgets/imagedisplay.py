import os

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
from .tile import Tile

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif")

class ImageDisplay(Tile):
    def __init__(self):
        super().__init__("image-display", "Image Display")
        self.set_overflow(Gtk.Overflow.HIDDEN)
        
        self.menu_open = False
        self.transition_lock = False
        
        self.overlay = Gtk.Overlay(vexpand=True,hexpand=True)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file("/programming/gtk4-hyprland-dashboard/styles/placeholder-image.jpg")
        self.image = Gtk.Picture.new_for_pixbuf(pixbuf)
        self.image.add_css_class("image")
        self.image.set_hexpand(True)
        self.image.set_vexpand(True)
        self.image.set_halign(Gtk.Align.FILL)
        self.image.set_valign(Gtk.Align.FILL)
        
        
        self.image_box = Gtk.Box(hexpand=True,vexpand=True,css_classes=["image-box"])
        self.image_box.append(self.image)
        self.image_box.set_overflow(Gtk.Overflow.HIDDEN)
        # self.overlay.add_overlay(self.image_box)
        
        
        gesture = Gtk.GestureClick.new()
        gesture.set_button(Gdk.BUTTON_SECONDARY)  # 0 = all buttons
        gesture.connect("pressed", self.on_pressed)
        self.add_controller(gesture)
        
        self.file_chooser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True)
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)

        self.path_entry = Gtk.Entry()
        self.path_entry.set_placeholder_text("Enter folder path")
        self.path_entry.connect("activate", self.on_path_entered)
        
        self.completion = Gtk.EntryCompletion()
        self.completion.set_inline_completion(True)
        self.path_entry.set_completion(self.completion)
        
        
        
        self.file_chooser_box.append(self.path_entry)

        # Flowbox in scrolled window
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_max_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.flowbox)
        self.file_chooser_box.append(scroll)
        
        self.overlay.set_child(self.file_chooser_box)
        self.append(self.overlay)
        
        self.store = Gtk.ListStore(str)
        self.completion.set_model(self.store)
        self.completion.set_text_column(0)
        
        self.path_entry.connect("changed", lambda e:self. update_completion(e))

    def update_completion(self, entry):
        text = self.path_entry.get_text()
        self.store.clear()
        dirname = os.path.dirname(text) if os.path.dirname(text) else '.'
        try:
            for name in os.listdir(dirname):
                full = os.path.join(dirname, name)
                if os.path.isdir(full):
                    self.store.append([full])
        except Exception:
            pass

    

    def on_path_entered(self, entry):
        path = entry.get_text()
        if not os.path.isdir(path):
            return

        # Clear flowbox
        for child in self.flowbox:
            self.flowbox.remove(child)

        # Populate thumbnails
        for filename in os.listdir(path):
            if filename.lower().endswith(IMAGE_EXTS):
                fullpath = os.path.join(path, filename)
                # pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                #     fullpath, width=100, height=100, preserve_aspect_ratio=True
                # )
                # thumb = Gtk.Image.new_from_pixbuf(pixbuf)

                # Make clickable
                event_box = Gtk.Label(label=filename)
                # event_box.connect("button-press-event", self.on_thumbnail_clicked, fullpath)
                self.flowbox.append(event_box)

        self.flowbox.show_all()

    def on_thumbnail_clicked(self, widget, event, fullpath):
        print("THUMB CLICK")

    def on_pressed(self, *args):
        if self.transition_lock:
            return
        self.transition_lock = True
        self.menu_open = not self.menu_open
        self.handle_toggle(self.menu_open)
        
        
    def set_transition_lock(self, state):
        self.transition_lock = state
        
    def handle_toggle(self, state):
        if state:
            self.image_box.add_css_class("hidden")
            self.image_box.set_can_focus(False)
            self.image_box.set_can_target(False)
        else:            
            self.image_box.remove_css_class("hidden")
            self.image_box.set_can_focus(True)
            self.image_box.set_can_target(True)
            
        GLib.timeout_add(500, self.set_transition_lock, False)