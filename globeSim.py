import os
import math
import time
import sys

# Platform-specific non-blocking key press detection
try:
    # For Unix-like systems (Linux, macOS)
    import tty
    import termios

    def getch():
        """Gets a single character from standard input without blocking."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

except ImportError:
    # For Windows
    import msvcrt

    def getch():
        """Gets a single character from standard input without blocking."""
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
        return None

# --- Phase 1: Setup and Data Loading ---

# Constants
SCREEN_WIDTH = 120  # Characters
SCREEN_HEIGHT = 40  # Characters
GLOBE_RADIUS = 0.9  # Relative to the screen height
MAP_FILENAME = "world_map.txt"
ROTATION_SPEED = 0.1

# State Variables
rotation_angle_y = 0.0  # Corresponds to longitude (left/right spin)
rotation_angle_x = 0.0  # Corresponds to latitude (up/down tilt)

def load_map_data(filename):
    """Loads the ASCII map from a text file into a 2D list."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [list(line.strip('\n')) for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: Map file '{filename}' not found.")
        print("Please make sure it's in the same directory as the script.")
        sys.exit(1)

def main():
    """Main function to run the interactive globe."""
    global rotation_angle_y, rotation_angle_x

    # Load the map
    earth_map = load_map_data(MAP_FILENAME)
    map_height = len(earth_map)
    map_width = len(earth_map[0])

    # --- Phase 2: The Rendering Engine (The Core Loop) ---
    print("Globe loaded. Use A/D to spin, W/S to tilt. Press 'q' to quit.")
    time.sleep(2)

    while True:
        # 2.1: Start the main loop
        # 2.3: Create an output buffer
        output_buffer = [[' ' for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]

        # Pre-calculate sines and cosines for the current rotation angles
        sin_y = math.sin(rotation_angle_y)
        cos_y = math.cos(rotation_angle_y)
        sin_x = math.sin(rotation_angle_x)
        cos_x = math.cos(rotation_angle_x)

        # 2.4: Iterate through each screen pixel (character cell)
        for j in range(SCREEN_HEIGHT):
            for i in range(SCREEN_WIDTH):
                # Normalize coordinates to a -1 to 1 range, accounting for character aspect ratio
                x_norm = (2 * i / SCREEN_WIDTH - 1) * (SCREEN_WIDTH / SCREEN_HEIGHT) * 0.5
                y_norm = 2 * j / SCREEN_HEIGHT - 1

                # 2.5: Project from 2D screen to 3D globe
                if x_norm**2 + y_norm**2 < GLOBE_RADIUS**2:
                    z_norm = math.sqrt(GLOBE_RADIUS**2 - x_norm**2 - y_norm**2)
                    
                    # 3D point on the surface of the sphere
                    x3d, y3d, z3d = x_norm, y_norm, z_norm

                    # 2.6: Apply inverse rotation
                    # Rotate around X-axis (tilt)
                    x_rot_x = x3d
                    y_rot_x = y3d * cos_x - z3d * sin_x
                    z_rot_x = y3d * sin_x + z3d * cos_x
                    
                    # Rotate around Y-axis (spin)
                    x_rot_y = x_rot_x * cos_y + z_rot_x * sin_y
                    y_rot_y = y_rot_x
                    z_rot_y = -x_rot_x * sin_y + z_rot_x * cos_y

                    # 2.7: Convert 3D point to 2D map coordinates (spherical to equirectangular)
                    # Latitude (from -PI/2 to PI/2)
                    lat = math.asin(y_rot_y / GLOBE_RADIUS)
                    # Longitude (from -PI to PI)
                    lon = math.atan2(x_rot_y, z_rot_y)

                    # Scale lat/lon to map dimensions
                    map_x = int((lon + math.pi) / (2 * math.pi) * map_width) % map_width
                    map_y = int((lat + math.pi / 2) / math.pi * map_height)
                    map_y = max(0, min(map_height - 1, map_y)) # Clamp to valid range

                    # 2.8: Populate the buffer
                    output_buffer[j][i] = earth_map[map_y][map_x]

        # 2.2 & 2.9: Render the frame without flicker
        # Add instructions to the buffer before printing
        instructions = " A/D: Spin | W/S: Tilt | Q: Quit "
        start_pos = (SCREEN_WIDTH - len(instructions)) // 2
        for idx, char in enumerate(instructions):
            if 0 <= start_pos + idx < SCREEN_WIDTH:
                 output_buffer[SCREEN_HEIGHT-1][start_pos + idx] = char

        # Combine buffer into a single string
        frame = "\n".join("".join(row) for row in output_buffer)

        # Use ANSI escape code '\033[H' to move cursor to top-left.
        # This overwrites the old frame instead of clearing the screen,
        # preventing the jittery/phasing effect.
        sys.stdout.write('\033[H' + frame)
        sys.stdout.flush()


        # --- Phase 3: Handling User Interaction ---
        key = getch()
        if key:
            if key == 'd':
                rotation_angle_y += ROTATION_SPEED
            elif key == 'a':
                rotation_angle_y -= ROTATION_SPEED
            elif key == 'w':
                rotation_angle_x -= ROTATION_SPEED
            elif key == 's':
                rotation_angle_x += ROTATION_SPEED
            elif key == 'q':
                break
        
        # Clamp vertical rotation to avoid flipping over
        rotation_angle_x = max(-math.pi/2, min(math.pi/2, rotation_angle_x))

        # 3.3: Control refresh rate
        time.sleep(0.01)

if __name__ == "__main__":
    main()

