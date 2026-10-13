"""
LibAR Public HTTPS Tunnel & Mobile Launcher
Starts the LibAR backend and opens an instant secure HTTPS URL for mobile access.
"""

import os
import subprocess
import sys
import time
import threading
import qrcode
from waitress import serve
from app import app

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
        print("   📱 SCAN WITH IPHONE / ANDROID TO LAUNCH LIBAR:")
        print("=" * 54 + "\n")
        qr.print_ascii(invert=True)
        print("\n" + "=" * 54 + "\n")
    except Exception as e:
        print(f"QR display note: {e}")

def run_server():
    serve(app, host="0.0.0.0", port=5000, threads=6)

def main():
    print("\n" + "#" * 60)
    print("   🚀 Starting LibAR Mobile Backend & Public HTTPS Tunnel")
    print("#" * 60)

    # Start Flask/Waitress in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)
    print(" ✓ Local backend running on http://127.0.0.1:5000")

    # Start localtunnel
    print(" → Opening secure HTTPS tunnel for mobile phone access...")
    try:
        proc = subprocess.Popen(
            ["npx", "--yes", "localtunnel", "--port", "5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        for line in iter(proc.stdout.readline, ''):
            if "your url is:" in line.lower():
                tunnel_url = line.strip().split()[-1]
                print(f"\n" + "★" * 60)
                print(f"   🌟 PUBLIC HTTPS MOBILE LINK: {tunnel_url}")
                print(f"★" * 60)
                print_qr_code(tunnel_url)
                print("Open the link above on your mobile phone to use LibAR!")
                print("Press Ctrl+C to stop.")
                break

        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping LibAR tunnel server...")
    except Exception as e:
        print(f"\nNote on tunnel: {e}")
        print("You can access LibAR via your local network URL shown in run_production.py")
        server_thread.join()

if __name__ == "__main__":
    main()
