import os
import geocoder
import requests


from datetime import datetime
from gi.repository import Gtk, GdkPixbuf, GLib
from .tile import Tile

WMO_TO_ICON = {
    # Clear sky
    0: "clear",

    # Mainly clear, partly cloudy, and overcast
    1: "mostlysunny",   # (or "mostlysunny", depending on style you prefer)
    2: "partlycloudy",
    3: "cloudy",

    # Fog
    45: "fog",
    48: "fog",

    # Drizzle
    51: "rain",   # light drizzle
    53: "rain",   # moderate drizzle
    55: "rain",   # dense drizzle

    # Freezing Drizzle
    56: "sleet",
    57: "sleet",

    # Rain
    61: "rain",
    63: "rain",
    65: "rain",

    # Freezing Rain
    66: "sleet",
    67: "sleet",

    # Snowfall
    71: "snow",
    73: "snow",
    75: "snow",

    # Snow grains
    77: "flurries",

    # Rain showers
    80: "chancerain",   # slight
    81: "rain",         # moderate
    82: "rain",         # violent

    # Snow showers
    85: "chancesnow",
    86: "snow",

    # Thunderstorms
    95: "tstorms",
    96: "tstorms",
    99: "tstorms",
    2137: "unknown"
}

class Weather(Tile):
    def __init__(self):
        super().__init__("weather", "Weather")
        
        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(1)
        self.grid.set_column_spacing(4)
        
        useenv = bool(os.getenv("USE_COORDS"))
        
        self.coords = [0,0]
        if(useenv):
            latitude = float(os.getenv("LATITUDE"))
            longitude = float(os.getenv("LONGITUDE"))
            self.coords = [latitude, longitude]
        else:
            g = geocoder.ip('me')
            latitude, longitude = g.latlng
            self.coords = [latitude,longitude]
            
        print(f'USED COORDS: {self.coords}')
        
        self.days = []
        self.days.append(self.WeatherDay(True))
        for i in range(6):
            self.days.append(self.WeatherDay())
        
        self.grid.attach(self.days[0],0,0,2,2)
        self.grid.attach(self.days[1],2,0,1,1)
        self.grid.attach(self.days[2],3,0,1,1)
        self.grid.attach(self.days[3],4,0,1,1)
        self.grid.attach(self.days[4],2,1,1,1)
        self.grid.attach(self.days[5],3,1,1,1)
        self.grid.attach(self.days[6],4,1,1,1)
        
        self.append(self.grid)
        
        self.update_weather()
        GLib.timeout_add_seconds(300, self.update_weather)
        
    def update_weather(self):
        url = f'https://api.open-meteo.com/v1/forecast?latitude={self.coords[0]}&longitude={self.coords[1]}&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max&current=temperature_2m,weather_code&timezone=Europe%2FBerlin'
        url = f'https://nope.nope'
        
        try:
            response = requests.get(url)

            # Check for errors
            if response.status_code == 200:
                data = response.json()
                temp_now = data["current"]["temperature_2m"]
                weathercode_now = data["current"]["weather_code"]
                
                for i in range(7):
                    time = data["daily"]["time"][i]
                    temp_max = data["daily"]["temperature_2m_max"][i]
                    temp_min = data["daily"]["temperature_2m_min"][i]
                    weather_code = data["daily"]["weather_code"][i]
                    rain_prob = data["daily"]["precipitation_probability_max"][i]
                    
                    self.days[i].update_icon(int(weather_code))
                    self.days[i].set_temps(min=int(temp_min), max=int(temp_max))
                    self.days[i].set_day_short(time)
                    self.days[i].set_rain_chance(rain_prob)
                    
                self.days[0].update_icon(int(weathercode_now))
                self.days[0].set_temps(max=int(temp_now))
                
            else:
                print("Error fetching weather:", response.status_code, response.text)   
                for i in range(7):
                    self.days[i].update_icon(2137)
                    self.days[i].set_temps(min="-", max="-")
                    self.days[i].set_day_short()
                    self.days[i].set_rain_chance()   
        except:
            for i in range(7):
                self.days[i].update_icon(2137)
                self.days[i].set_temps(min="-", max="-")
                self.days[i].set_day_short()
                self.days[i].set_rain_chance()   
        return True  
                
        
    class WeatherDay(Gtk.Box):
        def __init__(self, main = False):
            super().__init__(
                orientation=Gtk.Orientation.VERTICAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            self.add_css_class("weather-day-box")
            
            if(main):
                self.add_css_class("main")
            
            here = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(here, "../../weather-icons/unknown.svg")
            # icon_path = os.path.join(here, "../../weather-icons/mostlysunny.svg")
        
            self.icon_size = 80
            if(main):
                self.icon_size = 160
        
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, self.icon_size, self.icon_size)
            self.icon = Gtk.Image.new_from_pixbuf(pixbuf)
            self.icon.add_css_class("icon")
            
            self.icon.set_pixel_size(70)
            if(main):
                self.icon.set_pixel_size(140)
            
            self.temp_row = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            
            self.day_temp = Gtk.Label()
            self.day_temp.set_text("-°C")
            self.day_temp.add_css_class("day-temp")
            
            self.night_temp = Gtk.Label()
            self.night_temp.set_text("-°C")
            self.night_temp.add_css_class("night-temp")
            
            self.temp_row.append(self.day_temp)
            self.temp_row.append(self.night_temp)
            
            self.horizontal_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            
            self.day_short = Gtk.Label()
            self.day_short.set_text(" ? ")
            self.day_short.add_css_class("day-short")
            
            self.separator = Gtk.Label()
            self.separator.set_text("|")
            self.separator.add_css_class("separator")
            
            self.rain_chance = Gtk.Label()
            self.rain_chance.set_text(" -%")
            self.rain_chance.add_css_class("rain-chance")
            
            self.horizontal_box.append(self.day_short)
            self.horizontal_box.append(self.separator)
            self.horizontal_box.append(self.rain_chance)
                
            self.append(self.icon)
            self.append(self.horizontal_box)
            self.append(self.temp_row)
            
        def update_icon(self, code: int):
            icon = f'../../weather-icons/{WMO_TO_ICON[code]}.svg'
            here = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(here, icon)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, self.icon_size, self.icon_size)
            self.icon.set_from_pixbuf(pixbuf)
            
        def set_temps(self, min=None, max=None):
            if(max):
                self.day_temp.set_text(f'{max}°C')
            if(min):
                self.night_temp.set_text(f'{min}°C')
            
        def set_day_short(self, date=None):
            if date:
                dt = datetime.strptime(date, "%Y-%m-%d")
                short_day = dt.strftime("%a").upper()  # -> "MON"
                self.day_short.set_text(short_day)
            else:
                self.day_short.set_text(" ? ")
            
        def set_rain_chance(self, chance=None):
            if chance:
                self.rain_chance.set_text(f' {chance}%')
            else:
                self.rain_chance.set_text(f' -%')
                    
