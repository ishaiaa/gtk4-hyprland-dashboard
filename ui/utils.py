import psutil
import json
import subprocess

from gi.repository import Gtk, Gdk

def load_css(path: str):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(path)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def make_tile(label: str):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_css_classes(["tile", "tile-bg"])
    lbl = Gtk.Label(label=label)
    lbl.set_wrap(True)
    lbl.set_justify(Gtk.Justification.CENTER)
    box.append(lbl)
    return box

def apply_css(widget: Gtk.Widget, path: str):
    print(path)
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(path)
    widget.get_style_context().add_provider(
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    
def get_hyprland_programs():
    # grab clients from Hyprland
    raw = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
    clients = json.loads(raw)

    programs = {}
    for c in clients:
        pid = c["pid"]
        try:
            proc = psutil.Process(pid)
            exe = proc.exe()
            name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe, name = None, None

        programs[pid] = {
            "pid": pid,
            "exe": exe,
            "class": c.get("class"),
            "title": c.get("title"),
        }

    return programs
    
class ClickManager:
    def __init__(self):
        self.registered_click_callbacks = []

    def register_callback(self, callback):
        self.registered_click_callbacks.append(callback)
        
    def notify_click(self, controller, n_press, x, y):
        for callable in self.registered_click_callbacks:
            callable(x, y, controller, n_press)
            
class GlobalCallback:
    def __init__(self):
        self.callbacks = {}
        self.last_id = 0

    def create_callback(self, name):
        if name not in self.callbacks.keys():
            self.callbacks[name] = {}
            
    def attach_to_callback(self, name, callable):
        if name in self.callbacks.keys():
            self.last_id += 1
            self.callbacks[name][f'{self.last_id}'] = callable
            return self.last_id
            
    def detach_from_callback(self, name, id):
        if name in self.callbacks.keys():
            if id in self.callbacks[name].keys():
                del(self.callbacks[name][id])
            
    def call_callback(self, name, *args):
        if name in self.callbacks.keys():
            for callable in self.callbacks[name].keys():
                self.callbacks[name][f'{callable}'](*args)

global_click_manager = GlobalCallback()