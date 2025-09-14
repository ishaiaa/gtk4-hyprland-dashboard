#!/programming/gtk4-hyprland-dashboard/.venv/bin/python3
#!/usr/bin/env python3
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from PIL import Image   # pip install pillow
import io
import numpy as np

BUS_NAME = "org.freedesktop.Notifications"
OBJ_PATH = "/org/freedesktop/Notifications"
IFACE = "org.freedesktop.Notifications"

class NotificationDaemon(dbus.service.Object):
    def __init__(self, bus):
        bus_name = dbus.service.BusName(BUS_NAME, bus=bus)
        super().__init__(bus_name, OBJ_PATH)

    @dbus.service.method(IFACE, in_signature="susssasa{sv}i", out_signature="u")
    def Notify(self, app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout):
        print(f"\n--- New Notification ---")
        print(f"App: {app_name}")
        print(f"Summary: {summary}")
        print(f"Body: {body}")
        print(f"Icon: {app_icon}")
        print(f"Expire: {expire_timeout}")
        
        # Check for raw image data in hints
        if "image-data" in hints:
            img_struct = hints["image-data"]
            # Format: (width, height, rowstride, has_alpha, bits_per_sample, channels, data)
            width, height, rowstride, has_alpha, bps, channels, data = img_struct
            arr = np.frombuffer(bytes(data), dtype=np.uint8)
            arr = arr.reshape((height, rowstride))[:, :width * channels]
            arr = arr.reshape((height, width, channels))
            mode = "RGBA" if has_alpha else "RGB"
            img = Image.fromarray(arr, mode)
            img.save("notif_image.png")
            print("Saved notification image as notif_image.png")

        return 0  # notification ID

    @dbus.service.method(IFACE, out_signature="ssss")
    def GetServerInformation(self):
        return ("MinimalPythonDaemon", "Me", "1.0", "1.2")

    @dbus.service.method(IFACE, out_signature="as")
    def GetCapabilities(self):
        return ["body", "icon-static", "icon-multi"]

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    daemon = NotificationDaemon(bus)
    loop = GLib.MainLoop()
    print("Notification daemon running... (Ctrl+C to quit)")
    loop.run()

if __name__ == "__main__":
    main()
