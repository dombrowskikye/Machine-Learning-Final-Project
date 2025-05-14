import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)
world = client.get_world()

# Get all vehicles and destroy those that aren't moving
vehicles = world.get_actors().filter("vehicle.*")
destroyed = 0

for vehicle in vehicles:
    velocity = vehicle.get_velocity()
    speed = (velocity.x**2 + velocity.y**2 + velocity.z**2) ** 0.5  # Calculate speed
    if speed < 0.1:  # Considered "stuck"
        vehicle.destroy()
        destroyed += 1

print(f"Destroyed {destroyed} non-moving NPC vehicles.")
