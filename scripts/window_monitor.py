import time
import datetime
import subprocess
import os
import threading
import csv
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import pandas as pd
import sys

class WindowMonitor:
    def __init__(self):
     """
    Initialize window monitor for macOS.
    """
    pass  # No initialization needed for basic functionality

    def get_active_window(self):
        """Get the currently active application on macOS using AppleScript"""
        try:
            cmd = """osascript -e 'tell application "System Events"' -e 'set frontApp to name of first application process whose frontmost is true' -e 'end tell'"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            return "Unknown"
        except Exception as e:
            print(f"Error getting active window: {e}")
            return "Error"