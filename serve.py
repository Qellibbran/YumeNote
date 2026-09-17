#!/usr/bin/env python3
"""
Yume Note - Локальный сервер разработки и быстрого запуска для Android
"""

import http.server
import socket
import socketserver
import os
import sys

# Force UTF-8 output encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = 8080

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow cross-origin & caching headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    local_ip = get_local_ip()

    print("=" * 60)
    print("YUME NOTE - Local Server Started!")
    print("=" * 60)
    print(f"\nOpen on PC Browser:")
    print(f"   -> http://localhost:{PORT}")
    print(f"\nOpen and install on Android phone:")
    print(f"   -> http://{local_ip}:{PORT}")
    print("\nHow to install on Android:")
    print("   1. Connect phone to the same Wi-Fi network.")
    print(f"   2. Open Chrome on your phone and go to: http://{local_ip}:{PORT}")
    print("   3. Tap Chrome menu (three dots) -> 'Add to Home screen' / 'Install App'.")
    print("   4. Yume Note is installed as a full-screen native Android app!")
    print("\nPress Ctrl+C to stop the server.\n" + "=" * 60)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == '__main__':
    main()
