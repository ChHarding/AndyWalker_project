import Myfuncs
import re
import itertools
from collections import defaultdict

Live = True

if Live:
#Get data from the ADS-B API
    try:
        latitude, longitude, altitude, units = Myfuncs.read_gps_coordinates("COM6")
    except KeyboardInterrupt:
        print("Stopped reading GPS.")
    except Exception as exc:
        latitude = 42.04425
        longitude = -91.627306
        altitude = 260.00
        print(exc)

    r = Myfuncs.call_api(str(latitude), str(longitude), altitude)
    
else:
#Just use canned data from an old file
    with open(r"./Data/data.txt", "r", encoding="utf-8") as f:
        r = f.read()

r_list = r["ac"] #Extract the list of aircraft from the API response

keys_to_keep = {"lat", "lon", "alt_geom"} #Only keep the keys we need for plotting and range calculations
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

slant_range = [0] * len(r_list) #Initialize a list to hold the slant range values for each aircraft
terrain_masking = [0] * len(r_list) #Initialize a list to hold the terrain elevation values for each aircraft

for i in range(len(r_list)):
    radar = (latitude, longitude)
    plane = (r_list[i]["lat"], r_list[i]["lon"])
    Myfuncs.plot_plane (radar, plane, my_map, "Slant Range Path")
    
    radar += ((altitude),)
    plane += ((r_list[i]["alt_geom"] * 0.3048),)

    slant_range[i] = Myfuncs.calculate_slant_range(radar, plane)
    terrain_masking[i] = Myfuncs.get_elevation(radar, plane, 3)
    
    