#!/usr/bin/env python3
import subprocess
import argparse

def get_current_mouse_speed():
    """Get the current mouse tracking speed setting."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "com.apple.mouse.scaling"],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except subprocess.CalledProcessError:
        return "Unable to get current mouse speed"

def set_mouse_speed(speed):
    """Set the mouse tracking speed (0.0 to 3.0 is the typical range)."""
    try:
        subprocess.run(
            ["defaults", "write", "-g", "com.apple.mouse.scaling", "-float", str(speed)],
            check=True
        )
        # For changes to take effect immediately, restart the CoreGraphics server
        subprocess.run(
            ["killall", "-HUP", "SystemUIServer"],
            check=True
        )
        return f"Mouse speed set to {speed}"
    except subprocess.CalledProcessError as e:
        return f"Error setting mouse speed: {e}"

def main():
    parser = argparse.ArgumentParser(description="Control mouse cursor speed on macOS")
    parser.add_argument(
        "--get", 
        action="store_true", 
        help="Get the current mouse speed"
    )
    parser.add_argument(
        "--set", 
        type=float, 
        help="Set the mouse speed (recommended range: 0.0-3.0)"
    )
    
    args = parser.parse_args()
    
    if args.get:
        current_speed = get_current_mouse_speed()
        print(f"Current mouse speed: {current_speed}")
    elif args.set is not None:
        if args.set < 0:
            print("Warning: Negative values may have unexpected effects")
        elif args.set > 5:
            print("Warning: Values above 3.0 may make the cursor difficult to control")
        
        result = set_mouse_speed(args.set)
        print(result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()