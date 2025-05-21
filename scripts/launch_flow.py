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

class LaunchFlow:
    def __init__(self):
        pass
    def launch_flow_app(self):
        """Launch the Flow app"""
        try:
            # For macOS
            subprocess.run(["open", "-a", "Flow"])
            print("Launched Flow app to help you focus")
            #set_desktop_color(255, 0, 0)
        except Exception as e:
            print(f"Error launching Flow app: {e}")