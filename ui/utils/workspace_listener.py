import os
import socket
import threading
import subprocess
import json

from gi.repository import GLib

class WorkspaceListener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.callbacks = []
        self.sock_path = self._get_socket_path()

        # Start listening thread
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _get_socket_path(self):
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not sig:
            raise RuntimeError("HYPRLAND_INSTANCE_SIGNATURE not set (are you inside Hyprland?)")

        base = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        path = os.path.join(base, "hypr", sig, ".socket2.sock")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Hyprland socket2 not found at {path}")
        return path

    def attach_callback(self, cb):
        """Attach a callback that receives the 10-element workspace array."""
        if callable(cb):
            self.callbacks.append(cb)

    def _listen(self):
        """Listen for Hyprland IPC events."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.sock_path)

            while True:
                data = s.recv(4096).decode("utf-8", errors="ignore")
                if not data:
                    break

                for line in data.strip().splitlines():
                    if line.startswith("workspace"):
                        self._handle_workspace_event()

    def _handle_workspace_event(self):
        """Fetch simplified workspace info and notify callbacks."""
        try:
            workspaces = json.loads(subprocess.check_output(
                ["hyprctl", "workspaces", "-j"], text=True
            ))
            active = json.loads(subprocess.check_output(
                ["hyprctl", "activeworkspace", "-j"], text=True
            ))
        except subprocess.CalledProcessError as e:
            print(f"Error fetching workspace info: {e}")
            return

        result = [None] * 10
        for ws in workspaces:
            idx = ws["id"] - 1
            if 0 <= idx < 10:
                result[idx] = {
                    "id": ws["id"],
                    "name": ws["name"],
                    "windows": ws["windows"],
                    "active": ws["id"] == active.get("id")
                }

        for cb in self.callbacks:
            try:
                GLib.idle_add(cb, result)
            except Exception as e:
                print(f"Callback error: {e}")