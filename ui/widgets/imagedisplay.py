import os

from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, Pango
from .tile import Tile

from ..utils import save_image_path, load_image_path

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif")

class ImageDisplay(Tile):
    def __init__(self):
        super().__init__("image-display", "Image Display")
        self.set_overflow(Gtk.Overflow.HIDDEN)
        
        self.thumbnail_pool = ThreadPoolExecutor(max_workers=2)
        self.active_futures = set()
        
        self.menu_open = False
        self.transition_lock = False
        
        self.overlay = Gtk.Overlay(vexpand=True,hexpand=True)
        self.image = Gtk.Picture()
        self.image.add_css_class("image")
        self.image.set_hexpand(True)
        self.image.set_vexpand(True)
        self.image.set_halign(Gtk.Align.FILL)
        self.image.set_valign(Gtk.Align.FILL)
        
        image_path = load_image_path()
        filesystem_path = ""
        
        if image_path == None:
            filesystem_path = os.path.expanduser("~/")
            base_dir = os.path.dirname(__file__) 
            image_path = os.path.abspath(os.path.join(base_dir, "../../styles/placeholder-image.jpg"))
        else:
            filesystem_path = os.path.dirname(image_path)
            
        GLib.idle_add(self.update_image, image_path)
        
        self.image_box = Gtk.Box(hexpand=True,vexpand=True,css_classes=["image-box"])
        self.image_box.append(self.image)
        self.image_box.set_overflow(Gtk.Overflow.HIDDEN)
        self.overlay.add_overlay(self.image_box)
        
        
        gesture = Gtk.GestureClick.new()
        gesture.set_button(Gdk.BUTTON_SECONDARY)  # 0 = all buttons
        gesture.connect("pressed", self.on_pressed)
        self.add_controller(gesture)
        
        self.file_chooser_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, 
            vexpand=True, 
            overflow=Gtk.Overflow.HIDDEN,
            hexpand=True,
            css_classes=["file-chooser-box"]    
        )
        self.header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, 
            hexpand=True,
            css_classes=["header"]
        )

        self.path_entry = Gtk.Entry(hexpand=True, css_classes=["entry-box"])
        self.path_entry.set_placeholder_text("Enter path...")
        self.path_entry.connect("activate", self.on_path_entered)
        
        self.completion = Gtk.EntryCompletion()
        self.completion.set_inline_completion(True)
        self.path_entry.set_completion(self.completion)
        
        self.store = Gtk.ListStore(str)
        self.completion.set_model(self.store)
        self.completion.set_text_column(0)
        
        self.path_entry.connect("changed", lambda e:self. update_completion(e))
        
        self.cancel_button = Gtk.Button(
            label="Cancel", 
            cursor=Gdk.Cursor.new_from_name("pointer"),
            css_classes=["cancel-button"])
        self.cancel_button.connect("clicked", self.on_pressed)
        
        self.header.append(self.path_entry)
        self.header.append(self.cancel_button)

        self.file_list = Gtk.ListBox(hexpand=True, vexpand=True, css_classes=["file-list"])
        self.file_list.set_selection_mode(Gtk.SelectionMode.NONE)

        self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True, css_classes=["scroll-window"])
        self.scroll.set_child(self.file_list)
        
        self.file_chooser_box.append(self.header)
        self.file_chooser_box.append(self.scroll)
        
        self.overlay.set_child(self.file_chooser_box)
        # self.path_entry.set_text(filesystem_path)
        
        self.append(self.overlay)
        GLib.idle_add(self.on_path_entered, filesystem_path)
        
    def load_thumbnail_job(self, icon_widget, full_path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                full_path, 50, 50, preserve_aspect_ratio=True
            )
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            # drop Python references
            pixbuf = None
            GLib.idle_add(icon_widget.set_from_paintable, texture)
        except Exception as e:
            print("Failed to load thumbnail:", e)
            
    def update_image(self, image_path):
        save_image_path(image_path)

        # Get box size
        allocation = self.image_box.get_allocation()
        box_width = allocation.width
        box_height = allocation.height

        if box_width == 0 or box_height == 0:
            # box not realized yet, fallback to original size
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            img_width = pixbuf.get_width()
            img_height = pixbuf.get_height()

            box_ratio = box_width / box_height
            img_ratio = img_width / img_height

            # cover scaling with cropping
            if img_ratio > box_ratio:
                # image wider -> scale height, crop width
                scale_factor = box_height / img_height
                new_width = int(img_width * scale_factor)
                new_height = box_height
                pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
                x_offset = (new_width - box_width) // 2
                pixbuf = pixbuf.new_subpixbuf(x_offset, 0, box_width, box_height)
            else:
                # image taller -> scale width, crop height
                scale_factor = box_width / img_width
                new_width = box_width
                new_height = int(img_height * scale_factor)
                pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
                y_offset = (new_height - box_height) // 2
                pixbuf = pixbuf.new_subpixbuf(0, y_offset, box_width, box_height)

        # Update Gtk.Picture
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.image.set_paintable(texture)

        GLib.idle_add(self.handle_toggle, False)
        
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
        
        path = ""
        if type(entry) == type("string"):
            path = entry
        else:
            path = entry.get_text()
            
        self.path_entry.set_text(path)
        self.path_entry.get_root().set_focus(None)
        
        for row in self.file_list:
            for child in row:
                if isinstance(child, Gtk.Image):
                    child.set_from_paintable(None)
        
        self.file_list.remove_all()
        if not os.path.isdir(path):
            return

        icon_theme = Gtk.IconTheme.get_for_display(self.get_display())
        folder_icon = icon_theme.lookup_icon("folder", None, 40, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)
        placeholder_icon = icon_theme.lookup_icon("image-x-generic", None, 40, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)


        # Sort: directories first, then files
        entries = sorted(
            os.listdir(path),
            key=lambda f: (not os.path.isdir(os.path.join(path, f)), f.lower())
        )
        
        if path != "/":
            GLib.idle_add(self.append_row, "..", path, True, lambda pathdir=os.path.dirname(path): self.on_path_entered(pathdir), placeholder_icon, folder_icon)

        for filename in entries:
            fullpath = os.path.join(path, filename)

            if os.path.isdir(fullpath):
                GLib.idle_add(self.append_row, filename, fullpath, True, lambda pathdir=fullpath: self.on_path_entered(pathdir), placeholder_icon, folder_icon)

            elif filename.lower().endswith(IMAGE_EXTS):
                GLib.idle_add(self.append_row, filename, fullpath, False, lambda pathdir=fullpath: self.update_image(pathdir), placeholder_icon, folder_icon)

    def append_row(self, filename, fullpath, isFolder, callback, placeholdericon, foldericon):
        self.file_list.append(self.FileRow(filename, fullpath, isFolder, callback, placeholdericon, foldericon, parent=self))
        

    def on_pressed(self, *args):
        if self.transition_lock:
            return
        self.transition_lock = True
        self.handle_toggle(not self.menu_open)
        
        
    def set_transition_lock(self, state):
        self.transition_lock = state
        
    def handle_toggle(self, state):
        self.menu_open = state
        if state:
            self.image_box.add_css_class("hidden")
            self.image_box.set_can_focus(False)
            self.image_box.set_can_target(False)
            
            self.file_chooser_box.set_visible(True)
            self.file_chooser_box.set_can_focus(True)
            self.file_chooser_box.set_can_target(True)
        else:            
            self.image_box.remove_css_class("hidden")
            self.image_box.set_can_focus(True)
            self.image_box.set_can_target(True)
            
            self.file_chooser_box.set_visible(False)
            self.file_chooser_box.set_can_focus(False)
            self.file_chooser_box.set_can_target(False)
            
        GLib.timeout_add(500, self.set_transition_lock, False)
        
    class FileRow(Gtk.Box):
        def __init__(self, filename, fullpath, isFolder, callback, placeholdericon, foldericon, parent):
            super().__init__(
                orientation=Gtk.Orientation.HORIZONTAL, 
                hexpand=True,
                css_classes=["file-row"])
            self.parent = parent
            self.full_path = fullpath
            self.callback = callback
            self.press_count = 0
            
            if isFolder:
                self.icon = Gtk.Image.new_from_paintable(foldericon)
            else:
                self.icon = Gtk.Image.new_from_paintable(placeholdericon)
                future = self.parent.thumbnail_pool.submit(
                    self.parent.load_thumbnail_job, self.icon, self.full_path
                )
                self.parent.active_futures.add(future)
                future.add_done_callback(lambda f: self.parent.active_futures.discard(f))
            
            self.icon.add_css_class("file-icon")
            self.append(self.icon)
            self.append(Gtk.Label(label=filename, ellipsize=Pango.EllipsizeMode.END, halign=Gtk.Align.START, hexpand=True, css_classes=["file-name"]))
            
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self.click_callback)
            self.add_controller(gesture)

        def load_thumbnail(self):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.full_path, 50, 50, preserve_aspect_ratio=True)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                GLib.idle_add(self.icon.set_from_paintable, texture)
                texture = None
                pixbuf = None
                del(texture)
                del(pixbuf)
            except Exception as e:
                print("Failed to load thumbnail:", e)
            
        def decrement_click_count(self):
            self.press_count -= 1
            
            if self.press_count < 0:
                self.press_count = 0
            
        def click_callback(self, *args):
            self.press_count+=1
            GLib.timeout_add(500, self.decrement_click_count)
            
            if(self.press_count >= 2):
                self.press_count = 0
                self.callback()
                