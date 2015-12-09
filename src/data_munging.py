import functools
import numpy as np
import os
import pandas as pd
import pyproj
import requests
import rtree
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


chicago_bounding_box = {'upper_lat': 42.3098,
                        'lower_lat': 41.3273,
                        'left_lon': -88.3823,
                        'right_lon': -87.0941}

nyc_bounding_box = {'upper_lat': 41.340,
                        'lower_lat': 40.355,
                        'left_lon': -74.713,
                        'right_lon': -71.570}

def filter_readings_by_bb(readings, bb):
    """Filters readings by start lat/lon contained in bounding box."""
    to_keep = np.logical_and(np.logical_and(readings['start_lon'] >= bb['left_lon'],
        readings['start_lon'] <= bb['right_lon']),
        np.logical_and(readings['start_lat'] >= bb['lower_lat'],
            readings['start_lat'] <= bb['upper_lat']))
    return readings.ix[to_keep, :]

def filter_readings_to_chicago(readings):
    return filter_readings_by_bb(readings, chicago_bounding_box)

def filter_readings_to_nyc(readings):
    return filter_readings_by_bb(readings, nyc_bounding_box)

def add_routes_to_shapely():
    "nothing"

def calc_dist(*args):
    """I have no idea if Clark ='s ellipsoid is good for our purposes or not."""
    if len(args[0]) > 0:
        args = [list(arg) for arg in args]
    clark_geod = pyproj.Geod(ellps='clrk66')
    az12, az21, dist = clark_geod.inv(*args)
    return dist

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
    readings.sort_values(by=['ride_id', 'id'], inplace=True)
    return (rides, readings)

def add_proj_to_readings(readings, proj):
    proj_apply = functools.partial(_proj_apply, proj=proj)
    start_xy = readings.loc[:, ['start_lon', 'start_lat']].apply(proj_apply, axis=1)
    end_xy = readings.loc[:, ['end_lon', 'end_lat']].apply(proj_apply, axis=1)
    start_xy.columns = ('start_x', 'start_y')
    end_xy.columns = ('end_x', 'end_y')
    readings = readings.join(start_xy)
    readings = readings.join(end_xy)
    return readings

def clean_readings(readings):
    for axis in ['x', 'y', 'z']:
        readings['num_accel_' + axis] = readings['acceleration_' + axis].apply(_string_to_array)
        readings['std_' + axis] = readings['num_accel_' + axis].apply(np.std)
    readings['std_total'] = (readings['std_x'] ** 2 + readings['std_y'] ** 2 + readings['std_z'] ** 2) ** 0.5
    readings['gps_dist'] = calc_dist(readings['start_lon'],
                                     readings['start_lat'],
                                     readings['end_lon'],
                                     readings['end_lat'])
    readings['gps_speed'] = readings['gps_dist'] / (readings['end_time'] - readings['start_time'])
    readings['total_readings'] = readings['num_accel_x'].apply(lambda x: len(x))
    return readings

def pull_data_from_heroku():
    #does not work for some reason
    subprocess.call(src_dir + 'dump_data_to_csv.sh')

def pull_data_by_time_range():
    """Pulls data by time range"""

def update_data():
    """Archives old data and pulls new data. If data grows large,
    only get the new stuff. Can organize this within folders."""

def insert_readings_rtree(readings):
    readings_idx = rtree.index.Index()
    for index, row in readings[['start_x', 'start_y', 'end_x', 'end_y']].iterrows():
        left = min(row.start_x, row.end_x)
        right = max(row.start_x, row.end_x)
        top = max(row.start_y, row.end_y)
        bottom = min(row.start_y, row.end_y)
        # index_obj = (index, (left, bottom, right, top))
        # print index_obj
        readings_idx.insert(index, (left, bottom, right, top))
    return readings_idx

def expand_bb(bb, exp_amt):
    return [bb[0] - exp_amt, bb[1] - exp_amt,
            bb[2] + exp_amt, bb[3] + exp_amt]

if __name__ == '__main__':
    """does nothing"""