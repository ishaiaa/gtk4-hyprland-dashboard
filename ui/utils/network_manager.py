import gi
import ipaddress
import threading
import time
from gi.repository import NM, GLib

gi.require_version("NM", "1.0")

class NetworkMonitorSingleton:
    _instance = None
    _lock = threading.Lock()
    AP_TIMEOUT = 60  # seconds before an AP is considered out of range

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, update_interval=5, scan_interval=20):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.client = NM.Client.new(None)
        self.update_interval = update_interval
        self.scan_interval = scan_interval
        self.data = {}
        self.skip_types = {
            NM.DeviceType.LOOPBACK,
            NM.DeviceType.WIFI_P2P,
            NM.DeviceType.BRIDGE,
            NM.DeviceType.OLPC_MESH,
            NM.DeviceType.TUN,
            NM.DeviceType.DUMMY,
        }
        self._known_aps = {}  # key=bssid, value=(AP info dict, last_seen_timestamp)

        # Start the background update thread
        threading.Thread(target=self._update_loop, daemon=True).start()

        # Start periodic async Wi-Fi scans
        self._schedule_scan()

    def _enum_to_str(self, obj):
        return str(obj.value if hasattr(obj, "value") else obj)

    # --- Wi-Fi scanning ---
    def _schedule_scan(self):
        wifi_dev = next((d for d in self.client.get_devices() if d.get_device_type() == NM.DeviceType.WIFI), None)
        if wifi_dev:
            def do_scan():
                try:
                    wifi_dev.request_scan_async(None, None)
                except Exception:
                    pass
                return False
            GLib.idle_add(do_scan)
        GLib.timeout_add_seconds(self.scan_interval, self._schedule_scan)
        return False

    def _cache_access_points(self):
        now = time.time()
        wifi_devs = [d for d in self.client.get_devices() if d.get_device_type() == NM.DeviceType.WIFI]
        for dev in wifi_devs:
            for ap in dev.get_access_points():
                bssid = ap.get_bssid()
                self._known_aps[bssid] = ({
                    "ssid": ap.get_ssid().get_data().decode(errors="ignore"),
                    "bssid": bssid,
                    "strength": str(ap.get_strength()),
                    "flags": self._enum_to_str(ap.get_flags()),
                    "wpa_flags": self._enum_to_str(ap.get_wpa_flags()),
                    "rsn_flags": self._enum_to_str(ap.get_rsn_flags()),
                }, now)

    def list_available_networks(self):
        now = time.time()
        # remove old APs
        self._known_aps = {bssid: (info, ts) for bssid, (info, ts) in self._known_aps.items()
                           if now - ts < self.AP_TIMEOUT}
        # update cache from current scan
        self._cache_access_points()
        return [info for info, _ in self._known_aps.values()]

    # --- Devices and saved networks ---
    def list_devices(self):
        devices_info = []
        for dev in self.client.get_devices():
            if dev.get_device_type() in self.skip_types:
                continue

            info = {
                "iface": dev.get_iface(),
                "type": self._enum_to_str(dev.get_device_type()),
                "state": self._enum_to_str(dev.get_state()),
                "ip4": [],
                "ip6": [],
            }

            ip4cfg = dev.get_ip4_config()
            if ip4cfg:
                info["ip4"] = [ipaddress.IPv4Interface(addr.get_address() + f"/{addr.get_prefix()}").with_prefixlen
                                for addr in ip4cfg.get_addresses()]

            ip6cfg = dev.get_ip6_config()
            if ip6cfg:
                info["ip6"] = [ipaddress.IPv6Interface(addr.get_address() + f"/{addr.get_prefix()}").with_prefixlen
                                for addr in ip6cfg.get_addresses()]

            if dev.get_device_type() == NM.DeviceType.WIFI:
                active_ap = dev.get_active_access_point()
                if active_ap:
                    info["connected_ap"] = {
                        "ssid": active_ap.get_ssid().get_data().decode(errors="ignore"),
                        "bssid": active_ap.get_bssid(),
                        "strength": str(active_ap.get_strength()),
                        "flags": self._enum_to_str(active_ap.get_flags()),
                        "wpa_flags": self._enum_to_str(active_ap.get_wpa_flags()),
                        "rsn_flags": self._enum_to_str(active_ap.get_rsn_flags()),
                    }
            devices_info.append(info)
        return devices_info

    def list_saved_networks(self):
        connections_info = []
        for conn in self.client.get_connections():
            s_con = conn.get_setting_connection()
            s_wifi = conn.get_setting_wireless()
            if not s_con or not s_wifi:
                continue
            ssid = s_wifi.get_ssid()
            if ssid:
                ssid = ssid.get_data().decode(errors="ignore")
            connections_info.append({
                "id": s_con.get_id(),
                "uuid": s_con.get_uuid(),
                "ssid": ssid,
                "mode": s_wifi.get_mode(),
                "mac_address": s_wifi.get_mac_address(),
            })
        return connections_info

    def collect_all(self):
        return {
            "devices": self.list_devices(),
            "saved_networks": self.list_saved_networks(),
            "available_networks": self.list_available_networks(),
        }

    def _update_loop(self):
        while True:
            try:
                self.data = self.collect_all()
            except Exception:
                pass
            time.sleep(self.update_interval)

    def get_data(self):
        return self.data

    # --- Wi-Fi management with callbacks ---
    def enable_wifi(self, enable: bool, callback=None):
        def task():
            try:
                wifi_dev = next(d for d in self.client.get_devices() if d.get_device_type() == NM.DeviceType.WIFI)
                wifi_dev.enable(enable)
                if callback:
                    callback(0)
            except Exception:
                if callback:
                    callback(1)
        threading.Thread(target=task, daemon=True).start()

    def connect_saved(self, bssid, callback=None):
        def task():
            try:
                wifi_dev = next(d for d in self.client.get_devices() if d.get_device_type() == NM.DeviceType.WIFI)
                ap = next(ap for ap in wifi_dev.get_access_points() if ap.get_bssid() == bssid)
                connections = self.client.get_connections()
                conn = None
                for c in connections:
                    s_wifi = c.get_setting_wireless()
                    if s_wifi and s_wifi.get_ssid() == ap.get_ssid():
                        conn = c
                        break
                if conn:
                    self.client.activate_connection(conn, wifi_dev, ap)
                    if callback:
                        callback(0)
                else:
                    if callback:
                        callback(2)
            except Exception:
                if callback:
                    callback(1)
        threading.Thread(target=task, daemon=True).start()

    def connect_new(self, ssid, password=None, callback=None):
        def task():
            try:
                wifi_dev = next(d for d in self.client.get_devices() if d.get_device_type() == NM.DeviceType.WIFI)
                ssid_bytes = bytes(ssid, "utf-8")
                connection = NM.SimpleConnection.new()
                s_con = NM.SettingConnection.new()
                s_con.set_property("id", ssid)
                s_con.set_property("type", "802-11-wireless")
                connection.add_setting(s_con)

                s_wifi = NM.SettingWireless.new()
                s_wifi.set_property("ssid", GLib.Bytes.new(ssid_bytes))
                s_wifi.set_property("mode", "infrastructure")
                connection.add_setting(s_wifi)

                if password:
                    s_sec = NM.SettingWirelessSecurity.new()
                    s_sec.set_property("key-mgmt", "wpa-psk")
                    s_sec.set_property("psk", password)
                    connection.add_setting(s_sec)

                new_conn = self.client.add_connection(connection)
                self.client.activate_connection(new_conn, wifi_dev, None)
                if callback:
                    callback(0)
            except Exception:
                if callback:
                    callback(1)
        threading.Thread(target=task, daemon=True).start()


# automatically initialize singleton at import
network_monitor = NetworkMonitorSingleton()
