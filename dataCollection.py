import numpy as np
import pandas as pd
import random 
import csv
import time

#Improting Carla for simulation and data collection of vehicles.
import carla


#Creating the client and world to connect to Carla 
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
#Gets current world running in Carla
world = client.load_world('Town01')
blueprint_library = world.get_blueprint_library()

#Creating CSV file for data collection from LIDAR AND RADAR sensors
csv_file = open('sensor_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'sensor_type', 'x', 'y', 'z', 'velocity'])


#Confirming that the world and client has connected to Carla successfully
print(f"Connected to CARLA. Map: {world.get_map().name}")

#Get list of spawn points
spawn_points = world.get_map().get_spawn_points()

# Tester vehicle blueprint
test_vehicle_bp = blueprint_library.filter('model3')[0]

# Spawning a vehicle in the environemnt to attach sensors
for spawn_point in spawn_points:
    try: 
        location_point = spawn_point
        test_vehicle = world.spawn_actor(test_vehicle_bp, location_point)
        break
    except RuntimeError:
        continue

# Adding traffic to the simulation 
traffic_manager = client.get_trafficmanager()
spawn_points = world.get_map().get_spawn_points()
vehicles_list = []
for i in range(15):
    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
    for spawn_point in spawn_points:
        try: 
            vehicle = world.spawn_actor(vehicle_bp, spawn_point)
            vehicle.set_autopilot(True, traffic_manager.get_port())
            traffic_manager.auto_lane_change(vehicle, True)
            traffic_manager.set_hybrid_physics_mode(True)
            traffic_manager.vehicle_percentage_speed_difference(vehicle, 50)
            vehicles_list.append(vehicle)
            break
        except RuntimeError:
            continue

#Ensuring that there are actually vehicles running in the simulation
print("The vehicles are: ", vehicles_list)
    
    

# Saving data function
def save_data(sensor_type, sensor_data):
    #Filter if the data is not an actual dirver in the simulation (for example, just a tree). 
    for data in sensor_data:
        if sensor_type == 'RADAR':
            csv_writer.writerow([time.time(), sensor_type, data.depth, data.azimuth, data.altitude, data.velocity])
        elif sensor_type == 'LIDAR':
            csv_writer.writerow([time.time(), sensor_type, data.point.x, data.point.y, data.point.z, None])


# Create the LIDAR sensors and start data collecting
lidar_blueprint = blueprint_library.find('sensor.lidar.ray_cast')
lidar_transform = carla.Transform(carla.Location(z=2.5))
lidar_sensor = world.spawn_actor(lidar_blueprint, lidar_transform, attach_to=test_vehicle)
lidar_sensor.listen(lambda data: save_data('LIDAR', data))

#Create the RADAR sensors and start collecting data
radar_blueprint = blueprint_library.find('sensor.other.radar')
radar_transform = carla.Transform(carla.Location(z=2.5))
radar_sensor = world.spawn_actor(radar_blueprint, radar_transform, attach_to=test_vehicle)
radar_sensor.listen(lambda data: save_data('RADAR', data))


# AUtomatically stopping the simulation after a set time
start_time = time.time()

try:
    while True:
        time_running = time.time() - start_time
        if time_running > 60:  # Stop after 60 seconds
            break
        time.sleep(1)
        
finally: 
    # Stop the sensors and vehicles
    lidar_sensor.stop()
    radar_sensor.stop()
    test_vehicle.destroy()
    for vehicle in vehicles_list:
        vehicle.destroy()
    
    csv_file.close()



