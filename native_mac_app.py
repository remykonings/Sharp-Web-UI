import argparse
import socket
import subprocess
import time
import urllib.request

import webview

import app


def port_is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def find_available_port(preferred=7880):
    if not port_is_open(preferred):
        return preferred

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(url, timeout_seconds=30):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.8):
                return True
        except Exception:
            time.sleep(0.12)
    return False


def show_alert(title, message):
    # Keep launcher failures visible when started via Finder.
    safe_title = title.replace('"', "'")
    safe_message = message.replace('"', "'")
    subprocess.run(
        ["osascript", "-e", f'display alert "{safe_title}" message "{safe_message}" as critical'],
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Run Sharp Web UI in a native macOS window.")
    parser.add_argument("--check", action="store_true", help="Start server, verify availability, then exit.")
    args = parser.parse_args()

    port = find_available_port(7880)
    url = f"http://127.0.0.1:{port}"

    try:
        app.demo.launch(
            server_name="127.0.0.1",
            server_port=port,
            inbrowser=False,
            show_api=False,
            quiet=True,
            prevent_thread_lock=True,
            allowed_paths=[app.ASSETS_DIR, app.OUTPUT_DIR, "/"],
        )
    except Exception as exc:
        show_alert("Sharp Web UI Error", f"Could not start local server.\n{exc}")
        raise

    if not wait_for_server(url):
        show_alert("Sharp Web UI Error", "Local server started too slowly or failed to respond.")
        try:
            app.demo.close()
        except Exception:
            pass
        return

    if args.check:
        print(f"OK: native launcher server reachable at {url}")
        app.demo.close()
        return

    window = webview.create_window(
        "Sharp Web UI",
        url=url,
        width=1440,
        height=900,
        min_size=(1024, 700),
        background_color="#0f172a",
    )
    try:
        webview.start(debug=False, gui="cocoa")
    finally:
        try:
            app.demo.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
