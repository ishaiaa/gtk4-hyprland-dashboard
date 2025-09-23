import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import Gtk, GLib, GdkPixbuf

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
