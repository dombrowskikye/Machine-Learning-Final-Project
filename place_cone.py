import carla
import random

# === Connect to CARLA ===
client = carla.Client('localhost', 2000)
client.set_timeout(5.0)
world = client.get_world()

# === Get the blueprint for a traffic cone ===
blueprint_library = world.get_blueprint_library()
cone_bp = blueprint_library.find('static.prop.trafficcone01')

# === Define the spawn transform ===
spawn_location = carla.Location(x=116.15, y=55.54, z=0)
spawn_rotation = carla.Rotation(yaw=random.uniform(0, 360))
spawn_transform = carla.Transform(spawn_location, spawn_rotation)

# === Try to spawn the cone ===
cone_actor = world.try_spawn_actor(cone_bp, spawn_transform)

if cone_actor is None:
    print("[!] Failed to spawn traffic cone. Possible collision or bad spawn location.")
else:
    print(f"[+] Successfully spawned traffic cone at {spawn_location}")
