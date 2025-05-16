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

#this is now the main controller class

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

class DesktopColor:
    def __init__(self, switch_analyzer, stats_storage):
        self.switch_analyzer = switch_analyzer
        self.stats_storage = stats_storage
        
        # Define color range (from calm to intense)
        self.calm_color = (0, 100, 255)  # Blue (calm)
        self.warning_color = (255, 0, 0)  # Red (excessive switching)
        
        # How often to update the color (in seconds)
        self.update_interval = 5
        
    def calculate_color_intensity(self, recent_duration, historical_mean):
        """
        Calculate color intensity based on how current behavior 
        compares to historical average.
        
        Returns a value between 0.0 (calm) and 1.0 (excessive switching)
        """
        if historical_mean <= 0:
            return 0.0
            
        # Calculate ratio of recent to historical duration
        # Lower ratio means more switching (shorter durations)
        ratio = recent_duration / historical_mean
        
        # Invert and clamp the ratio to get intensity
        # 1.0 means recent durations are 0% of historical (extreme switching)
        # 0.0 means recent durations are 100% or more of historical (normal or better)
        intensity = max(0.0, min(1.0, 1.0 - ratio))
        
        return intensity
        
    def interpolate_color(self, intensity):
        """
        Interpolate between calm and warning colors based on intensity.
        
        Args:
            intensity: Value between 0.0 (calm) and 1.0 (warning)
            
        Returns:
            Tuple of RGB values for the interpolated color
        """
        r = int(self.calm_color[0] + (self.warning_color[0] - self.calm_color[0]) * intensity)
        g = int(self.calm_color[1] + (self.warning_color[1] - self.calm_color[1]) * intensity)
        b = int(self.calm_color[2] + (self.warning_color[2] - self.calm_color[2]) * intensity)
        
        # Ensure values are in valid RGB range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return (r, g, b)
    
    def update_color_based_on_behavior(self):
        """Updates desktop color based on user switching behavior continuously"""
        try:
            # Get recent switches (last minute)
            recent_switches = self.switch_analyzer.read_recent_switches(minutes=1)
            
            # If no recent switches, just return
            if not recent_switches or len(recent_switches) < 2:
                return
            
            # Calculate average duration of recent app sessions
            recent_durations = [int(switch[4]) for switch in recent_switches if len(switch) > 4 and switch[4]]
            if not recent_durations:
                return
                
            recent_avg_duration = sum(recent_durations) / len(recent_durations)
            
            # Get historical statistics
            historical_stats = self.stats_storage.calculate_statistics()
            
            if historical_stats and 'mean' in historical_stats:
                historical_mean_duration = historical_stats['mean']
                
                # Calculate how intense the color should be
                intensity = self.calculate_color_intensity(recent_avg_duration, historical_mean_duration)
                
                # Interpolate between calm and warning colors
                color = self.interpolate_color(intensity)
                
                # Set the desktop color
                set_desktop_color(*color)
                
                print(f"Updated desktop color to {color} (intensity: {intensity:.2f})")
                print(f"Recent avg duration: {recent_avg_duration:.1f}s, Historical mean: {historical_mean_duration:.1f}s")
                
        except Exception as e:
            print(f"Error updating desktop color: {e}")

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