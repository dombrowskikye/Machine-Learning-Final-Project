import carla
import time

# Connect to CARLA
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

# Load Town01 explicitly
world = client.load_world('Town01')
blueprint_library = world.get_blueprint_library()

# === Move spectator to the desired location ===
spectator = world.get_spectator()
sensor_location = carla.Location(x=100, y=50, z=10)
sensor_rotation = carla.Rotation(pitch=-15, yaw=180, roll=0)
spectator.set_transform(carla.Transform(sensor_location, sensor_rotation))

print("Loaded Town01. Spectator moved to x=100, y=50, z=10 and now tracking...")

try:
    while True:
        transform = spectator.get_transform()
        loc = transform.location
        rot = transform.rotation

        print(f"Location: x={loc.x:.2f}, y={loc.y:.2f}, z={loc.z:.2f} | "
              f"Rotation: pitch={rot.pitch:.2f}, yaw={rot.yaw:.2f}, roll={rot.roll:.2f}")
        
        time.sleep(0.5)  # update every half second
except KeyboardInterrupt:
    print("Stopped tracking.")
