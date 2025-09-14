from gi.repository import Gtk, GLib
from .tile import Tile
from pydbus import SessionBus

class Notifications(Tile):
    def __init__(self):
        super().__init__("notifications", "Notifications")
        self.bus = SessionBus()

        # Subscribe to all messages from Notifications interface
        self.bus.subscribe(
            iface="org.freedesktop.Notifications",
            signal=None,  # include method calls, not just signals
            signal_fired=self.print_notify
        )

    def print_notify(self, bus, message):
        print("anything?")
        # Called for every message on the interface
        if message.get_member() == "Notify":
            args = message.get_body()
            app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout = args
            print(f"[{app_name}] {summary}: {body}")
