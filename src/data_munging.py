import numpy as np
import os
import pandas as pd
import pyproj
import requests
import subprocess

src_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
root_dir = src_dir + '../'
data_dir = root_dir + 'dat/'


def _proj_apply(row, proj):
    x,y = proj(*row)
    return pd.Series({'x':x, 'y':y})

#EPSG:3435
#NAD83 / Illinois East (ftUS) (Google it)
#Note that this this projection takes arguments in the form (lon, lat),
#presumably to agree with the (x, y) output
NAD83 = pyproj.Proj('+init=EPSG:3435')
NAD83_apply = functools.partial(proj_apply, proj=NAD83)

chicago_bounding_box = {'upper_lat': 42.3098,
						'lower_lat': 41.3273,
						'left_lon': -88.3823.
						'right_lon': -87.0941}

nyc_bounding_box = {'upper_lat': 41.340,
						'lower_lat': 40.355,
						'left_lon': -74.713,
						'right_lon': -71.570}



def _string_to_array(str_array):
    if str_array.strip() == '---':
        return pd.Series()
    if str_array[:2] == '- ':
        return pd.Series(float(str_array[2:]))
    return np.array([float(i) for i in str_array[5:-1].split('\n- ')])

def get_nearest_street(lat, lon):
	osrm_api = 'http://router.project-osrm.org/nearest?loc='
	nearest_street_resp = requests.get(osrm_api + str(lat) + ',' + str(lon))
	return nearest_street.json()['name']

def read_raw_data():
	"""Returns rides and readings Pandas dfs"""
	rides = pd.read_csv('../dat/rides.csv')
	readings = pd.read_csv('../dat/readings.csv')
	return (rides, readings)

def clean_readings(cleanings):
	for axis in ['x', 'y', 'z']:
    	split_accel = readings['acceleration_' + axis].apply(_string_to_array)
    	readings['num_accel_' + axis] = split_accel


def pull_data_from_heroku():
	#does not work for some reason
	subprocess.call(src_dir + 'dump_data_to_csv.sh')

if __name__ == '__main__':
	"""does nothing"""
