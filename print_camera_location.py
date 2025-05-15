# print_camera_location.py

import carla
import glob
import os
import sys
import time

# Add CARLA egg
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

def main():
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    try:
        spectator = world.get_spectator()

        print("Printing camera (spectator) coordinates. Press Ctrl+C to stop.\n")
        while True:
            transform = spectator.get_transform()
            loc = transform.location
            print(f"x={loc.x:.2f}, y={loc.y:.2f}, z={loc.z:.2f}")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
