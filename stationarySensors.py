import numpy as np
import pandas as pd
import random 
import csv
import time
import os

#Improting Carla for simulation and data collection of vehicles.
import carla


#Creating the directory to store camera pictures
if not os.path.exists('camera_images'):
    os.makedirs('camera_images')

#Creating the client and world to connect to Carla 
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
#Gets current world running in Carla
world = client.load_world('Town01')
blueprint_library = world.get_blueprint_library()
vehicles_list = []

#Moving the cursor to the sensor and camnera location
spectator = world.get_spectator()
sensor_location = carla.Location(x=100, y=50, z=10)
sensor_rotation = carla.Rotation(pitch=-15, yaw=180, roll=0)
spectator.set_transform(carla.Transform(sensor_location, sensor_rotation))

#Creating a picture image of the passing vehicles with timestamp and frame
def save_image(image):
    image.save_to_disk('camera_images/%06d.png' % image.frame, carla.ColorConverter.Raw)
    print(f"Image saved: {image.frame}")

#Creating CSV file for data collection from LIDAR AND RADAR sensors
csv_file = open('sensor_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Timestamp', 'sensor_type', 'x', 'y', 'z', 'velocity'])


# Saving data function
def save_data(sensor_type, sensor_data):
    vehicle_positions = [v.get_location() for v in vehicles_list]
    #Filter if the data is not an actual dirver in the simulation (for example, just a tree). 
    if sensor_type == 'RADAR':
        for data in sensor_data:
            #get the radar location
            x = data.depth * np.cos(data.azimuth)
            y = data.depth * np.sin(data.azimuth)
            radar_location = carla.Location(x=radar_transform.location.x + x, y=radar_transform.location.y +y, z=radar_transform.location.z)
            #check if the vehicle is near the detection location
            for vehicle in vehicle_positions:
                if radar_location.distance(vehicle) < 3:
                    csv_writer.writerow([time.time(), sensor_type, data.depth, data.azimuth, data.altitude, data.velocity])
                    break
    
    elif sensor_type == 'LIDAR':
        for data in sensor_data:
            #get the lidar location
            lidar_location = lidar_transform.transform(data.point)
            #check if the vehicle is near the detection location
            for vehicle in vehicle_positions:
                if lidar_location.distance(vehicle) < 2:
                    csv_writer.writerow([time.time(), sensor_type, data.point.x, data.point.y, data.point.z, None])
                    break
            


# Create the LIDAR sensors and start data collecting
lidar_blueprint = blueprint_library.find('sensor.lidar.ray_cast')
lidar_transform = carla.Transform(carla.Location(x=100, y=50, z=3))
lidar_sensor = world.spawn_actor(lidar_blueprint, lidar_transform)
lidar_sensor.listen(lambda data: save_data('LIDAR', data))

#Create the RADAR sensors and start collecting data
radar_blueprint = blueprint_library.find('sensor.other.radar')
radar_transform = carla.Transform(carla.Location(x=100, y=50, z=3))
radar_sensor = world.spawn_actor(radar_blueprint, radar_transform)
radar_sensor.listen(lambda data: save_data('RADAR', data))

#Creating the RGB camera to take pictures of the vehicles in the simulation
camera_blueprint = blueprint_library.find('sensor.camera.rgb')  
camera_blueprint.set_attribute('image_size_x', '800')
camera_blueprint.set_attribute('image_size_y', '600')
camera_blueprint.set_attribute('fov', '90')
camera_transform = carla.Transform(carla.Location(x=100, y=50, z=3))
camera_sensor = world.spawn_actor(camera_blueprint, camera_transform)
camera_sensor.listen(lambda image: save_image(image))

#Spawning multiple vehciles (5 vehicles)
tm = client.get_trafficmanager()

for i in range(20):
    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
    spawn_loc = carla.Location(x=148.38, y=57.09, z=2.5)
    spawn_rot = carla.Rotation(yaw=-177.5)  # Facing camera
    vehicle_transform = carla.Transform(spawn_loc, spawn_rot)
    try: 
        vehicle = world.spawn_actor(vehicle_bp, vehicle_transform)
        vehicle.set_autopilot(True, tm.get_port())
        vehicles_list.append(vehicle)
        time.sleep(15)
    except RuntimeError:
        continue

# AUtomatically stopping the simulation after a set time
start_time = time.time()

try:
    while True:
        time_running = time.time() - start_time
        if time_running > 120:  # Stop after 120 seconds
            break
        time.sleep(10)
        
finally: 
    # Stop the sensors and vehicles
    lidar_sensor.stop()
    radar_sensor.stop()
    for vehicle in vehicles_list:
        vehicle.destroy()
    
    csv_file.close()
