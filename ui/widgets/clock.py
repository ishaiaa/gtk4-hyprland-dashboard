from datetime import datetime

from gi.repository import Gtk, GLib
from .tile import Tile

class Clock(Tile):
    def __init__(self):
        super().__init__("clock", "Clock", False, False, Gtk.Orientation.HORIZONTAL)
        # (later: update a label every second)
        
        self.datetimebox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        self.datetimebox.add_css_class("date-time-box")
        
        self.timebox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        self.timebox.add_css_class("time-box")
        
        self.datebox = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
        self.datebox.add_css_class("date-box")
        
        self.time_hour = Gtk.Label()
        self.time_hour.set_text("21")
        self.time_hour.add_css_class("time-hours")
        
        self.time_separator = Gtk.Label()
        self.time_separator.set_text(":")
        self.time_separator.add_css_class("time-separator")
        
        self.time_minute = Gtk.Label()
        self.time_minute.set_text("37")
        self.time_minute.add_css_class("time-minutes")
        
        self.timebox.append(self.time_hour)
        self.timebox.append(self.time_separator)
        self.timebox.append(self.time_minute)
        
        
        self.day = Gtk.Label()
        self.day.set_text("Sunday, ")
        self.day.add_css_class("day")
        
        self.date = Gtk.Label()
        self.date.set_text("7 September 2025")
        self.date.add_css_class("date")
        
        self.datebox.append(self.day)
        self.datebox.append(self.date)
        
        self.datetimebox.append(self.timebox)
        self.datetimebox.append(self.datebox)
        
        self.update_clock()
        
        self.append(self.datetimebox)
        
        GLib.timeout_add_seconds(1, self.update_clock)
        # self.append(self.currentweatherbox)
        
    def update_clock(self):
        now = datetime.now()

        hour = now.strftime("%H")   # string, "00"–"23"
        minute = now.strftime("%M") # string, "00"–"59"
        day_name = now.strftime("%A")
        date_str = now.strftime("%-d %B %Y")   # use %#d on Windows
        
        self.time_hour.set_text(hour)
        self.time_minute.set_text(minute)
        self.day.set_text(f'{day_name}, ')
        self.date.set_text(date_str)
                
        return True