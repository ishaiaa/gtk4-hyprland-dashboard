import cairo
import math
import os
import psutil
import pynvml
import time


from collections import deque
from gi.repository import Gtk, GLib
from .tile import Tile


class SmoothStat:
    def __init__(self, maxlen=10):
        self.samples = deque(maxlen=maxlen)

    def add(self, value):
        self.samples.append(value)

    def get(self):
        return sum(self.samples) / len(self.samples)

class Perf(Tile):
    def __init__(self):
        super().__init__("perf", "Perf", False, True)
        pynvml.nvmlInit()
        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(30)
        self.grid.set_column_spacing(30)
        
        self.cpu = self.PerfTile(0.2, "CPU", (1.0, 0.8, 0.1), self.get_cpu_stats)
        self.gpu = self.PerfTile(0.5, "GPU", (0.2, 0.8, 0.7), self.get_gpu_stats)
        self.ram = self.PerfTile(0.1, "RAM", (0.7, 0.1, 0.2), self.get_ram_stats)
        self.ssd = self.PerfTile(1.0, "SSD", (0.4, 0.2, 0.9), self.get_ssd_stats)
        
        self.cpu_usage = SmoothStat(maxlen = 10)
        self.cpu_temp = SmoothStat(maxlen = 10)
        self.gpu_usage = SmoothStat(maxlen = 10)
        self.gpu_temp = SmoothStat(maxlen = 10)
        self.ram_usage = SmoothStat(maxlen = 10)
        self.ssd_write = SmoothStat(maxlen = 10)
        self.ssd_read = SmoothStat(maxlen = 10)
        
        self.last_io = psutil.disk_io_counters()
        self.last_time = psutil.time.time()
        
        self.grid.attach(self.cpu, 0,0,1,1)
        self.grid.attach(self.gpu, 1,0,1,1)
        self.grid.attach(self.ram, 0,1,1,1)
        self.grid.attach(self.ssd, 1,1,1,1)
        
        
        self.append(self.grid)
        self.update_tiles()
        GLib.timeout_add_seconds(1, self.update_tiles)
        
        
    def update_tiles(self):
        self.cpu.update_stats()
        self.gpu.update_stats()
        self.ram.update_stats()
        self.ssd.update_stats()
        
        return True
        
    class PerfTile(Gtk.Frame):
        def __init__(self, progress, name, color, getter):
            super().__init__()
            self.set_hexpand(True)
            self.set_vexpand(True)
            self.set_css_classes(["perf-tile", "tile-bg"])

            self.getter = getter

            # Main overlay container
            overlay = Gtk.Overlay()
            overlay.set_hexpand(True)
            overlay.set_vexpand(True)

            self.name = Gtk.Label()
            self.name.set_text(name)
            self.name.add_css_class("perf-name")

            self.perf_bar = self.CircularProgress(progress, color)

            # Base box (your actual button contents)
            box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            box.append(self.name)
            box.append(self.perf_bar)
            box.add_css_class("chart-box")

            # Add main content to overlay
            overlay.set_child(box)

            # Overlay box (full size, for styling)
            overlay_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                vexpand=True,
                hexpand=True,
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
            )
            overlay_box.add_css_class("overlay-box")
            
            self.stat1 = Gtk.Label()
            self.stat1.set_text("100%")
            self.stat1.add_css_class("stat1-value")
            
            self.stat1_name = Gtk.Label()
            self.stat1_name.set_text("STAT1")
            self.stat1_name.add_css_class("stat1-name")
            
            self.stat2 = Gtk.Label()
            self.stat2.set_text("100°C")
            self.stat2.add_css_class("stat2-value")
            
            self.stat2_name = Gtk.Label()
            self.stat2_name.set_text("STAT2")
            self.stat2_name.add_css_class("stat2-name")
            
            overlay_box.append(self.stat1)
            overlay_box.append(self.stat1_name)
            overlay_box.append(self.stat2)
            overlay_box.append(self.stat2_name)
            
            # Add overlay layer (it sits above box but doesn’t shift it)
            overlay.add_overlay(overlay_box)

            # Attach overlay to button
            self.set_child(overlay)
            
        def update_stats(self):
            self.update_stats_text(*self.getter())
            
        def update_stats_text(self, stat1_name, stat1_value, stat2_name, stat2_value, progress):
            self.stat1_name.set_text(stat1_name)
            self.stat1.set_text(stat1_value)
            self.stat2_name.set_text(stat2_name)
            self.stat2.set_text(stat2_value)
            self.perf_bar.progress = progress
            self.perf_bar.queue_draw()
            

        class CircularProgress(Gtk.DrawingArea):
            def __init__(self, progress, color):
                super().__init__()
                self.progress = progress
                self.color = color
                self.set_content_width(200)
                self.set_content_height(200)
                self.set_draw_func(self.on_draw)
                self.add_css_class("progress-chart")
                self.queue_draw()

            def on_draw(self, drawing_area, cr, width, height):
                cx, cy = width/2, height/2
                radius = min(width, height)/2 - 10
                line_width = 10

                cr.set_line_width(line_width)
                cr.set_source_rgba(self.color[0] * 0.1, self.color[1]*0.1, self.color[2]*0.1, 0.2)
                cr.arc(cx, cy, radius, 0, 2*math.pi)
                cr.stroke()

                cr.set_source_rgb(*self.color)
                cr.arc(cx, cy, radius, -math.pi/2, -math.pi/2 + 2*math.pi*self.progress)
                cr.stroke()
    def get_cpu_stats(self):
        cpu_usage = psutil.cpu_percent() 

        # Temperature (requires lm-sensors support)
        temps = psutil.sensors_temperatures()
        cpu_temp = None
        if "coretemp" in temps:  # common on Intel/AMD
            cpu_temp = temps["coretemp"][0].current
        elif "k10temp" in temps:  # AMD
            cpu_temp = temps["k10temp"][0].current

        self.cpu_temp.add(cpu_temp)
        self.cpu_usage.add(cpu_usage)

        cpu_temp = round(self.cpu_temp.get(),1)
        cpu_usage = round(self.cpu_usage.get(),1)

        return ("USAGE", f'{cpu_usage}%', "TEMP", f'{cpu_temp}°C', cpu_usage/100)

    def get_gpu_stats(self):
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            # Usage
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_usage = util.gpu  # in %

            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )

            # Smooth values
            self.gpu_usage.add(gpu_usage)
            self.gpu_temp.add(temp)

            gpu_usage = round(self.gpu_usage.get(), 1)
            gpu_temp = round(self.gpu_temp.get(), 1)

            return (
                "USAGE", f"{gpu_usage}%",
                "TEMP", f"{gpu_temp}°C",
                gpu_usage / 100.0
            )
        except pynvml.NVMLError as e:
            return ("USAGE", "N/A", "TEMP", "N/A", 0.0)
        
    def get_ram_stats(self):
        mem = psutil.virtual_memory()

        # Match "free" and terminal bars: used = total - free
        used_gb = (mem.total - mem.free) / (1024**3)
        total_gb = mem.total / (1024**3)

        percent_used = (used_gb / total_gb) * 100

        # Smooth
        self.ram_usage.add(percent_used)
        ram_usage = round(self.ram_usage.get(), 1)

        return (
            "USED", f"{used_gb:.1f} GB",
            "TOTAL", f"{total_gb:.1f} GB",
            ram_usage / 100.0
        )
        
    def get_ssd_stats(self):
        # Disk space
        usage = psutil.disk_usage("/")
        used_gb = usage.used / (1024**3)
        total_gb = usage.total / (1024**3)
        percent_used = usage.percent

        # Disk IO (speed)
        now = time.time()
        io = psutil.disk_io_counters()

        # bytes per second
        read_bps = (io.read_bytes - self.last_io.read_bytes) / (now - self.last_time)
        write_bps = (io.write_bytes - self.last_io.write_bytes) / (now - self.last_time)

        # save state for next round
        self.last_io = io
        self.last_time = now

        # convert to MB/s
        read_mb = read_bps / (1024**2)
        write_mb = write_bps / (1024**2)

        # smooth values
        self.ssd_read.add(read_mb)
        self.ssd_write.add(write_mb)

        read_mb = round(self.ssd_read.get(), 1)
        write_mb = round(self.ssd_write.get(), 1)

        return (
            "READ", f"{read_mb} MB/s",
            "WRITE", f"{write_mb} MB/s",
            percent_used / 100.0
        )