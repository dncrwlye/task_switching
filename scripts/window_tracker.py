import time
import datetime
import subprocess
import os
import threading
import csv
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw

class TaskTracker:
    def __init__(self, use_tsv=False):
        # Determine file type (CSV or TSV) based on user preference
        self.use_tsv = use_tsv
        self.delimiter = '\t' if use_tsv else ','
        self.file_extension = 'tsv' if use_tsv else 'csv'
        
        # Set up the data file path
        self.data_path = os.path.expanduser(f"~/task_tracker_data.{self.file_extension}")
        
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
    
    def tracking_loop(self):
        """Main tracking loop that runs in the background"""
        self.last_switch_time = datetime.datetime.now()
        self.current_app = self.get_active_window()
        print(f"Starting tracking. Current app: {self.current_app}")
        
        while self.running:
            time.sleep(1)  # Check every second
            new_app = self.get_active_window()
            
            if new_app != self.current_app:
                self.record_app_switch(self.current_app, new_app)
                self.current_app = new_app
    
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