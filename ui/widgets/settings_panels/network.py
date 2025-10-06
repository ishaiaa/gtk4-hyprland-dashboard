from enum import StrEnum

import random
import json
from gi.repository import Gtk, GLib, Gdk, Pango
from ...utils import NetworkMonitor, global_callback_manager, global_state

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
        
        self.network_monitor = NetworkMonitor()
        
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
        
        self.scroll_box.append(self.connected_networks_expander)
        self.scroll_box.append(self.saved_networks_expander)
        self.scroll_box.append(self.aviable_networks_expander)
        self.scroll_window.set_child(self.scroll_box)
        
        self.append(self.scroll_window)
        
        self.update_state()
        GLib.timeout_add(2000, self.update_state)


    def update_state(self):
        if(not global_state.dashboard_visible):
            return True
        
        
        
        data = self.network_monitor.get_data()
        remove_queue = []
        connected_wifis = []
        
        #DEVICES
        for dev in self.connected_networks_box:
            device_data = next((d for d in data["devices"] if d.get("iface") == dev.id), None)
            if device_data is None:
                remove_queue.append(dev)
            else:
                if device_data["type"] is not "ethernet" and int(device_data["state"]) == 100:
                    connected_wifis.append(device_data["connected_ap"]["ssid"])
                dev.update_data(device_data)
                data["devices"].remove(device_data)
                
        for dev in data["devices"]:
            net_type = NetworkType.WIFI
            if dev["type"] == "ethernet":
                net_type = NetworkType.LAN
            else:
                if int(dev["state"]) == 100:
                    connected_wifis.append(dev["connected_ap"]["ssid"])
            self.connected_networks_box.append(self.NetworkEntry(self.network_monitor, dev["iface"], dev, net_type, NetworkState.CONNECTED))
                
        for dev in remove_queue:
            self.connected_networks_box.remove(dev)
            
        
        remove_queue = []
        
        connected_wifis_tile_ref = []
        aviable_networks_refs = []
            
        #SAVED
        for dev in self.saved_networks_box:
            device_data = next((d for d in data["saved_networks"] if d.get("uuid") == dev.id), None)
            if device_data is None:
                remove_queue.append(dev)
            else:
                link_data = next((d for d in data["available_networks"] if d.get("ssid") == device_data["ssid"]), None)
                if link_data:
                    aviable_networks_refs.append(link_data["ssid"])
                data["saved_networks"].remove(device_data)
                device_data["linked_data"] = link_data
                dev.update_data(device_data)
                if device_data["ssid"] in connected_wifis:
                    connected_wifis_tile_ref.append(dev)
                
        for dev in data["saved_networks"]:
            if dev["ssid"] in connected_wifis:
                continue
            device_data = dev
            link_data = next((d for d in data["available_networks"] if d.get("ssid") == device_data["ssid"]), None)
            if link_data:
                aviable_networks_refs.append(link_data["ssid"])
            device_data["linked_data"] = link_data
            self.saved_networks_box.append(self.NetworkEntry(self.network_monitor, dev["uuid"], device_data, NetworkType.WIFI, NetworkState.SAVED))
                
        for dev in remove_queue:
            self.saved_networks_box.remove(dev)
            
        #clean up already connected devices:
        for dev in connected_wifis_tile_ref:
            self.saved_networks_box.remove(dev)
            
        for ssid in aviable_networks_refs:
            device_data = next((d for d in data["available_networks"] if d.get("ssid") == ssid), None)
            if device_data:
                data["available_networks"].remove(device_data)
            
        remove_queue = []
        connected_wifis_tile_ref = []
            
        #AVIABLE
        # print(f'AVIABLE NETWORKS\n{data["available_networks"]}\n')
        
        for dev in self.aviable_networks_box:
            device_data = next((d for d in data["available_networks"] if d.get("bssid") == dev.id), None)
            if device_data is None:
                remove_queue.append(dev)
            else:
                dev.update_data(device_data)
                if device_data["ssid"] in connected_wifis:
                    connected_wifis_tile_ref.append(dev)
                data["available_networks"].remove(device_data)
                
        for dev in data["available_networks"]:
            if dev["ssid"] in connected_wifis:
                continue
            self.aviable_networks_box.append(self.NetworkEntry(self.network_monitor, dev["bssid"], dev, NetworkType.WIFI, NetworkState.AVIABLE))
                
        for dev in remove_queue:
            self.aviable_networks_box.remove(dev)
            
        for dev in connected_wifis_tile_ref:
            self.aviable_networks_box.remove(dev)
            
        #hide expanders
        saved_count = 0
        aviable_count = 0
        for c in self.saved_networks_box:
            saved_count += 1
        for c in self.aviable_networks_box:
            aviable_count +=1
            
        if saved_count > 0:
            self.saved_networks_expander.set_visible(True)
        else:
            self.saved_networks_expander.set_visible(False)
            
        if aviable_count > 0:
            self.aviable_networks_expander.set_visible(True)
        else:
            self.aviable_networks_expander.set_visible(False)
            
            
        
        return True
    
    class NetworkEntry(Gtk.Box):
        def __init__(self,network_monitor, id, data, type: NetworkType, state: NetworkState):
            super().__init__(
                orientation=Gtk.Orientation.VERTICAL, 
                cursor=Gdk.Cursor.new_from_name("pointer"),
                vexpand=True, 
                valign=Gtk.Align.CENTER, 
                css_classes=["network-entry-box"]
            )
            
            self.network_monitor: NetworkMonitor = network_monitor
            
            
            self.id = id
            self.data = data
            self.type = type
            self.state = state
            
            self.subtitle_cache = None
            self.subtitle_css_cache = None
            self.subtitle_lock = False
                
            
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
                ellipsize=Pango.EllipsizeMode.END,
                label="", 
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
            
            self.conn_strength_value = Gtk.Label(label="-%", css_classes=["value"])
            self.conn_strength_name = Gtk.Label(label="RSS", css_classes=["name"])
            
            self.conn_strength.append(self.conn_strength_value)
            self.conn_strength.append(self.conn_strength_name)
            
            self.protection = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, 
                valign=Gtk.Align.CENTER, 
                halign=Gtk.Align.END,
                css_classes=["connection-strength"]
            )
            
            self.protection_value = Gtk.Label(label="WPA", css_classes=["value"])
            self.protection_name = Gtk.Label(label="", css_classes=["name"])
            
            self.protection.append(self.protection_value)
            self.protection.append(self.protection_name)
            
            self.text_grid.attach(self.network_name, 0,0,3,1)
            self.text_grid.attach(self.subtitle, 0,1,2,1)
            
            self.text_grid.attach(self.protection, 2,0,1,1)
            self.text_grid.attach(self.conn_strength, 2,1,1,1)
            
            self.icon = Gtk.Image(css_classes=["icon"])
            
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
            self.password_entry.connect("activate", self.connect_new)
            
            self.action_button = Gtk.Button(
                hexpand=True,css_classes=["button"])
            self.action_gesture = Gtk.GestureClick()
            self.action_gesture.connect("pressed", self.primary_action)
            self.action_button.add_controller(self.action_gesture)
            
            self.secondary_button = Gtk.Button(
                hexpand=True,label="FORGET",css_classes=["button"])
            self.secondary_gesture = Gtk.GestureClick()
            self.secondary_gesture.connect("pressed", self.secondary_action)
            self.secondary_button.add_controller(self.secondary_gesture)
            
            self.menu_grid.attach(self.secondary_button,0,1,1,1)
            
            
            
            self.menu_grid.attach(self.action_button,1,1,1,1)
            
            self.menu_box.append(self.menu_grid)
            
            self.revealer = Gtk.Revealer(transition_duration=500, transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
            self.revealer.set_child(self.menu_box)
            self.revealer.set_reveal_child(False)  # collapsed
                        
            self.append(self.display_box)
            self.append(self.revealer)
            
            self.toggled = False
            
            self.gesture = Gtk.GestureClick.new()
            self.gesture.set_propagation_phase(Gtk.PropagationPhase.BUBBLE)
            self.gesture.connect("pressed", self.on_box_click)
            self.add_controller(self.gesture)
            
            #ADJUST FOR DISPLAY TYPE
            if type == NetworkType.LAN:
                self.set_cursor(None)
                self.set_can_target(False)
                self.revealer.set_reveal_child(False)
                self.network_name.set_text('Ethernet Card')
                self.conn_strength.set_visible(False)
                self.protection.set_visible(False)
                # self.set_can_focus(False)
                
            if state == NetworkState.CONNECTED:
                self.secondary_button.set_label("DISABLE CARD")
                self.action_button.set_label("DISCONNECT")
                    
            if state == NetworkState.SAVED:
                self.action_button.set_label("CONNECT")
                
            if state == NetworkState.AVIABLE:
                self.secondary_button.set_visible(False)
                self.conn_strength.set_visible(True)
                self.action_button.set_visible(True)
                self.action_button.set_label("CONNECT")
                if(int(self.data["wpa_flags"]) > 0 or  int(self.data["rsn_flags"]) > 0):
                    self.menu_grid.attach(self.password_entry, 0,0,2,1)
                
                
            self.update_display()
            
        def update_data(self, data):
            self.data = data
            self.update_display()
            
        def update_display(self):            
            # print(f'UPDATE DATA {self.id}')
            # print(self.data)
            # print(self.data.get("linked_data"))
            # print("---")
            self.remove_css_class("off")
            
            
            if self.state == NetworkState.CONNECTED:
                if self.type == NetworkType.LAN:
                    if int(self.data["state"]) == 100:
                        self.update_icon(999)
                        ip = "No IP"
                        if self.data["ip4"]:
                            ip = self.data["ip4"]
                        self.update_subtitle(f'Connected | {ip}')
                    else:
                        self.update_icon(0)
                        self.add_css_class("off")
                        self.update_subtitle("Disconnected")
                else:
                    self.state_lock(False)
                    if int(self.data["state"]) == 100:
                        protected =  int(self.data["connected_ap"]["wpa_flags"]) > 0 or int(self.data["connected_ap"]["rsn_flags"]) > 0
                        
                        ip = "No IP"
                        if self.data["ip4"]:
                            ip = self.data["ip4"]
                    
                        self.update_icon(int(self.data["connected_ap"]["strength"]))    
                        self.secondary_button.set_label("DISABLE CARD")
                        self.conn_strength_value.set_text(f'{self.data["connected_ap"]["strength"]}%')
                        self.network_name.set_text(self.data["connected_ap"]["ssid"])
                        self.update_subtitle(f'Connected | {ip}')
                        if protected:
                            self.protection.set_visible(True)
                        self.conn_strength.set_visible(True)
                        self.action_button.set_visible(True)
                    elif int(self.data["state"]) in [10, 20, 120]:
                        self.update_icon(0)
                        self.network_name.set_text("Wireless Card")
                        self.secondary_button.set_label("ENABLE CARD")
                        self.update_subtitle("Card Disabled")
                        self.add_css_class("off")
                        self.protection.set_visible(False)
                        self.conn_strength.set_visible(False)
                        self.action_button.set_visible(False)
                    else:
                        self.update_icon(0)
                        self.network_name.set_text("Wireless Card")
                        self.secondary_button.set_label("DISABLE CARD")
                        self.update_subtitle(f'Disconnected | {self.data["state"]}')
                        self.add_css_class("off")
                        self.protection.set_visible(False)
                        self.action_button.set_visible(False)
                        self.conn_strength.set_visible(False)
            elif self.state == NetworkState.SAVED:
                self.network_name.set_text(self.data["ssid"])
                
                if self.data["linked_data"] == None:
                    self.update_icon(0)
                    self.update_subtitle("Out of Reach")
                    self.conn_strength.set_visible(False)
                    self.action_button.set_visible(False)
                    self.protection.set_visible(False)
                else:
                    protected =  int(self.data["linked_data"]["wpa_flags"]) > 0 or  int(self.data["linked_data"]["rsn_flags"]) > 0

                    self.update_icon(int(self.data["linked_data"]["strength"]))
                    self.conn_strength_value.set_text(f'{self.data["linked_data"]["strength"]}%')
                    self.conn_strength.set_visible(True)
                    self.action_button.set_visible(True)
                    
                    if protected:
                        self.update_subtitle("WPA-Protected")
                        self.protection.set_visible(True)
                    else:
                        self.update_subtitle("Not Protected")
                        self.protection.set_visible(False)
                        
            elif self.state == NetworkState.AVIABLE:
                
                self.network_name.set_text(self.data["ssid"])
                protected =  int(self.data["wpa_flags"]) > 0 or int(self.data["rsn_flags"]) > 0
                self.protection.set_visible(protected)
                
                self.update_icon(int(self.data["strength"]))
                self.conn_strength_value.set_text(f'{self.data["strength"]}%')
                    
                if protected:
                    self.update_subtitle("WPA-Protected")
                else:
                    self.update_subtitle("Not Protected")


        def connect_new(self, *args):
            def connect_new_callback(state):
                print(f'what the fuck {state}')
                self.state_lock(False)
                self.password_entry.set_editable(True)
                self.password_entry.set_sensitive(True)
                
                if state == 2:
                    self.update_subtitle("Password Incorrect!", True, 5000)
                elif state is not 0:
                    self.update_subtitle("Couldn't establish connection :c", True, 5000)
            protected =  int(self.data["wpa_flags"]) > 0 or int(self.data["rsn_flags"]) > 0
            
            password = None
            
            if protected:
                password = self.password_entry.get_text()
                self.password_entry.set_text("")
                self.password_entry.set_editable(False)
                self.password_entry.set_sensitive(False)
            
            self.state_lock(True)
            self.update_subtitle("Connecting...", priority=True)
            self.network_monitor.connect_new(self.data["iface"], self.data["ssid"], password, callback=connect_new_callback)
                

        def primary_action(self, g, *args):
            g.set_state(Gtk.EventSequenceState.CLAIMED)
            if self.state == NetworkState.CONNECTED:
                def disconnect_callback(state):
                    self.state_lock(False)
                    if state is not 0:
                        self.update_subtitle("Something went wrong :c", True, 5000)
                
                self.state_lock(True)
                self.update_subtitle("Disconnecting...", priority=True)
                self.network_monitor.disconnect_wifi(self.data["iface"], disconnect_callback)
                return
            
            if self.state == NetworkState.SAVED:
                if self.data["linked_data"] == None:
                    self.update_subtitle("How TF did you click that?", True, 5000)
                    return
                
                def connect_saved_callback(state):
                    self.state_lock(False)
                    if state is not 0:
                        self.update_subtitle("Couldn't establish connection :c", True, 5000)
                
                self.state_lock(True)
                self.update_subtitle("Connecting...", priority=True)
                self.network_monitor.connect_saved(self.data["iface"], self.data["uuid"], connect_saved_callback)
                return
                
            if self.state == NetworkState.AVIABLE:
                self.connect_new()
                return
            
        
        def secondary_action(self, g,*args):
            g.set_state(Gtk.EventSequenceState.CLAIMED)
            if self.state == NetworkState.CONNECTED:
                
                def disable_callback(state):
                    if state is not 0:
                        self.update_subtitle("Something went wrong :c", True, 5000)
                
                self.state_lock(True)
                
                if int(self.data["state"]) in [10, 20, 120]:
                    self.update_subtitle("Enabling Card...", priority=True)
                    self.network_monitor.enable_wifi(self.data["iface"], True, disable_callback)
                else:
                    self.update_subtitle("Disabling Card...", priority=True)
                    self.network_monitor.enable_wifi(self.data["iface"], False, disable_callback)
                return
            
            if self.state == NetworkState.SAVED:
                def forget_saved_callback(state):
                    self.state_lock(False)
                    if state is not 0:
                        self.update_subtitle("An error occured :c", True, 5000)
                
                self.state_lock(True)
                self.update_subtitle("Forgetting...", priority=True)
                self.network_monitor.forget_saved(self.data["uuid"], forget_saved_callback)
                                
                return
                
            if self.state == NetworkState.AVIABLE:
                self.update_subtitle("How TF did you click that?", True, 5000)
                return

        def state_lock(self, state):
            if state:
                self.set_can_target(False)
                self.action_button.set_sensitive(False)
                self.secondary_button.set_sensitive(False)
                self.subtitle_lock = True
                self.add_css_class("busy")
            else:
                self.set_can_target(True)
                self.action_button.set_sensitive(True)
                self.secondary_button.set_sensitive(True)
                self.subtitle_lock = False
                self.remove_css_class("busy")
        def update_subtitle(self, text, error = False, lock_ms = None, priority = False):
            if self.subtitle_lock and not priority:
                return
            
            self.subtitle.remove_css_class("error")
            self.subtitle.set_text(text)
            
            if error:
                self.subtitle.add_css_class("error")
            
            if lock_ms and not priority:
                self.subtitle_lock = True
                GLib.timeout_add(lock_ms, self.__unlock_subtitle)
                
        def __unlock_subtitle(self):
            self.subtitle_lock = False
                
                
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
            
        def update_icon(self, strength: int) -> Gtk.Image:
            # strength: 0–100
            
            if self.type == NetworkType.LAN:
                if strength == 0:
                    icon = "network-wired-disconnected-symbolic"
                else:
                    icon = "network-wired-symbolic"
            else:
                if strength == 0:
                    icon = f'network-wireless-disconnected-symbolic'
                elif strength < 20:
                    icon = f'network-wireless-signal-none-symbolic'
                elif strength < 40:
                    icon = f'network-wireless-signal-weak-symbolic'
                elif strength < 60:
                    icon = f'network-wireless-signal-ok-symbolic'
                elif strength < 80:
                    icon = f'network-wireless-signal-good-symbolic'
                else:
                    icon = f'network-wireless-signal-excellent-symbolic'
                
                
            self.icon.set_from_icon_name(icon)
            self.icon.set_pixel_size(40)