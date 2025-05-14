# unsafe_radar_logger.py (continuous spawning version)

import carla
import csv
import time
import os
import numpy as np
import random
import sys
import traceback

# === Config ===
LABEL = 'unsafe'
OUTPUT_FILE = f'{LABEL}_radar_data.csv'
SPAWN_INTERVAL = 4  # Time between spawn attempts
MAX_ACTIVE_VEHICLES = 15  # Maximum number of vehicles active at once
RADAR_LOCATION = carla.Location(x=84, y=57, z=3)
RADAR_ROTATION = carla.Rotation(yaw=0)
SPAWN_LOCATION = carla.Location(x=148.38, y=57.09, z=2.5)
TOTAL_RUNTIME = 240  # Total runtime for the entire process
VEHICLE_CLEANUP_THRESHOLD = 100  # Distance threshold for removing vehicles that have gone too far

# === Setup ===
def setup_csv_writer(filename):
    try:
        if not os.path.exists('output'):
            os.makedirs('output')
        file_path = os.path.join('output', filename)
        print(f"Creating output file: {file_path}")
        file = open(file_path, 'w', newline='')
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'x', 'y', 'z', 'velocity', 'azimuth', 'sensor_id', 'vehicle_id', 'label'])
        print("CSV header written successfully")
        return file, writer
    except Exception as e:
        print(f"ERROR in setup_csv_writer: {e}")
        print(traceback.format_exc())
        raise

def setup_carla():
    try:
        print("Connecting to CARLA server...")
        client = carla.Client('localhost', 2000)
        client.set_timeout(20.0)  # Increased timeout
        print("Loading world...")
        world = client.load_world('Town01') 
        print("World loaded successfully")
        return client, world
    except Exception as e:
        print(f"ERROR in setup_carla: {e}")
        print(traceback.format_exc())
        raise

def set_spectator(world, transform):
    try:
        spectator = world.get_spectator()
        spectator.set_transform(transform)
        print("Spectator position set")
    except Exception as e:
        print(f"ERROR in set_spectator: {e}")
        print(traceback.format_exc())

def is_spawn_point_clear(spawn_point, vehicles, min_distance=8.0):
    for v in vehicles:
        try:
            if v.is_alive and v.get_transform().location.distance(spawn_point.location) < min_distance:
                return False
        except Exception as e:
            print(f"ERROR checking vehicle distance: {e}")
    return True

def create_radar_sensor(world, blueprint_library, transform, callback):
    try:
        print("Creating radar sensor...")
        radar_bp = blueprint_library.find('sensor.other.radar')
        radar_bp.set_attribute('horizontal_fov', '90')
        radar_bp.set_attribute('vertical_fov', '20')
        radar_bp.set_attribute('range', '30')
        radar = world.spawn_actor(radar_bp, transform)
        print(f"Radar spawned at {transform.location}")
        
        print("Setting up radar callback...")
        radar.listen(callback)
        print("Radar callback set up successfully")
        return radar
    except Exception as e:
        print(f"ERROR in create_radar_sensor: {e}")
        print(traceback.format_exc())
        raise

# Counter to track detection events
detection_count = 0

def save_radar_data(radar_data, sensor_id, radar_transform, vehicles_list, writer):
    global detection_count
    try:
        if not radar_data:
            return
            
        for detection in radar_data:
            try:
                x = detection.depth * np.cos(detection.azimuth)
                y = detection.depth * np.sin(detection.azimuth)
                z = detection.altitude
                velocity = detection.velocity
                azimuth = detection.azimuth
                radar_loc = radar_transform.location + carla.Location(x=x, y=y)

                match_found = False
                for vehicle in vehicles_list:
                    if not vehicle.is_alive:
                        continue
                        
                    if radar_loc.distance(vehicle.get_transform().location) < 6.0:
                        writer.writerow([time.time(), x, y, z, velocity, azimuth, sensor_id, vehicle.id, LABEL])
                        match_found = True
                        detection_count += 1
                        
                        # Print status update periodically
                        if detection_count % 10 == 0:
                            print(f"Radar detections recorded: {detection_count}")
                        break
            except Exception as e:
                print(f"ERROR processing individual detection: {e}")
                
    except Exception as e:
        print(f"ERROR in save_radar_data: {e}")
        print(traceback.format_exc())

def cleanup_distant_vehicles(vehicles_list, radar_location, threshold_distance):
    """Remove vehicles that have gone too far from the radar"""
    removed_count = 0
    remaining_vehicles = []
    
    for vehicle in vehicles_list:
        try:
            if not vehicle.is_alive:
                continue
                
            distance = vehicle.get_transform().location.distance(radar_location)
            if distance > threshold_distance:
                print(f"Removing vehicle {vehicle.id} (distance: {distance:.1f}m)")
                vehicle.destroy()
                removed_count += 1
            else:
                remaining_vehicles.append(vehicle)
        except Exception as e:
            print(f"Error checking vehicle {vehicle.id}: {e}")
    
    if removed_count > 0:
        print(f"Removed {removed_count} distant vehicles")
    
    return remaining_vehicles

def main():
    vehicles_list = []
    csv_file = None
    radar_sensor = None
    
    try:
        print("\n=== Starting CARLA Radar Logger (Continuous Spawning) ===")
        global_start_time = time.time()
        
        # Setup CSV writer
        print("\n[1/4] Setting up CSV writer...")
        csv_file, csv_writer = setup_csv_writer(OUTPUT_FILE)
        
        # Setup CARLA
        print("\n[2/4] Connecting to CARLA and setting up world...")
        client, world = setup_carla()
        blueprint_library = world.get_blueprint_library()
        
        # Set up radar transform and spectator
        print("\n[3/4] Setting up radar position...")
        radar_transform = carla.Transform(RADAR_LOCATION, RADAR_ROTATION)
        set_spectator(world, radar_transform)
        
        # Create radar sensor BEFORE spawning vehicles
        print("\n[4/4] Setting up radar sensor...")
        radar_sensor = create_radar_sensor(
            world, blueprint_library, radar_transform,
            lambda data: save_radar_data(data, 'radar_1', radar_transform, vehicles_list, csv_writer)
        )
        radar_start_time = time.time()
        
        
        # Setup traffic manager with more aggressive settings
        tm = client.get_trafficmanager()
        tm.set_global_distance_to_leading_vehicle(0.5)  # Closer following distance
        tm.set_synchronous_mode(False)  # Use asynchronous mode
        
        try:
            spawn_point = world.get_map().get_waypoint(SPAWN_LOCATION, project_to_road=True).transform
            print(f"Spawn point successfully mapped to road at {spawn_point.location}")
        except Exception as e:
            print(f"ERROR mapping spawn point to road: {e}")
            print("Using raw spawn location instead")
            spawn_point = carla.Transform(SPAWN_LOCATION, carla.Rotation())
            
        # Start the main loop for the entire process duration
        print(f"\n=== Starting main loop (continuous spawning for {TOTAL_RUNTIME} seconds) ===")
        
        main_start_time = time.time()
        last_vehicle_spawn_time = main_start_time
        last_cleanup_time = main_start_time
        last_flush_time = main_start_time
        detection_checkpoint = 0
        vehicle_bps = blueprint_library.filter('vehicle.*')
        spawned_count = 0
        
        # Main loop - runs for TOTAL_RUNTIME seconds
        while time.time() - radar_start_time < TOTAL_RUNTIME:
            current_time = time.time()
            elapsed = int(current_time - radar_start_time)
            
            # Attempt to spawn a new vehicle if we're under MAX_ACTIVE_VEHICLES
            if len(vehicles_list) < MAX_ACTIVE_VEHICLES and current_time - last_vehicle_spawn_time >= SPAWN_INTERVAL:
                try:
                    if is_spawn_point_clear(spawn_point, vehicles_list):
                        bp = random.choice(vehicle_bps)
                        vehicle = world.try_spawn_actor(bp, spawn_point)
                        if vehicle:
                            # Configure the vehicle with aggressive settings
                            vehicle.set_autopilot(True, tm.get_port())
                            tm.ignore_lights_percentage(vehicle, 0)
                            tm.ignore_signs_percentage(vehicle, 100)
                            tm.vehicle_percentage_speed_difference(vehicle, -40)  # Faster than normal
                            tm.distance_to_leading_vehicle(vehicle, 0.5)
                            tm.auto_lane_change(vehicle, True)

                            vehicles_list.append(vehicle)
                            spawned_count += 1
                            print(f"Spawned UNSAFE vehicle #{spawned_count} (active: {len(vehicles_list)}/{MAX_ACTIVE_VEHICLES})")
                        else:
                            print("Spawn failed — retrying next interval")
                    else:
                        print("Spawn point blocked — waiting for next interval")
                except Exception as e:
                    print(f"ERROR during vehicle spawning: {e}")
                    
                last_vehicle_spawn_time = current_time
            
            # Clean up vehicles that have gone too far from the radar (every 10 seconds)
            if current_time - last_cleanup_time >= 10:
                print("\n--- Performing vehicle cleanup check ---")
                vehicles_list = cleanup_distant_vehicles(vehicles_list, RADAR_LOCATION, VEHICLE_CLEANUP_THRESHOLD)
                last_cleanup_time = current_time
                
            # Status update every 10 seconds
            if elapsed % 10 == 0 and elapsed > 0:
                new_detections = detection_count - detection_checkpoint
                print(f"Progress: {elapsed}/{TOTAL_RUNTIME}s. " +
                      f"Active vehicles: {len(vehicles_list)}/{MAX_ACTIVE_VEHICLES}. " +
                      f"Total spawned: {spawned_count}. " +
                      f"New detections: {new_detections} in last 10s. " +
                      f"Total: {detection_count}")
                detection_checkpoint = detection_count
            
            # Flush output file periodically
            if current_time - last_flush_time > 5.0:
                csv_file.flush()
                last_flush_time = current_time
                
            time.sleep(0.1)  # Small sleep to prevent CPU overuse
            
        # Final data status
        total_elapsed = time.time() - global_start_time
        print(f"\nData collection complete in {total_elapsed:.1f} seconds.")
        print(f"Total vehicles spawned: {spawned_count}")
        print(f"Total radar detections: {detection_count}")
            
    except KeyboardInterrupt:
        print("\nData collection interrupted by user")
    except Exception as e:
        print(f"\nCRITICAL ERROR in main: {e}")
        print(traceback.format_exc())
    finally:
        print("\n=== Cleaning up resources ===")
        
        # Clean up radar
        if radar_sensor:
            try:
                print("Stopping and destroying radar sensor...")
                radar_sensor.stop()
                radar_sensor.destroy()
                print("Radar sensor destroyed")
            except Exception as e:
                print(f"Error destroying radar sensor: {e}")
        
        # Clean up vehicles
        if vehicles_list:
            try:
                print(f"Destroying {len(vehicles_list)} vehicles...")
                alive_count = 0
                for v in vehicles_list:
                    try:
                        if v.is_alive:
                            alive_count += 1
                            v.destroy()
                    except:
                        pass
                print(f"Destroyed {alive_count} active vehicles")
            except Exception as e:
                print(f"Error destroying vehicles: {e}")
        
        # Close CSV file
        if csv_file:
            try:
                print("Closing output file...")
                csv_file.flush()  # Ensure all data is written
                csv_file.close()
                print(f"Output file closed")
                
                # Verify file was created and has data
                file_path = os.path.join('output', OUTPUT_FILE)
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"Output file size: {size} bytes")
                    if size > 100:  # Assuming at least a header and some data
                        print(f"[DONE] Data saved to output/{OUTPUT_FILE}")
                    else:
                        print(f"[WARNING] Output file exists but may be empty or contain only headers")
                else:
                    print(f"[ERROR] Output file was not created at {file_path}")
            except Exception as e:
                print(f"Error closing CSV file: {e}")

if __name__ == '__main__':
    main()