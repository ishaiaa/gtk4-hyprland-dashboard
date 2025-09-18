#!/programming/gtk4-hyprland-dashboard/.venv/bin/python3
import os
import sys
import socket
import threading
import pynvml
import ctypes
ctypes.CDLL("libgtk4-layer-shell.so")


from dotenv import load_dotenv
load_dotenv()


from gi.repository import GLib
from ui.utils import load_css
from ui.app import MyApp

DEBUG = "--debug" in sys.argv

# Load variables from .env

os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"


SOCKET_PATH = "/tmp/hyperdash.sock"

def start_socket_server(app: MyApp):
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)

    def handle_connections():
        while True:
            conn, _ = server.accept()
            data = conn.recv(1024).decode().strip()
            if data == "toggle":
                GLib.idle_add(lambda: app.toggle_visibility())
            elif data == "quit":
                GLib.idle_add(lambda: app.quit())
            conn.close()

    threading.Thread(target=handle_connections, daemon=True).start()

def is_dashboard_running():
    if not os.path.exists(SOCKET_PATH):
        return False
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.close()
        return True
    except Exception:
        return False

def main():
    if "--start" in sys.argv:
        if is_dashboard_running():
            print("Dashboard is already running!")
            sys.exit(1)
            
        pynvml.nvmlInit()

        # Load CSS
        load_css("./styles/style.css")
        load_css("./styles/calendar.css")
        load_css("./styles/power.css")
        load_css("./styles/clock.css")
        load_css("./styles/weather.css")
        load_css("./styles/perf.css")
        load_css("./styles/processmonitor.css")
        load_css("./styles/windowfix.css")
        load_css("./styles/notifications-layer.css")
        load_css("./styles/notifications.css")
        load_css("./styles/workspaces.css")
        load_css("./styles/imagedisplay.css")
        load_css("./styles/applauncher.css")

        print(f'DBG: {DEBUG}')
        print(sys.argv)

        app = MyApp(debug=DEBUG)
        
        start_socket_server(app)  # 🔌 enable socket control
        app.run()

    elif "--toggle" in sys.argv or "--quit" in sys.argv:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        if "--toggle" in sys.argv:
            client.sendall(b"toggle")
        elif "--quit" in sys.argv:
            client.sendall(b"quit")
        client.close()

    else:
        print("Usage: ./main.py --start | --toggle | --quit")

if __name__ == "__main__":
    main()