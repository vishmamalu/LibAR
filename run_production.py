"""
LibAR Production & Mobile Server Runner
Supports local LAN access, QR code terminal generation, Waitress WSGI, and HTTPS options.
"""

import os
import socket
import sys
from pathlib import Path
import qrcode
from waitress import serve
from app import app

def get_local_ip() -> str:
    """Find the local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect, just determines route
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def print_qr_code(url: str):
    """Print an ASCII QR code in the terminal for instant mobile scanning."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        print("\n" + "=" * 54)
        print("   📱 SCAN WITH YOUR PHONE TO OPEN LIBAR:")
        print("=" * 54 + "\n")
        qr.print_ascii(invert=True)
        print("\n" + "=" * 54 + "\n")
    except Exception as e:
        print(f"QR display note: {e}")

def main():
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    local_ip = get_local_ip()

    http_url = f"http://{local_ip}:{port}"
    localhost_url = f"http://localhost:{port}"

    print("\n" + "#" * 60)
    print("   📚 LibAR — Mobile AR Library Navigation Server")
    print("#" * 60)
    print(f"\n ✓ Local Desktop URL:  {localhost_url}")
    print(f" ✓ Mobile Network URL:  {http_url}")
    print(f" ✓ Status:              Production WSGI Ready (Waitress)")
    print(f" ✓ AR Features:         Movement-Responsive 3D & Spatial AR")

    print_qr_code(http_url)

    print(f"Server is listening on http://{host}:{port} (Press Ctrl+C to stop)...")
    serve(app, host=host, port=port, threads=6)

if __name__ == "__main__":
    main()
