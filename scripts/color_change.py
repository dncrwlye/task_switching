import subprocess
from PIL import Image
import tempfile
import os

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
        
        if ratio <=1:
            ratio = ratio ** 2
        if ratio > 1:
            ratio = ratio
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
        #so, as intensity increases, so will the color change. makes sense
        #as the ratio gets large, the intensity gets smaller, so you want a large ratio
        #essentially, you want the difference between the recent averages and the historical averages to be equivelent 
        #now, i think it's changing too fast, it is too sensitive 
        
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
            recent_switches = self.switch_analyzer.read_recent_switches(minutes=10)        
            # If no recent switches, just return
            if not recent_switches or len(recent_switches) < 2:
                return        
            # Calculate average duration of recent app sessions
            #recent_durations = [int(switch[4]) for switch in recent_switches if len(switch) > 4 and switch[4]]

            recent_durations = []
            for switch in recent_switches:
                if len(switch) > 4 and switch[4]:
                    recent_durations.append(int(switch[4]))
            if not recent_durations:
                return            
            recent_avg_duration_2 = sum(recent_durations) / len(recent_durations)      
            recent_avg_duration = 0
            total_weight = 0

            for i in (list(range(0,len(recent_durations)))):
                recent_avg_duration = recent_avg_duration + recent_durations[i] * (i+1) #weight by i + 1 (1 to 5, in practice)
                total_weight = total_weight + (1+i)
            
            recent_avg_duration = recent_avg_duration / total_weight if total_weight > 0 else 0
         
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
                print(f"Recent avg duration 2: {recent_avg_duration_2:.1f}s, Historical mean: {historical_mean_duration:.1f}s")

                #print(f("ratio:" {ratio}))
        except Exception as e:
            print(f"Error updating desktop color: {e}")

def set_desktop_color(r, g, b):
    """
    Set the desktop background to a solid color using r,g,b values (0-255)
    """
    # Create a small solid color image
    img_size = (100, 100)
    color_img = Image.new('RGB', img_size, color=(r, g, b))
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    color_img.save(temp_path)
    temp_file.close()
    
    # AppleScript to set the desktop picture
    applescript = f'''
    tell application "Finder"
        set desktop picture to POSIX file "{temp_path}"
    end tell
    '''
    
    # Execute the AppleScript
    result = subprocess.run(["osascript", "-e", applescript], 
                           capture_output=True, 
                           text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"Desktop background set to RGB: {r}, {g}, {b}")
    
    # Don't delete the file immediately as macOS needs it
    # You might want to store these files somewhere and clean them up later

# Example: Set to a specific color (red)
#set_desktop_color(255, 0, 0)
