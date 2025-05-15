import carla

# === Connect to CARLA ===
client = carla.Client('localhost', 2000)
client.set_timeout(5.0)
world = client.get_world()

# === Get all actors in the world ===
all_actors = world.get_actors()

# === Filter only traffic cones ===
cones = [actor for actor in all_actors if 'trafficcone' in actor.type_id]

# === Destroy each cone ===
for cone in cones:
    print(f"[-] Destroying cone at {cone.get_location()}")
    cone.destroy()

print(f"[✓] Cleared {len(cones)} traffic cones.")
