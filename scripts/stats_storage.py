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

class StatsStorage:
    def __init__(self, base_dir="~/task_switch"):
        """Initialize the stats storage with configurable base directory"""
        # Set up paths
        self.base_dir = os.path.expanduser(base_dir)
        self.data_dir = os.path.join(self.base_dir, "data")
        self.tracker_data_path = os.path.join(self.data_dir, "task_tracker_data.csv")
        self.stats_path = os.path.join(self.data_dir, "duration_stats.csv")
        # Create directory if needed
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"Created data directory at {self.data_dir}")

    def read_tracker_data(self):
        """Read the tracker data into a pandas DataFrame"""
        try:
            df = pd.read_csv(self.tracker_data_path)
            print(f"Read {len(df)} records from {self.tracker_data_path}")
            return df
        except FileNotFoundError:
            print(f"Warning: Data file not found at {self.tracker_data_path}")
            return pd.DataFrame(columns=["id", "timestamp", "app_from", "app_to", "duration"])
    
    def calculate_statistics(self):
        """Calculate key statistics from the tracker data"""
        df = self.read_tracker_data()
        
        if len(df) == 0:
            print("No data available for statistics calculation")
            return {}
        
        stats = {
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "count": len(df),
            "mean": df['duration'].mean(),
            "median": df['duration'].median(),
            "std": df['duration'].std(),
            "min": df['duration'].min(),
            "max": df['duration'].max()
        }
        
        return stats
    
    def save_statistics(self):
        """Calculate and save statistics to CSV file"""
        stats = self.calculate_statistics()
        
        if not stats:
            print("No statistics to save")
            return None
        
        file_exists = os.path.isfile(self.stats_path)
        
        with open(self.stats_path, 'a') as f:
            # Write header if file doesn't exist
            if not file_exists:
                header = ','.join(stats.keys())
                f.write(f"{header}\n")
            
            # Write values
            values = ','.join(str(v) for v in stats.values())
            f.write(f"{values}\n")
        
        print(f"Statistics saved to {self.stats_path}")
        return self.stats_path
    