import os
import time
import psutil 
import pynvml

from gi.repository import Gio, Gtk, Gdk, GLib, GdkPixbuf, Pango
from .tile import Tile
from ..utils import global_click_manager, get_hyprland_programs

class ProcessMonitor(Tile):
    def __init__(self):
        super().__init__("process-monitor", "Process Monitor")
        global_click_manager.create_callback("process-deselect-detect")
        
        self.header_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                hexpand=True,
                valign=Gtk.Align.CENTER,
                css_classes=["header"]
            )
        
        self.title = Gtk.Label(css_classes=["title"], label="User Processes")
        spacer = Gtk.Box(hexpand=True)        
        self.mode_toggle = Gtk.Switch(css_classes=["mode-toggle"])
        
        self.header_box.append(self.title)
        self.header_box.append(spacer)
        self.header_box.append(self.mode_toggle)
        
        self.scroll_window = Gtk.ScrolledWindow(overlay_scrolling=True,kinetic_scrolling=True, valign=Gtk.Align.FILL, vexpand=True, hexpand=True, css_classes=["scroll-window"])
        self.scroll_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE,vexpand=True, hexpand=True, css_classes=["scroll-box"])
        self.scroll_window.set_child(self.scroll_box);
        
        self.process_widgets = {}
        
        self.update_process_list()
        GLib.timeout_add_seconds(3, self.update_process_list)
        
        self.append(self.header_box)
        self.append(self.scroll_window)

    def update_process_list(self):
        new_procs = get_hyprland_programs()  # your function
        old_pids = set(self.process_widgets.keys())
        new_pids = set(new_procs.keys())

        # 1️⃣ Add new processes
        for pid in new_pids - old_pids:
            info = new_procs[pid]
            widget = self.UserProcess(pid, info["class"], info["title"], info["exe"])
            self.scroll_box.append(widget)       # add to ListBox
            self.process_widgets[pid] = widget  # keep reference

        # 2️⃣ Remove processes that disappeared
        for pid in old_pids - new_pids:
            widget = self.process_widgets[pid]
            self.scroll_box.remove(widget)       # remove from ListBox
            del self.process_widgets[pid]

        # 3️⃣ Optional: update existing widgets if info changed
        for pid in old_pids & new_pids:
            info = new_procs[pid]
            widget = self.process_widgets[pid]
            widget.update_data(info)
                
        return True
                
        

    class UserProcess(Gtk.Box):
        def __init__(self, pid, name, title, process):
            super().__init__(
                orientation=Gtk.Orientation.VERTICAL, 
                vexpand=True, 
                valign=Gtk.Align.CENTER, 
                css_classes=["user-process-box"]
            )
            
            self.pid = pid;
            self.name = name;
            self.title = title;
            self.process = process;
            
            self.display_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                vexpand=True, 
                hexpand=True,
                valign=Gtk.Align.CENTER, 
                css_classes=["display-box"]
            )
            
            self.menu_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                vexpand=True, 
                hexpand=True,
                valign=Gtk.Align.CENTER, 
                css_classes=["menu-box", "menu-shown"]
            )
            
            self.icon = self.get_app_icon(self.pid)
            self.icon.add_css_class("icon")
            self.text_grid = Gtk.Grid(
                row_homogeneous=True, 
                column_homogeneous=True, 
                column_spacing=0, 
                row_spacing=0,
                css_classes=["text-grid"]
            )
            
            self.process_name = Gtk.Label(ellipsize=Pango.EllipsizeMode.END,label=f'{self.name} | {self.title}', css_classes=["process-name"], hexpand=True, halign=Gtk.Align.START)
            self.process_path = Gtk.Label(ellipsize=Pango.EllipsizeMode.END,label=process, css_classes=["process-path"], hexpand=True, halign=Gtk.Align.START)
            
            self.cpu_util = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                css_classes=["cpu-util"]
            )
            
            self.cpu_util_value = Gtk.Label(label="99,9%", css_classes=["value"])
            self.cpu_util_name = Gtk.Label(label="CPU", css_classes=["name"])
            
            self.cpu_util.append(self.cpu_util_value)
            self.cpu_util.append(self.cpu_util_name)
            
            self.ram_util = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                css_classes=["ram-util"]
            )
            
            self.ram_util_value = Gtk.Label(label="3108 MB", css_classes=["value"])
            self.ram_util_name = Gtk.Label(label="RAM", css_classes=["name"])
            
            self.ram_util.append(self.ram_util_value)
            self.ram_util.append(self.ram_util_name)
            
            
            self.text_grid.attach(self.process_name, 0,0,2,1)
            self.text_grid.attach(self.process_path, 0,1,2,1)
            self.text_grid.attach(self.cpu_util, 2,0,1,1)
            self.text_grid.attach(self.ram_util, 2,1,1,1)
            
            self.display_box.append(self.icon)
            self.display_box.append(self.text_grid)
            
            #-------------#
            #  MENU GRID  #
            #-------------#
            
            self.menu_grid = Gtk.Grid(
                row_homogeneous=True, 
                column_homogeneous=True, 
                column_spacing=0, 
                hexpand=True,
                row_spacing=0,
                css_classes=["menu-grid"]
            )
            
            #GPU
            self.gpu_util = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                hexpand=True,
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                css_classes=["gpu-util"]
            )
            
            self.gpu_util_value = Gtk.Label(hexpand=True,label="99,9%", css_classes=["value"])
            self.gpu_util_name = Gtk.Label(label="GPU", css_classes=["name"])
            
            self.gpu_util.append(self.gpu_util_value)
            self.gpu_util.append(self.gpu_util_name)
            
            #SSD
            self.ssd_util = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                hexpand=True,
                css_classes=["ssd-util"]
            )
            
            self.ssd_util_value = Gtk.Label(hexpand=True,label="16,2 MB/s", css_classes=["value"])
            self.ssd_util_name = Gtk.Label(label="SSD", css_classes=["name"])
            
            self.ssd_util.append(self.ssd_util_value)
            self.ssd_util.append(self.ssd_util_name)
            
            #UPTIME
            self.uptime_util = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                hexpand=True,
                css_classes=["uptime-util"]
            )
            
            self.uptime_util_value = Gtk.Label(hexpand=True,label="25h 61m", css_classes=["value"])
            self.uptime_util_name = Gtk.Label(label="UPTIME", css_classes=["name"])
            
            self.uptime_util.append(self.uptime_util_value)
            self.uptime_util.append(self.uptime_util_name)
            
            self.term_button = Gtk.Button(hexpand=True,label="TERMINATE",css_classes=["button"])
            self.kill_button = Gtk.Button(hexpand=True,label="KILL",css_classes=["button"])
            self.copy_pid_button = Gtk.Button(hexpand=True,label="COPY PID",css_classes=["button"])
            self.copy_path_button = Gtk.Button(hexpand=True,label="COPY PATH",css_classes=["button"])
            
            self.menu_grid.attach(self.term_button,0,0,1,3)
            self.menu_grid.attach(self.kill_button,0,3,1,3)
            self.menu_grid.attach(self.copy_pid_button,1,0,1,3)
            self.menu_grid.attach(self.copy_path_button,1,3,1,3)
            
            self.menu_grid.attach(self.gpu_util, 2,0,1,2)
            self.menu_grid.attach(self.ssd_util, 2,2,1,2)
            self.menu_grid.attach(self.uptime_util, 2,4,1,2)
            
            self.menu_box.append(self.menu_grid)
            
            self.revealer = Gtk.Revealer(transition_duration=500, transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
            self.revealer.set_child(self.menu_box)
            self.revealer.set_reveal_child(False)  # collapsed
                        
            
            self.append(self.display_box)
            self.append(self.revealer)
            
            self.gesture = Gtk.GestureClick.new()
            self.gesture.connect("pressed", self.on_box_click)
            self.add_controller(self.gesture)
            global_click_manager.attach_to_callback("process-deselect-detect", self.handle_deselect)
            
        def on_box_click(self, *args):
            global_click_manager.call_callback("process-deselect-detect")
            self.menu_box.add_css_class("menu-shown")
            self.revealer.set_reveal_child(True) 
        
        def handle_deselect(self):
            self.menu_box.remove_css_class("menu-shown")
            self.revealer.set_reveal_child(False) 

                
        def update_data(self, data):
            self.pid = data["pid"]
            self.name = data["class"]
            self.title = data["title"]
            self.process = data["exe"]
            
            stats = self.get_process_stats(self.pid)
            print(stats)
            
            self.process_name.set_text(f'{self.name} | {self.title}')
            self.process_path.set_text(self.process)
            self.icon = self.get_app_icon(self.pid)
            
            self.cpu_util_value.set_text(f'{stats["cpu_percent"]}%')
            self.ram_util_value.set_text(f'{stats["ram_mb"]} MB')
            self.gpu_util_value.set_text(f'{round(stats["gpu_percent"],1)}%')
            self.ssd_util_value.set_text(f'{stats["disk_mb"]} MB/s')
            self.uptime_util_value.set_text(self.format_runtime(stats["runtime_sec"]))
            
            print(f'Update {self.pid}')
            
        def get_process_stats(self, pid: int):
            stats = {}

            try:
                proc = psutil.Process(pid)

                stats["cpu_percent"] = round(proc.cpu_percent(None),1)
                stats["ram_mb"] = round(proc.memory_info().rss  / (1024**2),1)

                io_counters = proc.io_counters()
                stats["disk_mb"] = round((io_counters.read_bytes + io_counters.write_bytes) / (1024**2),1)
                stats["runtime_sec"] = time.time() - proc.create_time()

                stats["gpu_percent"] = 0.0

                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

                    for p in procs:
                        if p.pid == pid:
                            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                            stats["gpu_percent"] = util.gpu
                            break

            except Exception as e:
                stats["error"] = str(e)

            return stats

        def format_runtime(self, seconds: float) -> str:
            minutes = int(seconds // 60)
            hours = minutes // 60
            minutes = minutes % 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
            
        def get_app_icon(self, pid: int, size: int = 50) -> Gtk.Image:
            exe_name = None

            # get executable name from pid
            try:
                p = psutil.Process(pid)
                exe_name = os.path.basename(p.exe()).lower()
            except Exception:
                exe_name = None

            if exe_name:
                for appinfo in Gio.AppInfo.get_all():
                    if not isinstance(appinfo, Gio.DesktopAppInfo):
                        continue

                    # try StartupWMClass
                    startup_wmclass = appinfo.get_string("StartupWMClass")
                    if startup_wmclass and startup_wmclass.lower() == exe_name:
                        img = Gtk.Image.new_from_gicon(appinfo.get_icon())
                        img.set_pixel_size(size)
                        return img

                    # try Exec line
                    exec_line = appinfo.get_string("Exec")
                    if exec_line and exe_name in exec_line.lower():
                        img = Gtk.Image.new_from_gicon(appinfo.get_icon())
                        img.set_pixel_size(size)
                        return img

            # fallback
            img = Gtk.Image.new_from_icon_name("application-x-executable")
            img.set_pixel_size(size)
            return img