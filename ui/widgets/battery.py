import psutil
import subprocess

from gi.repository import Gtk, GLib, Gdk
from .tile import Tile



class Battery(Tile):
    def __init__(self):
        super().__init__("battery", "Battery")
        
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.batterypercent = 1.0;
        
        mainbox = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        mainbox.set_css_classes(["mainbox"])
        
        
        
        uptimebox = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                # vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        uptimebox.set_css_classes(["uptimebox"])
        
        batterybox = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
        )
        
        batterytip = Gtk.Box(
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
        )
        batterytip.set_css_classes(["batterytip"])
        
        self.batterybody = Gtk.Box(
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        self.batterybody.set_css_classes(["batterybody"])
        
        batteryicon = Gtk.Label()
        batteryicon.set_text("")
        
        self.batterybody.append(batteryicon)
        batterybox.append(batterytip)
        batterybox.append(self.batterybody)
        
        self.percentage = Gtk.Label()
        self.percentage.set_css_classes(["battery-percentage"])
        self.percentage.set_text("100%")
        
        
        uptime_title = Gtk.Label()
        uptime_title.set_css_classes(["battery-uptime-title"])
        uptime_title.set_text("UPTIME")
        
        self.uptime = Gtk.Label()
        self.uptime.set_css_classes(["battery-uptime"])
        self.uptime.set_text("15h 32m")
        
        uptimebox.append(self.percentage);
        uptimebox.append(self.uptime)
        uptimebox.append(uptime_title)
        
        mainbox.append(batterybox)
        mainbox.append(uptimebox)
        
        self.modify_battery()
        GLib.timeout_add(10000, self.modify_battery)  # ~60 FPS

        
        self.append(mainbox)
        
    def modify_battery(self):
        with open("/proc/uptime") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            self.uptime.set_text(f'{hours}h {minutes}m')
        battery = psutil.sensors_battery()
        batterypercent = battery.percent/100
        charging = battery.power_plugged
        self.apply_gradient(batterypercent)
        
        
        if charging:
            self.batterybody.set_css_classes(["batterybody", "charging"])
        else:
            self.batterybody.set_css_classes(["batterybody"])
        
        return True
        
        
    def apply_gradient(self, value):
        def lerp(a, b, t):
            return a + (b - a) * t

        def gradient(c1, c2, c3, t):
            if t <= 0.5:
                t2 = t / 0.5
                r = lerp(c1[0], c2[0], t2)
                g = lerp(c1[1], c2[1], t2)
                b = lerp(c1[2], c2[2], t2)
            else:
                t2 = (t - 0.5) / 0.5
                r = lerp(c2[0], c3[0], t2)
                g = lerp(c2[1], c3[1], t2)
                b = lerp(c2[2], c3[2], t2)
            return int(r), int(g), int(b)
        
        color = gradient((255,57,3),(255,208,89),(0,145,65), value)
        css = f"""
        .batterybody {{
            background: linear-gradient(0deg rgb({color[0]}, {color[1]}, {color[2]}) {value*100}%, transparent 0%);
        }}
        """
        
        self.percentage.set_text(f'{int(value*100)}%')
        self.provider.load_from_data(css.encode("utf-8"))