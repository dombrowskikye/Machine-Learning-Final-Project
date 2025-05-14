# safe_radar_logger.py (collect 120s of actual detection time with logging)

import carla
import csv
import time
import os
import numpy as np
import random
import sys
import traceback

# === Config ===
LABEL = 'safe'
OUTPUT_FILE = f'{LABEL}_radar_data.csv'
SPAWN_INTERVAL = 4
MAX_ACTIVE_VEHICLES = 15
RADAR_LOCATION = carla.Location(x=84, y=57, z=3)
RADAR_ROTATION = carla.Rotation(yaw=0)
SPAWN_LOCATION = carla.Location(x=148.38, y=57.09, z=2.5)
TOTAL_RUNTIME = 120
VEHICLE_CLEANUP_THRESHOLD = 100

# === Global State ===
detection_count = 0
first_detection_time = None

# === Setup ===
def setup_csv_writer(filename):
    if not os.path.exists('output'):
        os.makedirs('output')
    path = os.path.join('output', filename)
    f = open(path, 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'x', 'y', 'z', 'velocity', 'azimuth', 'sensor_id', 'vehicle_id', 'label'])
    print(f"[SETUP] CSV file created at {path}")
    return f, writer

def setup_carla():
    print("[SETUP] Connecting to CARLA...")
    client = carla.Client('localhost', 2000)
    client.set_timeout(20.0)
    world = client.load_world('Town01')
    print("[SETUP] CARLA world loaded")
    return client, world

def set_spectator(world, transform):
    world.get_spectator().set_transform(transform)
    print("[SETUP] Spectator positioned")

def is_spawn_point_clear(spawn_point, vehicles, min_distance=8.0):
    for v in vehicles:
        if v.is_alive and v.get_transform().location.distance(spawn_point.location) < min_distance:
            return False
    return True

def create_radar_sensor(world, blueprint_library, transform, callback):
    radar_bp = blueprint_library.find('sensor.other.radar')
    radar_bp.set_attribute('horizontal_fov', '90')
    radar_bp.set_attribute('vertical_fov', '20')
    radar_bp.set_attribute('range', '30')
    radar = world.spawn_actor(radar_bp, transform)
    radar.listen(callback)
    print("[SETUP] Radar sensor created and listening")
    return radar

def save_radar_data(radar_data, sensor_id, radar_transform, vehicles_list, writer):
    global detection_count, first_detection_time
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

            for vehicle in vehicles_list:
                if not vehicle.is_alive:
                    continue
                if radar_loc.distance(vehicle.get_transform().location) < 6.0:
                    writer.writerow([time.time(), x, y, z, velocity, azimuth, sensor_id, vehicle.id, LABEL])
                    detection_count += 1
                    if first_detection_time is None:
                        first_detection_time = time.time()
                        print("[INFO] First detection timestamp recorded")
                    if detection_count % 10 == 0:
                        print(f"[INFO] Radar detections recorded: {detection_count}")
                    break
        except Exception as e:
            print(f"[ERROR] Processing detection: {e}")

def cleanup_distant_vehicles(vehicles_list, radar_location, threshold):
    remaining = []
    removed = 0
    for v in vehicles_list:
        try:
            if not v.is_alive:
                continue
            if v.get_transform().location.distance(radar_location) > threshold:
                print(f"[CLEANUP] Removing vehicle {v.id}")
                v.destroy()
                removed += 1
            else:
                remaining.append(v)
        except:
            pass
    if removed:
        print(f"[CLEANUP] Removed {removed} vehicles beyond {threshold}m")
    return remaining

def main():
    global first_detection_time
    vehicles_list = []
    csv_file, radar_sensor = None, None
    try:
        print("\n=== Starting CARLA Radar Logger ===")
        csv_file, csv_writer = setup_csv_writer(OUTPUT_FILE)
        client, world = setup_carla()
        blueprint_library = world.get_blueprint_library()
        radar_transform = carla.Transform(RADAR_LOCATION, RADAR_ROTATION)
        set_spectator(world, radar_transform)

        radar_sensor = create_radar_sensor(
            world, blueprint_library, radar_transform,
            lambda data: save_radar_data(data, 'radar_1', radar_transform, vehicles_list, csv_writer)
        )

        tm = client.get_trafficmanager()
        tm.set_global_distance_to_leading_vehicle(0.5)
        tm.set_synchronous_mode(False)

        spawn_point = world.get_map().get_waypoint(SPAWN_LOCATION, project_to_road=True).transform

        print("\n=== Entering main loop ===")
        main_start_time = time.time()
        last_spawn = main_start_time
        last_cleanup = main_start_time
        last_flush = main_start_time
        spawned_count = 0
        vehicle_bps = blueprint_library.filter('vehicle.*')

        while True:
            now = time.time()
            if first_detection_time and now - first_detection_time >= TOTAL_RUNTIME:
                break

            if len(vehicles_list) < MAX_ACTIVE_VEHICLES and now - last_spawn >= SPAWN_INTERVAL:
                if is_spawn_point_clear(spawn_point, vehicles_list):
                    bp = random.choice(vehicle_bps)
                    vehicle = world.try_spawn_actor(bp, spawn_point)
                    if vehicle:
                        vehicle.set_autopilot(True, tm.get_port())
                        vehicles_list.append(vehicle)
                        spawned_count += 1
                        print(f"[SPAWN] SAFE vehicle #{spawned_count} (active: {len(vehicles_list)})")
                last_spawn = now

            if now - last_cleanup >= 10:
                vehicles_list = cleanup_distant_vehicles(vehicles_list, RADAR_LOCATION, VEHICLE_CLEANUP_THRESHOLD)
                last_cleanup = now

            if now - last_flush >= 5:
                csv_file.flush()
                last_flush = now

            if first_detection_time:
                elapsed = int(now - first_detection_time)
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f"[PROGRESS] Elapsed: {elapsed}/{TOTAL_RUNTIME}s | Active vehicles: {len(vehicles_list)} | Total spawned: {spawned_count} | Total detections: {detection_count}")

            time.sleep(0.1)

        print(f"\n[INFO] Data collection complete: {detection_count} detections in {TOTAL_RUNTIME}s.")

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] User terminated the script.")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        print(traceback.format_exc())
    finally:
        print("\n=== Cleaning up resources ===")
        if radar_sensor:
            radar_sensor.stop()
            radar_sensor.destroy()
            print("[CLEANUP] Radar sensor destroyed")
        for v in vehicles_list:
            try:
                if v.is_alive:
                    v.destroy()
            except:
                pass
        if csv_file:
            csv_file.flush()
            csv_file.close()
            print("[CLEANUP] Output file closed")
        print(f"[DONE] Data saved to output/{OUTPUT_FILE}")

if __name__ == '__main__':
    main()
