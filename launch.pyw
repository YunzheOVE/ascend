"""Double-click to open Ascend: starts the judge in the background if it isn't running, then opens the browser.
(.pyw files run without a console window on Windows.)"""
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

URL = "http://localhost:8000/"
HERE = os.path.dirname(os.path.abspath(__file__))


def running():
    try:
        urllib.request.urlopen(URL + "api/roadmap", timeout=1)
        return True
    except OSError:
        return False


if not running():
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    # pythonw keeps the server windowless; it keeps running after this launcher exits
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pythonw, os.path.join(HERE, "server.py")], cwd=HERE, creationflags=flags, close_fds=True)
    for _ in range(100):  # wait up to ~20 s for the first start (problem bank import)
        if running():
            break
        time.sleep(0.2)
webbrowser.open(URL)
