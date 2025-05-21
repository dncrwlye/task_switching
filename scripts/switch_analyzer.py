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

class TaskSwitchAnalyzer:
    def __init__(self, task_tracker, stats_storage):
        """
        Initialize analyzer with reference to TaskTracker for data access
        
        Args:
            task_tracker: TaskTracker instance that contains data path information
        """
        self.task_tracker = task_tracker
        self.stats_storage = stats_storage
        
    def read_recent_switches(self, minutes=1):
        """Read switches from CSV/TSV file within the last X minutes"""
        time_window = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        recent_switches = []
        
        try:
            with open(self.task_tracker.data_path, 'r', newline='') as f:
                reader = csv.reader(f, delimiter=self.task_tracker.delimiter)
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if len(row) >= 2:  # Make sure there's at least an ID and timestamp
                        try:
                            # Parse the timestamp (format: 2025-05-13T14:30:45.123456)
                            timestamp = datetime.datetime.fromisoformat(row[1])
                            if timestamp > time_window:
                                recent_switches.append(row)
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing row: {row}, {e}")
            
            return recent_switches
        except FileNotFoundError:
            print(f"Data file not found: {self.task_tracker.data_path}")
            return []
    def check_excessive_task_switching(self, minutes=1):
    # Get recent switches
        recent_switches = self.read_recent_switches(minutes)
    
    # If we don't have enough recent switches, no excessive switching
        if len(recent_switches) < 5:
            return False
    
    # Calculate average duration of recent app sessions
        recent_durations = [int(switch[4]) for switch in recent_switches if len(switch) > 4 and switch[4]]
        #print(recent_durations)
        if not recent_durations:
            return False
        
        recent_avg_duration = sum(recent_durations) / len(recent_durations)
    
    # Get historical statistics
        historical_stats = self.stats_storage.calculate_statistics()
    
    # Check if recent average duration is significantly lower than historical mean
        if historical_stats and 'mean' in historical_stats:
            historical_mean_duration = historical_stats['mean']
        
        # If recent durations are less than 50% of typical durations, that's excessive switching
            threshold_ratio = 0.5  # This can be adjusted based on desired sensitivity
        
            print(f"Recent avg duration: {recent_avg_duration:.1f}s, Historical mean: {historical_mean_duration:.1f}s")
        
            if recent_avg_duration < historical_mean_duration * threshold_ratio:
                print("EXCESSIVE TASK SWITCHING DETECTED - User isn't staying in apps long enough!")
                return True
    
        return False