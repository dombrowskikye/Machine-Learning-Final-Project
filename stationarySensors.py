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

