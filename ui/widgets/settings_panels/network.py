from enum import StrEnum

import random
import json
from gi.repository import Gtk, GLib, Gdk, Pango
from ...utils import network_monitor, global_callback_manager

import json

class NetworkType(StrEnum):
    LAN = "lan"
    WIFI = "wifi"
    
class NetworkState(StrEnum):
    OFF = "off"
    CONNECTED = "connected"
    SAVED = "saved"
    AVIABLE = "aviable"
    
def format_for_output(data):
    def convert(obj):
        if isinstance(obj, (list, tuple)):
            return [convert(x) for x in obj]
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return str(obj)  # fallback for enums, flags, etc.
    return json.dumps(convert(data), indent=2)

class Network(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            css_classes=["network-settings"]
        )
        
        self.scroll_window = Gtk.ScrolledWindow(hexpand=True,vexpand=True, css_classes=["scroll-window"])
        self.scroll_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            valign=Gtk.Align.START,
            css_classes=["scroll-box"])
        
        self.connected_networks_expander = Gtk.Expander(
            label="Current Connections",
            expanded=True, 
            valign=Gtk.Align.START,
            hexpand=True, 
            css_classes=["connected-networks", "network-expander"])
        
        self.connected_networks_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            vexpand=True,
            css_classes=["networks-box"])
        self.connected_networks_expander.set_child(self.connected_networks_box)
        
        self.saved_networks_expander = Gtk.Expander(
            label="Saved Networks",
            expanded=True, 
            valign=Gtk.Align.START,
            hexpand=True, 
            css_classes=["saved-networks", "network-expander"])
        
        self.saved_networks_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            vexpand=True,
            css_classes=["networks-box"])
        self.saved_networks_expander.set_child(self.saved_networks_box)
        
        
        self.aviable_networks_expander = Gtk.Expander(
            label="Aviable Networks",
            expanded=True, 
            valign=Gtk.Align.START,
            hexpand=True, 
            css_classes=["aviable-networks", "network-expander"])
        
        self.aviable_networks_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            vexpand=True,
            css_classes=["networks-box"])
        self.aviable_networks_expander.set_child(self.aviable_networks_box)
        

        self.connected_networks_box.append(self.NetworkEntry("WDM.PL___HALN621b3730_5G", NetworkType.WIFI, NetworkState.CONNECTED))
        self.connected_networks_box.append(self.NetworkEntry("Ethernet", NetworkType.LAN, NetworkState.CONNECTED))
        self.connected_networks_box.append(self.NetworkEntry("Ethernet", NetworkType.LAN, NetworkState.OFF))

        self.saved_networks_box.append(self.NetworkEntry("WIFI-1 NETWORK NAME", NetworkType.WIFI, NetworkState.SAVED))
        self.saved_networks_box.append(self.NetworkEntry("WIFI-2 NETWORK NAME", NetworkType.WIFI, NetworkState.SAVED))
        self.saved_networks_box.append(self.NetworkEntry("WIFI-3 NETWORK NAME", NetworkType.WIFI, NetworkState.SAVED))
        self.saved_networks_box.append(self.NetworkEntry("WIFI-4 NETWORK NAME", NetworkType.WIFI, NetworkState.SAVED))

        self.aviable_networks_box.append(self.NetworkEntry("WIFI-1 NETWORK NAME", NetworkType.WIFI, NetworkState.AVIABLE))
        self.aviable_networks_box.append(self.NetworkEntry("WIFI-2 NETWORK NAME", NetworkType.WIFI, NetworkState.AVIABLE))
        self.aviable_networks_box.append(self.NetworkEntry("WIFI-3 NETWORK NAME", NetworkType.WIFI, NetworkState.AVIABLE))
        self.aviable_networks_box.append(self.NetworkEntry("WIFI-4 NETWORK NAME", NetworkType.WIFI, NetworkState.AVIABLE))


        self.scroll_box.append(self.connected_networks_expander)
        self.scroll_box.append(self.saved_networks_expander)
        self.scroll_box.append(self.aviable_networks_expander)
        self.scroll_window.set_child(self.scroll_box)
        
        self.append(self.scroll_window)
        
        #GLib.timeout_add(2000, self.net_debug)


    
    def net_debug(self):
        print("NETWORK DUMP GO BRRR")
        print(format_for_output(network_monitor.collect_all()))
        print("")
        print("")
        return True
    
    class NetworkEntry(Gtk.Box):
        def __init__(self, name, type: NetworkType, state: NetworkState):
            super().__init__(
                orientation=Gtk.Orientation.VERTICAL, 
                cursor=Gdk.Cursor.new_from_name("pointer"),
                vexpand=True, 
                valign=Gtk.Align.CENTER, 
                css_classes=["network-entry-box"]
            )
            
            
            self.id = name
            self.name = name;
            
            self.subtitle_cache = None
            self.subtitle_css_cache = None
            self.subtitle_lock = False
            
            if state == NetworkState.OFF:
                self.add_css_class("off")
                
            if type == NetworkType.LAN:
                self.set_cursor(None)
                self.set_can_target(False)
                # self.set_can_focus(False)
            
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
            
            
            self.text_grid = Gtk.Grid(
                row_homogeneous=True, 
                column_homogeneous=True, 
                column_spacing=0, 
                row_spacing=0,
                css_classes=["text-grid"]
            )
            
            self.network_name = Gtk.Label(
                ellipsize=Pango.EllipsizeMode.END,label=f'{
                    self.name}', 
                    css_classes=["network-name"], 
                    hexpand=True, 
                    halign=Gtk.Align.START)
            
            self.subtitle = Gtk.Label(
                ellipsize=Pango.EllipsizeMode.END,
                label="", 
                css_classes=["network-subtitle"], 
                hexpand=True, 
                halign=Gtk.Align.START)
            
            #connection Strenght
            
            self.conn_strength = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                css_classes=["connection-strength"]
            )
            
            self.conn_strength_value = Gtk.Label(label="100%", css_classes=["value"])
            self.conn_strength_name = Gtk.Label(label="RSSI", css_classes=["name"])
            
            self.conn_strength.append(self.conn_strength_value)
            self.conn_strength.append(self.conn_strength_name)
            
            
            self.text_grid.attach(self.network_name, 0,0,3,1)
            self.text_grid.attach(self.subtitle, 0,1,2,1)
            
            if (state != NetworkState.OFF and type != NetworkType.LAN):
            
                self.text_grid.attach(self.conn_strength, 2,1,1,1)
            
            self.icon = None
            
            if type == NetworkType.LAN:
                if state ==NetworkState.OFF:
                    self.icon = self.wifi_icon(-1)
                else:
                    self.icon = self.wifi_icon(999)
            else:
                self.icon = self.wifi_icon(random.randint(0, 100))
            
            self.display_box.append(self.icon)
            self.display_box.append(self.text_grid)
            
            #-------------#
            #  MENU GRID  #
            #-------------#
            
            self.menu_grid = Gtk.Grid(
                column_spacing=10, 
                column_homogeneous=True,
                hexpand=True,
                row_spacing=10,
                css_classes=["menu-grid"]
            )
            
            
            self.password_entry = Gtk.Entry(
                css_classes=["password-entry"],
                visibility=False,
                placeholder_text="Password",
                secondary_icon_name="view-reveal-symbolic",
            )
    
            # entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "")

            
            self.password_entry.connect("icon-press", self.toggle_password)
            
            self.action_button = Gtk.Button(
                hexpand=True,css_classes=["button"])
            self.action_button.connect("clicked", lambda a: print("CLICK PRPRPR"))
            
            self.secondary_button = Gtk.Button(
                hexpand=True,label="FORGET",css_classes=["button"])
            self.secondary_button.connect("clicked", lambda a: print("CLICK PRPRPR"))
            
            
            if state == NetworkState.CONNECTED:
                self.action_button.set_label("DISCONNECT")
                self.menu_grid.attach(self.secondary_button,0,1,1,1)
                
                
            if state == NetworkState.SAVED:
                self.action_button.set_label("CONNECT")
                self.menu_grid.attach(self.secondary_button,0,1,1,1)
                
            if state == NetworkState.AVIABLE:
                self.action_button.set_label("CONNECT")
            
            self.menu_grid.attach(self.action_button,1,1,1,1)
            
            if state == NetworkState.AVIABLE:
                self.menu_grid.attach(self.password_entry, 0,0,2,1)
            self.menu_box.append(self.menu_grid)
            
            self.revealer = Gtk.Revealer(transition_duration=500, transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
            self.revealer.set_child(self.menu_box)
            self.revealer.set_reveal_child(False)  # collapsed
                        
            
            self.append(self.display_box)
            self.append(self.revealer)
            
            self.toggled = False
            
            self.gesture = Gtk.GestureClick.new()
            self.gesture.connect("pressed", self.on_box_click)
            self.add_controller(self.gesture)
            
            
        def update_subtitle(self, text, error = False, lock_ms = None):
            if self.subtitle_lock:
                self.subtitle_cache = text
                self.subtitle_css_cache = error
                return
            
            self.subtitle.remove_css_class("error")
            self.subtitle_cache = self.subtitle.get_text
            self.subtitle.set_text(text)
            
            if error:
                self.subtitle.add_css_class("error")
            
            if lock_ms:
                self.subtitle_lock = True
                GLib.timeout_add(lock_ms, self.__unlock_subtitle)
                
        def __unlock_subtitle(self):
            self.subtitle.set_text(self.subtitle_cache)
            self.subtitle.remove_css_class("error")
            if self.subtitle_css_cache:
                self.subtitle.add_css_class("error")
                
                
        def toggle_password(self, *args):
            self.password_entry.set_visibility(not self.password_entry.get_visibility())
            icon_name = "view-reveal-symbolic" if not self.password_entry.get_visibility() else "view-conceal-symbolic"
            self.password_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, icon_name)

        def on_box_click(self, *args):
            self.toggled = not self.toggled
            
            if self.toggled:
                self.menu_box.add_css_class("menu-shown")
                self.revealer.set_reveal_child(True) 
            else:
                self.menu_box.remove_css_class("menu-shown")
                self.revealer.set_reveal_child(False) 
            
        def wifi_icon(self, strength: int) -> Gtk.Image:
            # strength: 0–100
            
            if strength < 0:
                icon = "network-wired-disconnected-symbolic"
            elif strength == 0:
                icon = "network-wireless-offline-symbolic"
            elif strength < 20:
                icon = "network-wireless-signal-none-symbolic"
            elif strength < 40:
                icon = "network-wireless-signal-weak-symbolic"
            elif strength < 60:
                icon = "network-wireless-signal-ok-symbolic"
            elif strength < 80:
                icon = "network-wireless-signal-good-symbolic"
            elif strength <= 100:
                icon = "network-wireless-signal-excellent-symbolic"
            else:
                icon = "network-wired-symbolic"
                
            img = Gtk.Image.new_from_icon_name(icon)
            img.set_pixel_size(40)
            img.add_css_class("icon")
            return img