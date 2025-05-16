import subprocess
from PIL import Image
import tempfile
import os

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
