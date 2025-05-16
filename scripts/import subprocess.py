import subprocess
import random

def set_desktop_color(r, g, b):
    """
    Set the desktop background to a solid color using r,g,b values (0-255)
    """
    # Convert RGB to macOS hex format
    color_hex = f"{r/255} {g/255} {b/255}"
    
    # AppleScript to change the desktop background color
    applescript = f'''
    tell application "System Events"
        tell every desktop
            set picture to {{r:{r/255}, g:{g/255}, b:{b/255}}}
        end tell
    end tell
    '''
    
    # Execute the AppleScript
    subprocess.run(["osascript", "-e", applescript])
    print(f"Desktop background set to RGB: {r}, {g}, {b}")

# Example: Set to a specific color (red)
set_desktop_color(255, 0, 0)

# Example: Set to a random color
# r = random.randint(0, 255)
# g = random.randint(0, 255)
# b = random.randint(0, 255)
# set_desktop_color(r, g, b)