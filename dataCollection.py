import numpy as np
import pandas as pdclear

import carla


#Testing to make sure the Carla API environemnt is set up correctly and working
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

world = client.get_world()
print(f"Connected to CARLA. Map: {world.get_map().name}")
