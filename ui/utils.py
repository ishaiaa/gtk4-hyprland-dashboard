import os
import psutil
import json
import socket
import subprocess
import threading
import dbus
import dbus.service
import dbus.mainloop.glib
import numpy as np
import asyncio



from PIL import Image
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

APP_DATA_DIR = os.path.join(os.path.expanduser("~/.local/share/hyperdash"))
STATE_FILE = os.path.join(APP_DATA_DIR, "state.json")
os.makedirs(APP_DATA_DIR, exist_ok=True)    

def save_image_path(selected_file):
    data = {"used_image": selected_file}
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def load_image_path():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        return data.get("used_image")

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
    raw = subprocess.check_output(["hyprctl", "clients", "-j"], text=True, encoding="utf-8", errors="replace")
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
    
    
# State used in all widgets to check whether dashboard is currently visible
# This will minimize unnecessary tasks such as weather pulling, or monitoring processes when idle
            
class GlobalState:
    def __init__(self):
        self.dashboard_visible = True
    
    def toggle_visible(self):
        self.dashboard_visible = not self.visible
        
    def set_visible(self, state):
        self.dashboard_visible = state
        
global_state = GlobalState()
            
            
# Global callback handler. You can register a custom event, and attach as many callbacks as needed.
# You can attach callback and invoke them from any location in the project

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




# NOTIFICATION DAEMON

BUS_NAME = "org.freedesktop.Notifications"
OBJ_PATH = "/org/freedesktop/Notifications"
IFACE = "org.freedesktop.Notifications"


class NotificationDaemon(dbus.service.Object):
    """
    Notification Daemon.
    - Provides a global instance (get_instance).
    - Multiple callbacks can be attached.
    """

    _instance = None

    def __init__(self):
        if NotificationDaemon._instance is not None:
            raise RuntimeError("Use NotificationDaemon.get_instance() instead")

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(BUS_NAME, bus=self.bus)
        super().__init__(bus_name, OBJ_PATH)

        self._callbacks = []  # list of subscriber functions
        NotificationDaemon._instance = self

    import dbus

    def unwrap(self,value):
        if isinstance(value, (dbus.String, dbus.ObjectPath)):
            return str(value)
        elif isinstance(value, (dbus.Int32, dbus.Int64, dbus.UInt32, dbus.UInt64, dbus.Byte)):
            return int(value)
        elif isinstance(value, dbus.Boolean):
            return bool(value)
        elif isinstance(value, dbus.Double):
            return float(value)
        elif isinstance(value, (list, dbus.Array)):
            return [self.unwrap(v) for v in value]
        elif isinstance(value, (dict, dbus.Dictionary)):
            return {self.unwrap(k): self.unwrap(v) for k, v in value.items()}
        else:
            return value


    # -------------------------
    # D-Bus API
    # -------------------------
    @dbus.service.method(IFACE, in_signature="susssasa{sv}i", out_signature="u")
    def Notify(self, app_name, replaces_id, app_icon,
               summary, body, actions, hints, expire_timeout):
        notif = {
            "app": self.unwrap(app_name),
            "summary": self.unwrap(summary),
            "body": self.unwrap(body),
            "icon": self.unwrap(app_icon),
            "expire": self.unwrap(expire_timeout),
            # "hints": self.unwrap(dict(hints)),
        }

        # Extract raw image if present
        if "image-data" in hints:
            img_struct = hints["image-data"]
            width, height, rowstride, has_alpha, bps, channels, data = img_struct
                        
            pixel_bytes = GLib.Bytes(bytes(data))

            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                pixel_bytes,
                GdkPixbuf.Colorspace.RGB,
                bool(has_alpha),
                bps,
                width,
                height,
                rowstride
            )

            gtk_image = Gtk.Image.new_from_pixbuf(pixbuf)
            gtk_image.add_css_class("image")
            notif["image"] = gtk_image

        # Notify subscribers
        for cb in list(self._callbacks):
            try:
                if "image-data" in hints:
                    img_struct = hints["image-data"]
                    width, height, rowstride, has_alpha, bps, channels, data = img_struct
                                
                    pixel_bytes = GLib.Bytes(bytes(data))

                    pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                        pixel_bytes,
                        GdkPixbuf.Colorspace.RGB,
                        bool(has_alpha),
                        bps,
                        width,
                        height,
                        rowstride
                    )

                    notif["image"] = pixbuf
                GLib.idle_add(cb,notif)
            except Exception as e:
                print(f"[NotificationDaemon] callback error: {e}")

        return 0

    @dbus.service.method(IFACE, out_signature="ssss")
    def GetServerInformation(self):
        return ("MinimalPythonDaemon", "YourName", "1.0", "1.2")

    @dbus.service.method(IFACE, out_signature="as")
    def GetCapabilities(self):
        return ["body", "icon-static", "icon-multi"]

    # -------------------------
    # Public API
    # -------------------------
    @classmethod
    def get_instance(cls):
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = NotificationDaemon()
            print("Notification daemon started.")
        return cls._instance

    def add_callback(self, cb):
        """Subscribe a callback function (notif: dict -> None)."""
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    def remove_callback(self, cb):
        """Unsubscribe a callback."""
        if cb in self._callbacks:
            self._callbacks.remove(cb)

import os
import socket
import threading
import subprocess
import json

class WorkspaceListener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.callbacks = []
        self.sock_path = self._get_socket_path()

        # Start listening thread
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _get_socket_path(self):
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not sig:
            raise RuntimeError("HYPRLAND_INSTANCE_SIGNATURE not set (are you inside Hyprland?)")

        base = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        path = os.path.join(base, "hypr", sig, ".socket2.sock")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Hyprland socket2 not found at {path}")
        return path

    def attach_callback(self, cb):
        """Attach a callback that receives the 10-element workspace array."""
        if callable(cb):
            self.callbacks.append(cb)

    def _listen(self):
        """Listen for Hyprland IPC events."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.sock_path)

            while True:
                data = s.recv(4096).decode("utf-8", errors="ignore")
                if not data:
                    break

                for line in data.strip().splitlines():
                    if line.startswith("workspace"):
                        self._handle_workspace_event()

    def _handle_workspace_event(self):
        """Fetch simplified workspace info and notify callbacks."""
        try:
            workspaces = json.loads(subprocess.check_output(
                ["hyprctl", "workspaces", "-j"], text=True
            ))
            active = json.loads(subprocess.check_output(
                ["hyprctl", "activeworkspace", "-j"], text=True
            ))
        except subprocess.CalledProcessError as e:
            print(f"Error fetching workspace info: {e}")
            return

        result = [None] * 10
        for ws in workspaces:
            idx = ws["id"] - 1
            if 0 <= idx < 10:
                result[idx] = {
                    "id": ws["id"],
                    "name": ws["name"],
                    "windows": ws["windows"],
                    "active": ws["id"] == active.get("id")
                }

        for cb in self.callbacks:
            try:
                GLib.idle_add(cb, result)
            except Exception as e:
                print(f"Callback error: {e}")