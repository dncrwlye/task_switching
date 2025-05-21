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

class TrackingService:
    def __init__(self, task_tracker, window_monitor, switch_analyzer, flow_launcher=None, desktop_color=None):
        self.task_tracker = task_tracker
        self.window_monitor = window_monitor
        self.switch_analyzer = switch_analyzer
        self.flow_launcher = flow_launcher
        self.desktop_color = desktop_color
        self.running = False
        self.current_app = None
        self.last_switch_time = None
        self.tracking_thread = None
        
        # Color update counter
        self.color_update_interval = 0
    
    def tracking_loop(self):
        """Main tracking loop that runs in the background"""
        self.last_switch_time = datetime.datetime.now()
        self.current_app = self.window_monitor.get_active_window()
        print(f"Starting tracking. Current app: {self.current_app}")
        
        check_interval = 0
        self.color_update_interval = 0
        
        while self.running:
            time.sleep(1)  # Check every second
            new_app = self.window_monitor.get_active_window()
            if new_app != self.current_app:
                self.task_tracker.record_app_switch(self.current_app, new_app)
                self.current_app = new_app
            
            # Increment counters
            check_interval += 1
            self.color_update_interval += 1
            
            # Check for excessive switching every 10 seconds (for Flow app)
            if check_interval >= 10:
                excessive = self.switch_analyzer.check_excessive_task_switching()
                
                # Launch Flow app only in extreme cases
                if excessive and self.flow_launcher:
                    self.flow_launcher.launch_flow_app()
                
                check_interval = 0
            
            # Update desktop color more frequently (every 5 seconds)
            if self.desktop_color and self.color_update_interval >= self.desktop_color.update_interval:
                self.desktop_color.update_color_based_on_behavior()
                self.color_update_interval = 0
    
    def start(self):
        """Start the tracking process"""
        if not self.running:
            self.running = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            print("Task tracking started")
    
    def stop(self):
        """Stop the tracking process"""
        self.running = False
        print("Task tracking stopped")