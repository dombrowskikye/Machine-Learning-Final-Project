import carla
import random

# === Connect to CARLA ===
client = carla.Client('localhost', 2000)
client.set_timeout(5.0)
world = client.get_world()
blueprints = world.get_blueprint_library()

# === Choose a reliable small vehicle blueprint ===
vehicle_bp = random.choice([
    blueprints.find('vehicle.mini.cooper_s'),
    blueprints.find('vehicle.audi.tt'),
    blueprints.find('vehicle.carlamotors.carlacola')
])

# === Get road height from the map ===
map = world.get_map()
xy_loc = carla.Location(x=116.15, y=55.54)
waypoint = map.get_waypoint(xy_loc, project_to_road=True)
spawn_z = waypoint.transform.location.z

# === Define transform and spawn ===
spawn_transform = carla.Transform(
    location=carla.Location(x=116.15, y=55.54, z=spawn_z + 0.1),
    rotation=carla.Rotation(yaw=random.uniform(0, 360))
)

# === Try spawning ===
vehicle = world.try_spawn_actor(vehicle_bp, spawn_transform)

if vehicle:
    vehicle.set_autopilot(False)  # Make sure it's stationary
    print(f"[+] Spawned stationary vehicle ({vehicle_bp.id}) at {spawn_transform.location}")
else:
    print("[!] Failed to spawn vehicle — possibly due to collision at location.")
