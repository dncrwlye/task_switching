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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from color_change import set_desktop_color

from tracking_service import TrackingService
from task_tracker import TaskTracker
from window_monitor import WindowMonitor
from switch_analyzer import TaskSwitchAnalyzer
from stats_storage import StatsStorage
from launch_flow import LaunchFlow
from color_change import DesktopColor

def create_image():
    """Create a simple icon for the system tray"""
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(0, 120, 212))
    return image

def setup_tray_icon(tracking_service):
    """Set up the system tray icon and menu"""
    
    def on_start(icon, item):
        tracking_service.start()
        icon.update_menu()
    
    def on_stop(icon, item):
        tracking_service.stop()
        icon.update_menu()
    
    def on_exit(icon, item):
        tracking_service.stop()
        icon.stop()
    
    # Create the menu
    menu = (
        item('Start Tracking', on_start, enabled=lambda item: not tracking_service.running),
        item('Stop Tracking', on_stop, enabled=lambda item: tracking_service.running),
        item('Exit', on_exit)
    )
    
    # Create the icon
    icon = pystray.Icon("TaskTracker", create_image(), "Task Tracker", menu)
    return icon

if __name__ == "__main__":
    # Set to True for TSV, False for CSV
    use_tsv = False  # Change this value based on your preference
    
    # Create all the components
    task_tracker = TaskTracker(use_tsv=use_tsv)
    window_monitor = WindowMonitor()
    stats_storage = StatsStorage()
    switch_analyzer = TaskSwitchAnalyzer(task_tracker, stats_storage)
    flow_launcher = LaunchFlow()
    desktop_color = DesktopColor(switch_analyzer, stats_storage)  # Pass stats_storage
    
    # Create the tracking service that coordinates everything
    tracking_service = TrackingService(
        task_tracker=task_tracker,
        window_monitor=window_monitor,
        switch_analyzer=switch_analyzer,
        flow_launcher=flow_launcher,
        desktop_color=desktop_color
    )
    
    # Set up the system tray icon
    icon = setup_tray_icon(tracking_service)
    
    # Start tracking automatically on launch
    tracking_service.start()
    
    # Run the system tray icon (this will block until you exit)
    icon.run()