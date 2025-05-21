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

class TaskTracker:
    def __init__(self, use_tsv=False):
        # Determine file type
        self.use_tsv = use_tsv
        self.delimiter = '\t' if use_tsv else ','
        self.file_extension = 'tsv' if use_tsv else 'csv'
        
        # Set up the data directory and file path
        self.data_dir = os.path.expanduser("~/task_switch/data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"Created data directory at {self.data_dir}")
        
        self.data_path = os.path.join(self.data_dir, f"task_tracker_data.{self.file_extension}")
        
        self.last_switch_time = None
        self.setup_datafile()
    
    def setup_datafile(self):
        """Initialize the CSV/TSV file if it doesn't exist"""
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w', newline='') as f:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerow(['id', 'timestamp', 'app_from', 'app_to', 'duration'])
                print(f"Created new {self.file_extension.upper()} file at {self.data_path}")
    
    def record_app_switch(self, app_from, app_to):
        """Record an application switch in the CSV/TSV file"""
        now = datetime.datetime.now().isoformat()
        duration = 0
        if self.last_switch_time:
            duration = int((datetime.datetime.now() - self.last_switch_time).total_seconds())
        
        # Get the next ID by counting existing rows
        next_id = 1
        try:
            with open(self.data_path, 'r', newline='') as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                next_id = sum(1 for _ in reader)  # Header counts as 1
        except FileNotFoundError:
            # File doesn't exist yet, start with ID 1
            pass
        
        # Append the new record
        with open(self.data_path, 'a', newline='') as f:
            writer = csv.writer(f, delimiter=self.delimiter)
            writer.writerow([next_id, now, app_from, app_to, duration])
        
        self.last_switch_time = datetime.datetime.now()
        print(f"Switch recorded: {app_from} -> {app_to} (Duration: {duration}s)")
