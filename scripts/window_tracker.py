import time
import datetime
import subprocess
import os
import threading
import csv
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw
import pandas as pd

class TaskTracker:
    def __init__(self, use_tsv=False):
        # Determine file type (CSV or TSV) based on user preference
        self.use_tsv = use_tsv
        self.delimiter = '\t' if use_tsv else ','
        self.file_extension = 'tsv' if use_tsv else 'csv'
        
        # Set up the data directory and file path
        self.data_dir = os.path.expanduser("~/task_switch/data")
        # Create the data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"Created data directory at {self.data_dir}")
        
        self.data_path = os.path.join(self.data_dir, f"task_tracker_data.{self.file_extension}")
        
        self.running = False
        self.current_app = None
        self.last_switch_time = None
        self.setup_datafile()
    
    def setup_datafile(self):
        """Initialize the CSV/TSV file if it doesn't exist"""
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w', newline='') as f:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerow(['id', 'timestamp', 'app_from', 'app_to', 'duration'])
                print(f"Created new {self.file_extension.upper()} file at {self.data_path}")
    
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
    
    def read_recent_switches(self, minutes=1):
        """Read switches from CSV/TSV file within the last X minutes"""
        time_window = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        recent_switches = []
        
        try:
            with open(self.data_path, 'r', newline='') as f:
                reader = csv.reader(f, delimiter=self.delimiter)
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
            print(f"Data file not found: {self.data_path}")
            return []
    
    def check_excessive_task_switching(self, minutes=1, threshold=2):
        """Check if user has switched tasks too frequently in recent minutes"""
        recent_switches = self.read_recent_switches(minutes)
        switch_count = len(recent_switches)
        
        print(f"DEBUG: Found {switch_count} switches in the last {minutes} minute(s)")
        
        if switch_count > threshold:
            print("EXCESSIVE TASK SWITCHING DETECTED!")
            print(f"You've switched tasks {switch_count} times in the last {minutes} minute(s).")
            # Uncomment when you're ready to launch Flow:
            self.launch_flow_app()
            return True
        
        return False
    
    def launch_flow_app(self):
        """Launch the Flow app"""
        try:
            # For macOS
            subprocess.run(["open", "-a", "Flow"])
            print("Launched Flow app to help you focus")
        except Exception as e:
            print(f"Error launching Flow app: {e}")
    
    def tracking_loop(self):
        """Main tracking loop that runs in the background"""
        self.last_switch_time = datetime.datetime.now()
        self.current_app = self.get_active_window()
        print(f"Starting tracking. Current app: {self.current_app}")
        
        check_interval = 0
        
        while self.running:
            time.sleep(1)  # Check every second
            new_app = self.get_active_window()
            
            if new_app != self.current_app:
                self.record_app_switch(self.current_app, new_app)
                self.current_app = new_app
            
            # Check for excessive switching every 10 seconds
            check_interval += 1
            if check_interval >= 10:
                self.check_excessive_task_switching()
                check_interval = 0
    
    def start(self):
        """Start the tracking process"""
        if not self.running:
            self.running = True
            self.tracking_thread = threading.Thread(target=self.tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()
            print(f"Task tracking started - saving to {self.data_path}")
    
    def stop(self):
        """Stop the tracking process"""
        self.running = False
        print("Task tracking stopped")

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
    

#okay, so we should save the stats at the end of every session, somehow
#then, those would be used to calculated 






















def create_image():
    """Create a simple icon for the system tray"""
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(0, 120, 212))
    return image

def setup_tray_icon(tracker):
    """Set up the system tray icon and menu"""
    
    def on_start(icon, item):
        tracker.start()
        icon.update_menu()
    
    def on_stop(icon, item):
        tracker.stop()
        icon.update_menu()
    
    def on_exit(icon, item):
        tracker.stop()
        icon.stop()
    
    # Create the menu
    menu = (
        item('Start Tracking', on_start, enabled=lambda item: not tracker.running),
        item('Stop Tracking', on_stop, enabled=lambda item: tracker.running),
        item('Exit', on_exit)
    )
    
    # Create the icon
    icon = pystray.Icon("TaskTracker", create_image(), "Task Tracker", menu)
    return icon

if __name__ == "__main__":
    # Set to True for TSV, False for CSV
    use_tsv = False  # Change this value based on your preference
    
    tracker = TaskTracker(use_tsv=use_tsv)
    icon = setup_tray_icon(tracker)
    
    # Start tracking automatically on launch
    tracker.start()
    
    # Run the system tray icon (this will block until you exit)
    icon.run()
