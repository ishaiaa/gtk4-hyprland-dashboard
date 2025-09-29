import threading
import traceback
import sdbus
import uuid
import asyncio
import time


from pprint import pprint
from sdbus_block.networkmanager import (
    NetworkManager,
    NetworkManagerSettings,
    NetworkDeviceGeneric,
    NetworkConnectionSettings,
    NetworkDeviceWireless,
    IPv4Config,
    ActiveConnection,
    AccessPoint,
    NetworkConnectionSettings,
    ConnectivityState,
    DeviceState,
    ConnectionState
)
from sdbus_block.networkmanager.enums import (
    DeviceType
)



sdbus.set_default_bus(sdbus.sd_bus_open_system())

from gi.repository import GLib

class NetworkMonitor():
    def __init__(self):
        self.network_manager = NetworkManager()
        self.network_manager_settings = NetworkManagerSettings()
        self._devices = []
        self._track_devices()
        self._scan_networks()
        GLib.timeout_add_seconds(30, self._scan_networks)
        
    def _track_devices(self):
        self._devices = []
        for path in self.network_manager.devices:
            dev = NetworkDeviceGeneric(path)
            type = dev.device_type
            if type not in [DeviceType.WIFI, DeviceType.ETHERNET]:
                continue
            self._devices.append({
                "path": path,
                "iface": dev.interface,
                "wireless": type == DeviceType.WIFI
            })
        

    def get_devices_data(self):
        devices = []
        for device_dict in self._devices:
            dev = None
            if device_dict["wireless"]:
                dev = NetworkDeviceWireless(device_dict["path"])
            else:
                dev = NetworkDeviceGeneric(device_dict["path"])
            
            type = dev.device_type
            connection_status = dev.ip4_connectivity
            connection_details = None
            ip4 = None
            
            if connection_status > 1:
                try:
                    ip4 = IPv4Config(dev.ip4_config).address_data[0]["address"][1]
                except:
                    ip4 = None
                    
                if type == DeviceType.WIFI and dev.active_access_point is not "/":
                    ap = AccessPoint(dev.active_access_point)
                    connection_details = {
                        "ssid": str(ap.ssid.decode('utf-8')),
                        "bssid": str(ap.hw_address),
                        "strength": ap.strength,
                        "wpa_flags": ap.wpa_flags,
                        "rsn_flags": ap.rsn_flags
                    }
                    
            devices.append({
                "iface": dev.interface,
                "type": "wifi" if type == DeviceType.WIFI else "ethernet",
                "state": dev.state,
                "status": connection_status,
                "ip4": ip4,
                "connected_ap": connection_details
            })
        
        return devices

    def get_saved_networks(self):
        conn = self.network_manager_settings.list_connections()
        saved_networks = []
        for c in conn:
            settings = NetworkConnectionSettings(c).get_settings()
            if settings["connection"]["type"][1] == "802-11-wireless" and "HYPRDASH_TEMP" not in settings["connection"]["id"][1]:
                # pprint(settings)
                saved_networks.append({
                    "id": settings["connection"]["id"][1],
                    "uuid": settings["connection"]["uuid"][1],
                    "ssid": str(settings["802-11-wireless"]["ssid"][1].decode('utf-8')),
                    "iface": settings["connection"]["interface-name"][1]
                })
        # print("---")
        return saved_networks
    
    def _scan_networks(self):
        for device_dict in self._devices:
            if not device_dict["wireless"]:
                continue
            
            try:
                dev = NetworkDeviceWireless(device_dict["path"])
                dev.request_scan({})
            except:
                pass
        return True
    
    def get_aviable_networks(self):
        aviable_networks = []
        for device_dict in self._devices:
            if not device_dict["wireless"]:
                continue
            
            dev = NetworkDeviceWireless(device_dict["path"])
            for ap_path in dev.get_all_access_points():
                ap = AccessPoint(ap_path)
                aviable_networks.append({
                    "ssid": str(ap.ssid.decode('utf-8')),
                    "bssid": str(ap.hw_address),
                    "strength": ap.strength,
                    "iface": device_dict["iface"],
                    "wpa_flags": ap.wpa_flags,
                    "rsn_flags": ap.rsn_flags
                })
        return aviable_networks

    def get_data(self):
        return {
            "devices": self.get_devices_data(),
            "saved_networks": self.get_saved_networks(),
            "available_networks": self.get_aviable_networks(),
        }

    """
    CONNECTION MANAGEMENT METHODS
    """

    def enable_wifi(self, iface: str, enable: bool, callback=None):
        try:
            device = None
            for device_dict in self._devices:
                if device_dict["iface"] == iface:
                    device = NetworkDeviceWireless(device_dict["path"])
                    break
                    
            def do_enable():
                try:
                    device.managed = enable
                    if callback:
                        GLib.idle_add(callback, 0)
                except Exception:
                    if callback:
                        GLib.idle_add(callback, 1)
                return False

            GLib.idle_add(do_enable)
        except Exception:
            if callback:
                GLib.idle_add(callback, 1)

    def disconnect_wifi(self, iface: str, callback=None):
        def task():
            bus = sdbus.sd_bus_open_system()

            nm = sdbus.DbusInterfaceCommon(
                bus,
                '/org/freedesktop/NetworkManager',
                'org.freedesktop.NetworkManager'
            )
            try:
                deactivated = False
                for device_dict in self._devices:
                    print(device_dict)
                    if device_dict["iface"] == iface:
                        dev = NetworkDeviceWireless(device_dict["path"], bus=bus)
                        if dev.ip4_connectivity > 1:
                            self.network_manager.deactivate_connection(dev.active_connection)
                            deactivated = True
                        break
                
                if deactivated and callback:
                    GLib.idle_add(callback, 0)
            except Exception:
                traceback.print_exc()
                if callback:
                    GLib.idle_add(callback, 1)
        threading.Thread(target=task, daemon=True).start()


    def connect_saved(self, iface: str, uuid: str, callback=None):
        conn_path = None
        
        for c in self.network_manager_settings.list_connections():
            if NetworkConnectionSettings(c).get_settings()["connection"]["uuid"][1] == uuid:
                conn_path = c
                break
        
        device_path = None
        for device_dict in self._devices:
            if device_dict["iface"] == iface:            
                device_path = device_dict["path"]
                break
        print(f'CONNECT SAVED\n{device_path}\n{conn_path}')
            
        if not conn_path or not device_path:
            if callback:
                GLib.idle_add(callback, 1)
            return
            
        self.network_manager.activate_connection(conn_path, device_path)
            
        def task():
            try:
                if callback:
                    GLib.idle_add(callback, 0)
            except Exception:
                if callback:
                    GLib.idle_add(callback, 1)
                    
        threading.Thread(target=task, daemon=True).start()
        
    def forget_saved(self, uuid: str, callback=None):
        conn_path = None
        
        for c in self.network_manager_settings.list_connections():
            if NetworkConnectionSettings(c).get_settings()["connection"]["uuid"][1] == uuid:
                conn_path = c
                break
            
        if not conn_path :
            if callback:
                GLib.idle_add(callback, 1)
            return
            
        def task():
            bus = sdbus.sd_bus_open_system()

            nm = sdbus.DbusInterfaceCommon(
                bus,
                '/org/freedesktop/NetworkManager',
                'org.freedesktop.NetworkManager'
            )
            
            try:
                NetworkConnectionSettings(conn_path, bus=bus).delete()
                if callback:
                    GLib.idle_add(callback, 0)
            except Exception:
                if callback:
                    GLib.idle_add(callback, 1)
                    
        threading.Thread(target=task, daemon=True).start()
        
        
    def connect_new(self, iface: str, ssid: str, password: str = None, callback=None):
        device_path = None
        for device_dict in self._devices:
            if device_dict["iface"] == iface:            
                device_path = device_dict["path"]
                break

        if not device_path:
            if callback:
                GLib.idle_add(callback, 1)
            return

        # temporary connection settings using D-Bus typed values
        conn_settings = {
            "connection": {
                "id": ("s", f"HYPRDASH_TEMP {ssid}"),
                "type": ("s", "802-11-wireless"),
                "uuid": ("s", str(uuid.uuid4())),
                "interface-name": ("s", iface)
            },
            "802-11-wireless": {
                "ssid": ("ay", ssid.encode()),  # array of bytes
                "mode": ("s", "infrastructure")
            },
            "ipv4": {"method": ("s", "auto")},
            "ipv6": {"method": ("s", "auto")}
        }

        if password:
            conn_settings["802-11-wireless-security"] = {
                "key-mgmt": ("s", "wpa-psk"),
                "psk": ("s", password)
            }

        conn_settings_path, active_connection_path = self.network_manager.add_and_activate_connection(conn_settings, device_path, "/")
        
        def task():
            bus = sdbus.sd_bus_open_system()

            nm = sdbus.DbusInterfaceCommon(
                bus,
                '/org/freedesktop/NetworkManager',
                'org.freedesktop.NetworkManager'
            )
            
            try:
                # add and activate temporary connection
                active_connection = ActiveConnection(active_connection_path, bus=bus)
                active_conn = ActiveConnection(active_connection_path, bus=bus)
                timeout = 15
                start = time.time()
                connected = False
                bad_password = False
                while True:
                    try:
                        time_passed = time.time() - start
                        print(time_passed)
                        state = active_conn.state
                        print(state)
                        if state == ConnectionState.ACTIVATED:
                            connected = True
                            self.network_manager.deactivate_connection(active_connection_path)
                            break
                        elif state  == ConnectionState.DEACTIVATED:
                            bad_password = True #Not 100% accurate, but propable enough for my usecase xD
                            break
                        elif state == ConnectionState.UNKNOWN or time_passed > timeout:
                            self.network_manager.deactivate_connection(active_connection_path)
                            break
                        time.sleep(0.1)
                    except:
                        bad_password = True
                        break
                
                
                
                
                
                if connected:
                    
                    
                    def update_settings():
                        temp_conn = NetworkConnectionSettings(conn_settings_path)
                        new_settings = dict(temp_conn.get_settings())
                        new_settings["connection"]["id"] = ("s", ssid)
                        temp_conn.update(new_settings)
                        self.network_manager.activate_connection(conn_settings_path)
                    
                    GLib.idle_add(update_settings)
                    
                    if callback:
                        GLib.idle_add(callback, 0)
                else:
                    temp_conn = NetworkConnectionSettings(conn_settings_path, bus=bus)
                    temp_conn.delete()
                    if callback:
                        GLib.idle_add(callback, 2 if bad_password else 1)

            except Exception as e:
                traceback.print_exc()
                print("Failed to connect:", e)
                # clean up temp connection if it exists
                if conn_settings_path:
                    try:
                        NetworkConnectionSettings(conn_settings_path, bus=bus).delete()
                    except Exception:
                        pass

                if callback:
                    GLib.idle_add(callback, 1)

        threading.Thread(target=task, daemon=True).start()
