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

kimball_bounding_box = {'upper_lat': 41.95,
                        'lower_lat': 41.90,
                        'left_lon': -87.75,
                        'right_lon': -87.70}


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

def filter_to_good_readings(readings):
    return readings.loc[get_good_readings(readings), :]

def get_good_readings(readings):
    return np.logical_and.reduce((readings['gps_mph'] < 30,
                                   readings['gps_mph'] > 4,
                                   readings['total_readings'] > 90,
                                   readings['total_readings'] < 110))

def calc_dist(*args):
    """I have no idea if Clark ='s ellipsoid is good for our purposes or not.
    Accepts calc_dist(lon, lat, lon, lat) where they may be iterables or
    single values."""
    try:
        args = [list(arg) for arg in args]
    except:
        'nothing'
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

to_total_mag = lambda x: [np.array([(x['num_accel_x'][i] ** 2 +
                                   x['num_accel_y'][i] ** 2 +
                                   x['num_accel_z'][i] ** 2) ** 0.5
                                   for i in range(len(x['num_accel_x']))])]

def clean_readings(readings):
    for axis in ['x', 'y', 'z']:
        readings['num_accel_' + axis] = readings['acceleration_' + axis].apply(_string_to_array)
        readings['abs_mean_' + axis] = readings['num_accel_' + axis].apply(lambda x: np.mean(np.abs(x)))
        readings['std_' + axis] = readings['num_accel_' + axis].apply(np.std)
    readings['std_total'] = (readings['std_x'] ** 2 + readings['std_y'] ** 2 + readings['std_z'] ** 2) ** 0.5
    readings['duration'] = readings['end_time'] - readings['start_time']
    readings['gps_dist'] = calc_dist(readings['start_lon'],
                                     readings['start_lat'],
                                     readings['end_lon'],
                                     readings['end_lat'])
    readings['num_accel_total'] = readings.apply(to_total_mag, axis=1)
    readings['num_accel_total'] = readings['num_accel_total'].apply(lambda x: x[0])
    readings['abs_mean_total'] = readings['num_accel_total'].apply(np.mean)
    readings['gps_speed'] = readings['gps_dist'] / readings['duration']
    readings['gps_mph'] = readings['gps_speed'] * 2.23694
    readings['total_readings'] = readings['num_accel_x'].apply(lambda x: len(x))
    readings['start_datetime'] = readings['start_time'].apply(pd.datetime.fromtimestamp)
    readings['end_datetime'] = readings['end_time'].apply(pd.datetime.fromtimestamp)
    readings['abs_mean_over_speed'] = readings['abs_mean_total'] / readings['gps_speed']
    return readings

def pull_data_from_heroku():
    #does not work for some reason
    subprocess.call(src_dir + 'dump_data_to_csv.sh')

def pull_data_by_time_range():
    """Pulls data by time range"""

def update_data():
    """Archives old data and pulls new data. If data grows large,
    only get the new stuff. Can organize this within folders."""

def reading_to_bb(row):
    left = min(row.start_x, row.end_x)
    right = max(row.start_x, row.end_x)
    bottom = min(row.start_y, row.end_y)
    top = max(row.start_y, row.end_y)
    return (left, bottom, right, top)

def insert_readings_rtree(readings):
    readings_idx = rtree.index.Index()
    for index, reading in readings.iterrows():
        readings_idx.insert(index, reading_to_bb(reading))
    return readings_idx

def point_to_bb(x, y, side_length):
    return [x - side_length / 2., y - side_length / 2.,
            x + side_length / 2, y + side_length / 2.]

def expand_bb(bb, exp_amt):
    return [bb[0] - exp_amt, bb[1] - exp_amt,
            bb[2] + exp_amt, bb[3] + exp_amt]

def calc_reading_diffs(reading0, reading1):
    start0 = reading0[['start_x', 'start_y']].values
    start1 = reading1[['start_x', 'start_y']].values
    end0 = reading0[['end_x', 'end_y']].values
    end1 = reading1[['end_x', 'end_y']].values
    diff0 = np.linalg.norm(start0 - start1) + np.linalg.norm(end0 - end1)
    diff1 = np.linalg.norm(start0 - end1) + np.linalg.norm(end0 - start1)
    diff = min(diff0, diff1)
    dist0 = np.linalg.norm(start0 - end0)
    dist1 = np.linalg.norm(start1 - end1)
    if dist0 == 0 or dist1 == 0:
        return np.inf
    return diff / (dist0 + dist1)

def select_random_point(readings):
    """ Selects a random reading and samples a point from
    the segment as uniform(0,1) linearly interpolating from start
    to end.
    """
    an_idx = np.random.choice(readings.index, 1)
    place_on_route = np.random.uniform()
    return (an_idx,
           (float(place_on_route * readings['start_x'][an_idx]  +
             (1 - place_on_route) * readings['end_x'][an_idx]),
           float(place_on_route * readings['start_y'][an_idx]  +
            (1 - place_on_route) * readings['end_y'][an_idx])))

if __name__ == '__main__':
    """does nothing"""