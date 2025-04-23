from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd
import flr_utils as utils

GOES_FLARE_PATH = '/Users/fuzzb/OneDrive/Documents/armvtsprep/flare/goes_hpc.csv'
GOES_FLARE_OUTPUT_PATH = '/Users/fuzzb/OneDrive/Documents/armvtsprep/flare/noaa_ar_hpc.csv'
NOAA_AR_PATH = '/Users/fuzzb/OneDrive/Documents/armvtsprep/flare/solar_region_data.csv'

def initialize():
	noaa_ar = read_noaa_ars()
	# print(noaa_ar)

	goes_fl = get_flare_dataframe(GOES_FLARE_PATH)
	#print(goes_fl)

	centroids = get_ar_centroids(goes_fl, noaa_ar)
	goes_fl['centroids'] = centroids
	print(goes_fl.head(10))

	goes_fl = fix_cent_locations(goes_fl)

	print(goes_fl.head(10))

	goes_fl = utils.append_hpc_coord(goes_fl)
	goes_fl = transform_fl_lat_lon(goes_fl)

	print(goes_fl.head(10))

	goes_fl.to_csv(GOES_FLARE_OUTPUT_PATH)


def read_noaa_ars():
	noaa_ar = pd.read_csv(NOAA_AR_PATH)
	#noaa_ar = noaa_ar.rename(columns={'Unnamed: 0': 'id'})
	#noaa_ar = noaa_ar.set_index("id")
	#noaa_ar['year'] = noaa_ar['year'].astype(str)
	#noaa_ar['month'] = noaa_ar['month'].astype(str)
	#noaa_ar['day'] = noaa_ar['day'].astype(str)
	#noaa_ar['ar_time'] = pd.to_datetime(noaa_ar[['year', 'month', 'day']].apply(lambda x: '-'.join(x), axis=1))
	return noaa_ar


def transform_fl_lat_lon(fdf):
	lat = fdf['fl_lat']
	lon = fdf['fl_lon']
	fdf['y'] = np.sin(np.deg2rad(lat))
	fdf['x'] = np.sin(np.deg2rad(lon)) * np.cos(np.deg2rad(lat))
	return fdf


def calculate_lon_delta(lat_degree, day):
	alpha = 14.11
	beta = -1.7
	gamma = -2.35

	velocity_in_deg = alpha + beta * (np.sin(np.deg2rad(lat_degree))) ** 2 + gamma * (np.sin(np.deg2rad(lat_degree))) ** 4
	delta_lon = velocity_in_deg * day
	return delta_lon
	#TEST: print calculate_lon_delta(0, -25.5)

def fix_cent_locations(df):
	# set goes location as primary source
	df['fl_location'] = df['goes_location']

	# for each goes location that is still invalid --(0, 0), set it to nan
	df.loc[df['fl_location'] == '(0, 0)', 'fl_location'] = df.loc[df['fl_location'] == '(0, 0)', 'centroids']

	# drop if there exists fl lat and fl lon columns to avoid confusion
	df = df.drop(['fl_lat', 'fl_lon'], axis=1)

	# create two new columns fl_lat and fl_lon for latitude and longitude
	df = df.reindex(columns=np.append(df.columns.values, ['fl_lat', 'fl_lon']))
	# extract the locations from either aia or goes location strings
	df = df.apply(utils.reformat_locations, axis=1)

	# fix interpolated latitudes and longitudes over 90 degrees

	# print df.to_csv('flares_flares.csv')
	return df


def get_flare_dataframe(file_path):
	"""Reads the goes flare dataframe given in flare file path, downloaded using our script"""
	df = pd.read_csv(file_path, delimiter=',',
	                 parse_dates=['start_time', 'end_time', 'peak_time'])
	new_columns = df.columns.values
	new_columns[0] = 'flare_id'
	df.columns = new_columns
	df = df.set_index('flare_id')
	# return fix_noaa_ar_numbers( pd.read_csv(file_path, delimiter='\t', parse_dates=True) )
	#df = fix_flare_locations(fix_noaa_ar_numbers(df))
	df = transform_fl_lat_lon(df)
	# df = df[ df['goes_class'] > 'C9.9' ]

	return df


def fix_flare_locations(df):
	""" Gets the flare dataframe and consolidates the flare locations from aia and goes using the following strategy
        if there is a valid aia location, that is not NaN, it uses that. If not it uses the goes location if valid"""

	# set goes location as primary source
	df['fl_location'] = df['goes_location']

	# for each goes location that is still invalid --(0, 0), set it to nan
	df.loc[df['fl_location'] == '(0, 0)', 'fl_location'] = np.nan

	# create two new columns fl_lat and fl_lon for latitude and longitude
	df = df.reindex(columns=np.append(df.columns.values, ['fl_lat', 'fl_lon']))
	# extract the locations from either aia or goes location strings
	df = df.apply(utils.reformat_locations, axis=1)

	return df


def fix_noaa_ar_numbers(df):
	""" Gets the flare dataframe and consolidates the noaa ar numbers from aia and goes using the following strategy
        if the is a valid goes active region, that is not 0, it uses that. If not it uses a valid aia number"""

	# set goes noaa numbers as primary source
	# df['noaa_active_region'] = df['noaa_active_region_goes']
	# if noaa ar no from goes is zero, set it to NaN
	df.loc[df['noaa_active_region'] == 0, 'noaa_active_region'] = np.nan

	# for each null (nan) noaa ar number, get the ar number from aia
	# df.loc[pd.isnull(df['noaa_active_region']), 'noaa_active_region'] =  df.loc[pd.isnull(df['noaa_active_region']), 'noaa_active_region_aia']
	# for each noaa ar number that is still zero, set it to nan
	# df.loc[df['noaa_active_region'] == 0, 'noaa_active_region'] = np.nan

	# print len(df['noaa_active_region'].unique())
	return df


def search_noaa(noaa_ar, noaa_no, peak_time):
	#     print noaa_no
	if noaa_no == 0:
		return {}
	elif noaa_no < 10000:
		noaa_no += 10000

	print(noaa_ar)

	my_ar = noaa_ar[(noaa_ar['region_number'] == noaa_no)]
	if my_ar.shape[0] == 0:
		if noaa_no == noaa_no:
			print('There are no AR from NOAA for \#', noaa_no)
		return {}
	else:
		print('Found AR \#', noaa_no, 'for time', peak_time)
		my_ar['diff'] = my_ar["ar_time"] - peak_time
		closest = my_ar[np.abs(my_ar['diff']) == np.abs(my_ar['diff']).min()]
		closest = closest[np.abs(closest['diff'].values) < np.timedelta64(72, 'h')]
		if closest.shape[0] == 1:
			return closest.to_dict(orient='records')
		else:
			return {}


def calc_dist(noaa_ar, ar_no, t, fl_x, fl_y):
	ar_record = search_noaa(noaa_ar, ar_no, t)
	if (len(ar_record)) == 1:
		ar_x = ar_record[0]['x']
		ar_y = ar_record[0]['y']
		dist = np.sqrt((fl_x - ar_x) ** 2 + (fl_y - ar_y) ** 2)
	else:
		dist = np.nan
	return dist


def calc_cent_dist(noaa_ar, ar_no, t):
	ar_record = search_noaa(noaa_ar, ar_no, t)
	if (len(ar_record)) == 1:
		ar_x = ar_record[0]['x']
		ar_y = ar_record[0]['y']
		return np.sqrt(ar_x ** 2 + ar_y ** 2)
	else:
		return np.nan

	return dist


def distance_to_ar(fdf, noaa_ar):
	return fdf.apply(lambda row: calc_dist(noaa_ar, row['noaa_active_region'], row['peak_time'], row['x'], row['y']), axis=1)


def distance_to_cent(fdf, noaa_ar):
	return fdf.apply(lambda row: calc_cent_dist(noaa_ar, row['noaa_active_region'], row['peak_time']), axis=1)


def find_noaa_centroid(noaa_ar, ar_no, t, fl_x, fl_y):
	"""
	Based on a given noaa_ar number and a time, find the interpolated noaa ar location.
	If location (specifically longitude is greater than 90 or less than -90, fix them to 90 degrees.
	:param noaa_ar: Data frame for noaa ar's
	:param ar_no: Noaa active region number
	:param t: time of the flare (for interpolation)
	:param fl_x: not used
	:param fl_y: not used
	:return:
	"""
	ar_record = search_noaa(noaa_ar, ar_no, t)
	#     print ar_record
	if (len(ar_record)) == 1:
		ar_lat = ar_record[0]['latitude']
		ar_lon = ar_record[0]['central_meridian_dist']

		t_diff_day = ar_record[0]['diff'] / pd.Timedelta('1 day')
		#         print t_diff_day
		new_ar_lon = ar_lon + calculate_lon_delta(ar_lat, -t_diff_day)
		if new_ar_lon > 90:
			new_ar_lon = 90
		elif new_ar_lon < -90:
			new_ar_lon = -90

		return '(' + str(new_ar_lon) + ', ' + str(ar_lat) + ')'
	else:
		return np.nan


def get_ar_centroids(fdf, noaa_ar):
	return fdf.apply(
		lambda row: find_noaa_centroid(noaa_ar, row['noaa_active_region'], row['peak_time'], row['x'], row['y']),
		axis=1)


def transform_fl_lat_lon(fdf):
	lat = fdf['fl_lat']
	lon = fdf['fl_lon']
	fdf['y'] = np.sin(np.deg2rad(lat))
	fdf['x'] = np.sin(np.deg2rad(lon)) * np.cos(np.deg2rad(lat))
	return fdf


def main():
	initialize()
	print('DONE!')


if __name__ == "__main__":
	main()
