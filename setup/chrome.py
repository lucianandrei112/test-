import subprocess
import time
import os
import platform
import socket
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Detect platform
IS_WINDOWS = platform.system() == "Windows"

# Base path
base_path = os.path.abspath(os.path.dirname(__file__))
karrero8000 = r"C:\Users\Arifsoft\Desktop\Folders\newproject\browsers\browser8888"  # Use this as default user-data-dir

# Chromedriver path
chrome_driver_filename = "chromedriver.exe" if IS_WINDOWS else "chromedriver"
chrome_driver_path = os.path.join(base_path, chrome_driver_filename)

# Chrome executable finder
def find_chrome_path():
    if IS_WINDOWS:
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
    else:
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome"
        ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("❌ Google Chrome not found on your system.")

# Port check utility
def is_chrome_debugging_running(port):
    """Check if Chrome with remote debugging is already running."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", int(port))) == 0

# Main function to open or connect to Chrome
def open_browser():
    chrome_path = find_chrome_path()
    user_data_dir = karrero8000
    port="8888"
    if not is_chrome_debugging_running(port):
        print(f"[INFO] Chrome not running on port {port} — launching it.")
        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)  # Wait for Chrome to be ready
    else:
        print(f"[INFO] Chrome already running on port {port} — connecting.")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")

    # Setup WebDriver
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver
