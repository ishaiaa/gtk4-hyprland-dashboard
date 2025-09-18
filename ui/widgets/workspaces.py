import subprocess

from gi.repository import Gtk, GLib, Gdk
from .tile import Tile
from .imagedisplay import ImageDisplay
from ..utils import WorkspaceListener, global_click_manager

class Workspaces(Tile):
    def __init__(self):
        super().__init__("workspaces", "Workspaces", False, True)
        self.grid = Gtk.Grid(
            column_homogeneous=True,
            row_homogeneous=True,
            row_spacing=20,
            column_spacing=20,
            vexpand=True,
            hexpand=True
        )
        
        self.workspaces = []
        for i in range(10):
            self.workspaces.append(self.Workspace(i+1, ""))
        
        self.workspaces[0].set_icon("") #web
        self.workspaces[1].set_icon("") #discord
        self.workspaces[2].set_icon("") #steam
        self.workspaces[3].set_icon("") #code
        self.workspaces[4].set_icon("") #git
        self.workspaces[5].set_icon("") #terminal
        self.workspaces[6].set_icon("") #minecraft
        # self.workspaces[7].set_icon("") 
        self.workspaces[8].set_icon("") #terminal
        self.workspaces[9].set_icon("") #music
        
        self.grid.attach(self.workspaces[0], 0,0,1,1)
        self.grid.attach(self.workspaces[1], 1,0,1,1)
        self.grid.attach(self.workspaces[2], 2,0,1,1)
        self.grid.attach(self.workspaces[3], 3,0,1,1)
        self.grid.attach(self.workspaces[4], 4,0,1,1)
        
        self.grid.attach(self.workspaces[5], 0,1,1,1)
        self.grid.attach(self.workspaces[6], 1,1,1,1)
        self.grid.attach(self.workspaces[7], 2,1,1,1)
        self.grid.attach(self.workspaces[8], 3,1,1,1)
        self.grid.attach(self.workspaces[9], 4,1,1,1)
        
        
        self.grid.attach(ImageDisplay(), 5,0,3,2)
        
        self.append(self.grid)
        
        listener = WorkspaceListener()
        listener.attach_callback(self.update_workspaces)
        listener._handle_workspace_event()
        
        
    def update_workspaces(self, arr):
        for i, ws in enumerate(arr):
            self.workspaces[i].update_state(ws)
        
    class Workspace(Gtk.Box):
        def __init__(self, id, icon):
            super().__init__(
                vexpand=True,
                hexpand=True,
                cursor=Gdk.Cursor.new_from_name("pointer"),
                css_classes=["workspace-box", "tile-bg"]
            )
            self.add_css_class(f'workspace-{id}')
            
            self.id = id           
            self.overlay = Gtk.Overlay(vexpand=True,hexpand=True,css_classes=["overlay"])
            
            self.icon = Gtk.Label(label=f'{icon}', vexpand=True,hexpand=True,css_classes=["icon"])
            self.number = Gtk.Label(label=f'- {id} -', valign=Gtk.Align.END, vexpand=True,hexpand=True,css_classes=["number"])
            self.overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,vexpand=True,hexpand=True,css_classes=["overlay-box"])
            self.overlay_box.append(self.number)
            
            self.overlay.set_child(self.icon)
            self.overlay.add_overlay(self.overlay_box)
            
            
            self.append(self.overlay)
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self.handle_click)
            self.add_controller(gesture)
            
        def handle_click(self, *args):
            subprocess.run(["hyprctl", "dispatch", "workspace", str(self.id)])
            global_click_manager.call_callback("hide-dashboard")
            
            
        def set_icon(self, icon):
            self.icon.set_text(icon)
            
        def update_state(self, data=None):
            
            self.remove_css_class("active")
            self.remove_css_class("used")
            
            if data == None:    
                return
            
            if data["windows"] > 0:
                self.add_css_class("used")    
            
            if data["active"] == True:
                self.add_css_class("active")            