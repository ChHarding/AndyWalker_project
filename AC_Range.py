import Myfuncs
import re
import itertools
import time
import ast
from collections import defaultdict
from functools import reduce
from operator import or_

# Defaults
default_live = False 
default_lr = "10"
default_latitude = 50.827276295494734 #Assumes you don't just measure your location
default_longitude = 0.2060202678627942 #Assumes you don't just measure your location
default_altitude = 50.00 #Assumes you don't just measure your location

if ((input(f"Enter Live Data (True/False) [{default_live}]: ").strip() or default_live) == "True"):
#Get data from the ADS-B API
    limit_range = input(f"Enter Range to Limit Data [{default_lr}]: ").strip() or default_lr
    try:
        latitude, longitude, altitude, units = Myfuncs.read_gps_coordinates("COM6")
    except KeyboardInterrupt:
        print("Stopped reading GPS.")
    except Exception as exc:
        latitude = default_latitude
        longitude=default_longitude
        altitude=default_altitude
    r = Myfuncs.call_api(str(latitude), str(longitude), altitude, limit_range)

else:
#Just use canned data from an old file
    with open(r"./Data/data.txt", "r", encoding="utf-8") as f:
        r_str = f.read()
        r = ast.literal_eval(r_str)
        # Ask for input and offer the fallback option
        latitude = input(f"Enter sensor latitude [{default_latitude}]: ").strip() or default_latitude
        longitude = input(f"Enter sensor longitude [{default_longitude}]: ").strip() or default_longitude
        altitude = input(f"Enter sensor altitude [{default_altitude}]: ").strip() or default_altitude

r_list = r["ac"] #Extract the list of aircraft from the API response

keys_to_keep = {"lat", "lon", "alt_geom", "flight"} #Only keep the keys we need for plotting and range calculations
filtered_r = [{k: v for k, v in d.items() if k in keys_to_keep} for d in r_list]
really_filtered_r = [
    d for d in filtered_r #Only keep entries that have the "alt_geom" key, since we need altitude for range calculations
    if "alt_geom" in d
    ]
r_list = really_filtered_r #Update r_list to only include the filtered entries

with open(r"./Data/output.txt", "w") as g:
    print(r_list, file=g) #Write the filtered list of aircraft to a file for debugging purposes

range_0 = Myfuncs.calculate_radar_range(rcs_sqm=1)
range_10 = Myfuncs.calculate_radar_range(rcs_sqm=10)
range_20 = Myfuncs.calculate_radar_range(rcs_sqm=100)
range_30 = Myfuncs.calculate_radar_range(rcs_sqm=1000)

my_map = Myfuncs.plot_map (latitude, longitude, range_10, range_20, range_30)

slant_range = []
terrain_masking = []

# Print header row
print(f"{'Degrees (Az)':<15} {'Degrees (El)':<15} {'Slant Range (km)':<20} {'Masked?':<14} {'Received Time (ms)':<15}")
print("-" * 88)

for i in range(len(r_list)):
    
    radar = (latitude, longitude)
    plane = (r_list[i]["lat"], r_list[i]["lon"])
    
    radar += ((altitude),)
    plane += ((r_list[i]["alt_geom"] * 0.3048),)
    
    slant_range.append(Myfuncs.calculate_slant_range(radar, plane))
    terrain_masking.append(Myfuncs.get_masking(radar, plane, 5))
    
    print(f"{(str(round(slant_range[i][0], 3))):<15} {(str(round(slant_range[i][1], 3))):<7} \
        {(str(round(slant_range[i][2] / 1000, 2))):<20} {(str(reduce(or_, terrain_masking[i]))):<6} \
        {(time.time_ns() // 1_000_000):<15} ")

    if (reduce(or_, terrain_masking[i])):
        Myfuncs.plot_plane (radar[0:2], plane[0:2], my_map, r_list[i], "red")
    else:
        Myfuncs.plot_plane (radar[0:2], plane[0:2], my_map, r_list[i], "blue")

