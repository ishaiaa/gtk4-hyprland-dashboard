
import os
import shlex
import shutil
import subprocess

from concurrent.futures import ThreadPoolExecutor
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
from .tile import Tile
from ..utils import get_applications,increment_usage, global_callback_manager, read_pinned, pin_unpin, overwrite_pins
class AppLauncher(Tile):
    def __init__(self):
        super().__init__("app-launcher", "App Launcher", False, True)
        
        self.thumbnail_pool = ThreadPoolExecutor(max_workers=2)
        self.active_futures = set()
        
        self.icon_theme = Gtk.IconTheme.get_for_display(self.get_display())
        self.placeholder_icon = self.icon_theme.lookup_icon("application-x-executable", None, 80, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)
        
        self.pinned_apps_list = read_pinned()
        
        self.grid = Gtk.Grid(
            row_spacing=30,
            column_spacing=30,
            row_homogeneous=True,
            column_homogeneous=True,
            
        )
        
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            vexpand=True,
            css_classes=["tile-bg", "main-box"]
        )
        
        self.pinned_apps = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            vexpand=True,
            css_classes=["tile-bg", "pinned-apps"]
        )
            
        #APP_LAUNCHER
            
        self.entry_box = Gtk.Entry(hexpand=True, css_classes=["entry-box"])
        self.entry_box.set_placeholder_text("Search applications...")
        self.entry_box.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "system-search")
        
        self.scroll_window = Gtk.ScrolledWindow(
            hexpand=True,
            vexpand=True,
            css_classes=["scroll-window"]
        )
        
        self.flow_box = Gtk.FlowBox(
            hexpand=True,
            valign=Gtk.Align.START,
            halign=Gtk.Align.START,
            min_children_per_line=5,
            max_children_per_line=5,
            selection_mode=Gtk.SelectionMode.SINGLE,
            css_classes=["flow-box"],
            row_spacing=1,
            column_spacing=1,
            homogeneous=True,
        )
        
        self.scroll_window.set_child(self.flow_box)
        
        self.main_box.append(self.entry_box)
        self.main_box.append(self.scroll_window)
        
        self.entry_box.connect("changed", self.filter_app_list)
        self.flow_box.connect("child-activated", self.on_child_activated)
        
        
        #PINNED APPS
        
        self.reorder_buffer = None
        
        self.pinned_apps_flowbox = Gtk.FlowBox(
            min_children_per_line=8,
            max_children_per_line=8,
            selection_mode=Gtk.SelectionMode.NONE,
            vexpand=True,
            hexpand=True,
            homogeneous=True,
            css_classes=["pinned-apps-flowbox"]
        )
        
        self.pinned_apps.append(self.pinned_apps_flowbox)
        
        self.grid.attach(self.main_box, 0,0,8,6)
        self.grid.attach(self.pinned_apps, 0,7,8,2)
        
        self.append(self.grid)
        self.update_app_list()
        
        global_callback_manager.create_callback("update-app-launcher")
        global_callback_manager.attach_to_callback("update-app-launcher", self.update_app_list)
        
        self.update_pins()
        
    def handle_reorder(self, child):
        if self.reorder_buffer == None:
            self.reorder_buffer = child
            child.add_css_class("swap-tile")
            return
        
        if self.reorder_buffer == child:
            self.reorder_buffer = None
            child.remove_css_class("swap-tile")
            return
        
        flow_box_child_1 = self.reorder_buffer.get_parent()
        fbc_index_1 = flow_box_child_1.get_index()
        flow_box_child_2 = child.get_parent()
        fbc_index_2 = flow_box_child_2.get_index()
        
        self.pinned_apps_flowbox.remove(flow_box_child_1)
        self.pinned_apps_flowbox.remove(flow_box_child_2)
        
        if fbc_index_2 > fbc_index_1:
            self.pinned_apps_flowbox.insert(flow_box_child_2, fbc_index_1)
            self.pinned_apps_flowbox.insert(flow_box_child_1, fbc_index_2)
        else:
            self.pinned_apps_flowbox.insert(flow_box_child_1, fbc_index_2)
            self.pinned_apps_flowbox.insert(flow_box_child_2, fbc_index_1)
            
        self.reorder_buffer.remove_css_class("swap-tile")
        child.remove_css_class("swap-tile")
        self.reorder_buffer = None
        
        #rebuild pin list
        pinned_app_list_reordered = []
        
        
        for c in self.pinned_apps_flowbox:
            child = c.get_child()
            if not child.filler:
                pinned_app_list_reordered.append(child.executable)
                
        overwrite_pins(pinned_app_list_reordered)
        self.pinned_apps_list = pinned_app_list_reordered
        
            
    def handle_pin(self, pin):
        pin_unpin(pin)
        self.pinned_apps_list = read_pinned()
        self.update_pins()
        
    def update_pins(self):
        app_pins = self.pinned_apps_list
        termination_list = []
        child_count = 0
        
        for c in self.pinned_apps_flowbox:
            child = c.get_child()
            
            if child.filler:
                termination_list.append(c)
                
            else:
                if child.executable not in self.pinned_apps_list:
                    termination_list.append(c)
                    
                if child.executable in self.pinned_apps_list:
                    app_pins.remove(child.executable)
                    child_count += 1
                
        for c in termination_list:
            self.pinned_apps_flowbox.remove(c)
            
        del(termination_list)
                
        data_sets = [None for i in range(len(app_pins))]
        print(data_sets)
                
        for c in self.flow_box:
            child = c.get_child()
            if child.executable in app_pins:
                index = app_pins.index(child.executable)
                data_sets[index]=child.data.copy()
                child_count += 1
            
        print(*data_sets, sep="\n")
            
        for data in data_sets:
            self.pinned_apps_flowbox.append(self.PinnedApp(False, self, data, self.placeholder_icon))
            
            
        gaps_to_fill = 16-child_count
        for i in range(gaps_to_fill):
            self.pinned_apps_flowbox.append(self.PinnedApp(True, self))
            
        
    def on_child_activated(self, parent, child, *args):
        child.get_child().launch()
        
    def update_app_list(self, *args):        
        self.entry_box.set_text("")
        self.flow_box.remove_all()
        
        for data in get_applications():
            self.flow_box.append(self.AppTile(self, data, self.placeholder_icon))
            
    def filter_app_list(self, *args):
        search = self.entry_box.get_text()
        for child in self.flow_box:
            app_tile = child.get_child()
            if search.lower() in app_tile.name.lower() or search.lower() in app_tile.executable.lower():
                child.set_visible(True)
            else:
                child.set_visible(False)

        
        
    def load_thumbnail_job(self, icon_widget, icon_string, is_absolute):
        try:
            texture = None
            if is_absolute:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_string, 130, 130)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                pixbuf = None
                
            else:
                texture = self.icon_theme.lookup_icon(
                    icon_string, 
                    None,
                    130, 
                    1, 
                    Gtk.TextDirection.NONE, 
                    0)
        
            GLib.idle_add(icon_widget.set_from_paintable, texture)
        except Exception as e:
            print("Failed to load thumbnail:", e)
            
        
    class AppTile(Gtk.Overlay):
        def __init__(self, parent, data, placeholder_icon):
            super().__init__(
                cursor=Gdk.Cursor.new_from_name("pointer"),
                hexpand=True,
                vexpand=False,
                halign=Gtk.Align.FILL,
                valign=Gtk.Align.START,
                css_classes=["app-tile"],
            )
            
            self.tile_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                hexpand=True,
                vexpand=False,
                halign=Gtk.Align.FILL,
                valign=Gtk.Align.START,
                css_classes=["app-tile-box"],
            )
            
            self.data = data
            self.name = data["name"]
            self.parent = parent
            
            self.executable = data["executable"]
                
                
            self.icon = Gtk.Image.new_from_paintable(placeholder_icon)
            future = self.parent.thumbnail_pool.submit(
                self.parent.load_thumbnail_job, self.icon, data["icon"], data["isAbsolute"]
            )
            self.parent.active_futures.add(future)
            future.add_done_callback(lambda f: self.parent.active_futures.discard(f))
            
            self.icon.add_css_class("app-icon")
            
            self.label = Gtk.Label(
                label = data["name"],
                wrap_mode=Pango.WrapMode.WORD_CHAR,
                lines=3,
                valign=Gtk.Align.CENTER,
                halign=Gtk.Align.CENTER,
                justify=Gtk.Justification.CENTER,
                ellipsize=Pango.EllipsizeMode.END,
                css_classes=["app-title"]
            )
                
            self.tile_box.append(self.icon)
            self.tile_box.append(self.label)
            
            self.overlay_box = Gtk.Box(
                hexpand=True,
                vexpand=True,
                valign=Gtk.Align.FILL,
                halign=Gtk.Align.FILL,
                css_classes=["overlay-box"]
            )
            
            self.overlay_box_icon = Gtk.Box(
                valign=Gtk.Align.START,
                halign=Gtk.Align.END,
                css_classes=["overlay-box-icon"]
            )
            
            self.pin_icon = Gtk.Label(
                label="",
                css_classes=["overlay-box-icon-pin"]
            )
            
            # self.overlay_box.append(self.overlay_box_icon)
            self.overlay_box_icon.append(self.pin_icon)
            
            gesture = Gtk.GestureClick(button=Gdk.BUTTON_SECONDARY)
            gesture.connect("pressed", self.pin_app_toggle)
            self.add_controller(gesture)
            
            self.set_child(self.tile_box)
            self.add_overlay(self.overlay_box_icon)
            
            self.update_pin_state()
            
        def pin_app_toggle(self, *args):
            self.parent.handle_pin(self.executable)
            self.update_pin_state()
                
        def update_pin_state(self):
            ispinned = self.executable in read_pinned()
            if ispinned:
                self.add_css_class("pinned")
            else:
                self.remove_css_class("pinned")
                
                
        def launch(self):
            increment_usage(self.executable)
            self.run_app(self.executable)
            global_callback_manager.call_callback("hide-dashboard")
            
        def run_app(self, exec_line):
            args = shlex.split(exec_line)
            exe = args[0]

            # Redirect stdout/stderr to /dev/null so child logs do not appear in parent
            with open(os.devnull, "wb") as devnull:
                if os.path.isabs(exe):
                    subprocess.Popen(
                        args,
                        start_new_session=True,
                        stdout=devnull,
                        stderr=devnull,
                        cwd=os.path.expanduser("~")
                    )
                else:
                    resolved = shutil.which(exe)
                    if resolved:
                        subprocess.Popen(
                            [resolved] + args[1:],
                            start_new_session=True,
                            stdout=devnull,
                            stderr=devnull,
                            cwd=os.path.expanduser("~")
                        )
                    else:
                        print(f"Command not found: {exe}")
                        
    class PinnedApp(Gtk.Box):
        def __init__(self, filler, parent=None, data=None, placeholder_icon=None):
            super().__init__(
                cursor=Gdk.Cursor.new_from_name("pointer"),
                hexpand=True,
                vexpand=False,
                halign=Gtk.Align.FILL,
                valign=Gtk.Align.FILL,
                css_classes=["pinned-app"],
            )
            
            self.filler = False
            if filler:
                self.filler = True
                return
            
            self.add_css_class("not-empty")
            
            self.name = data["name"]
            self.parent = parent
            self.executable = data["executable"]
                
            self.icon = Gtk.Image.new_from_paintable(placeholder_icon)
            future = self.parent.thumbnail_pool.submit(
                self.parent.load_thumbnail_job, self.icon, data["icon"], data["isAbsolute"]
            )
            self.parent.active_futures.add(future)
            future.add_done_callback(lambda f: self.parent.active_futures.discard(f))
            
            self.icon.add_css_class("pinned-app-icon")
            self.icon.set_halign(Gtk.Align.FILL)
            self.icon.set_valign(Gtk.Align.FILL)
            self.icon.set_hexpand(True)
            self.icon.set_vexpand(True)
            
            gesture_left = Gtk.GestureClick(button=Gdk.BUTTON_PRIMARY)
            gesture_left.connect("pressed", self.launch)
            self.add_controller(gesture_left)
            
            gesture_right = Gtk.GestureClick(button=Gdk.BUTTON_SECONDARY)
            gesture_right.connect("pressed", self.move_handler)
            self.add_controller(gesture_right)
            
            self.append(self.icon)
            
        def move_handler(self, *args):
            self.parent.handle_reorder(self)
            
        def launch(self, *args):
            increment_usage(self.executable)
            self.run_app(self.executable)
            global_callback_manager.call_callback("hide-dashboard")
            
        def run_app(self, exec_line):
            args = shlex.split(exec_line)
            exe = args[0]

            # Redirect stdout/stderr to /dev/null so child logs do not appear in parent
            with open(os.devnull, "wb") as devnull:
                if os.path.isabs(exe):
                    subprocess.Popen(
                        args,
                        start_new_session=True,
                        stdout=devnull,
                        stderr=devnull,
                        cwd=os.path.expanduser("~")
                    )
                else:
                    resolved = shutil.which(exe)
                    if resolved:
                        subprocess.Popen(
                            [resolved] + args[1:],
                            start_new_session=True,
                            stdout=devnull,
                            stderr=devnull,
                            cwd=os.path.expanduser("~")
                        )
                    else:
                        print(f"Command not found: {exe}")