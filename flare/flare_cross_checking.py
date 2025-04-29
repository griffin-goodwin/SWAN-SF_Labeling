
from builtins import print

import numpy as np
import pandas as pd
import flr_utils as utils


SSW_FLARE_PATH = '/Users/griffingoodwin/Documents/gitrepos/armvtsprep/flare/ssw_hpc2.csv'
HINODE_FLARE_PATH = '/Users/griffingoodwin/Documents/gitrepos/armvtsprep/flare/Hinode_fromXRT.csv'
GOES_FLARE_PATH = '/Users/griffingoodwin/Documents/gitrepos/armvtsprep/flare/goes_hpc.csv'


# NO_LOC_FL_PATH = './datain/goes_fl_no_loc.csv'
# GOES_FL_OUT_PATH = '/datain/goes_fl_wloc.csv'


def initialize():
	goesf = utils.get_goes_flare_dataframe(GOES_FLARE_PATH)
	sswf = utils.get_ssw_flare_dataframe(SSW_FLARE_PATH)
	hdf = utils.get_hinode_flare_dataframe(HINODE_FLARE_PATH)

	no_correspondence_count = 0

	ssw_fl_id_list = []
	ssw_dist_list = []
	ssw_x_list = []
	ssw_y_list = []
	hinode_fl_id_list = []
	hinode_dist_list = []
	hinode_x_list = []
	hinode_y_list = []
	ssw_hinode_dist_list = []
	ssw_ar_list = []
	hinode_ar_list = []


	for fl_rec in goesf.itertuples():  # process each flare record from primary GOES flare list
		fl_s = fl_rec.start_time
		fl_e = fl_rec.end_time
		fl_mag = fl_rec.goes_class
		fl_xhpc = fl_rec.x_hpc
		fl_yhpc = fl_rec.y_hpc

		# search for flares in SSW and Hinode based on (1) temporal overlap and (2) magnitude
		ssw_results = search_fl_mag(search_fl_time(sswf, fl_s, fl_e), fl_mag)
		hinode_results = search_fl_mag(search_fl_time(hdf, fl_s, fl_e), fl_mag)

		ssw_flare_id = None
		hinode_flare_id = None
		if ssw_results.shape[0] == 0 and hinode_results.shape[0] == 0:
			no_correspondence_count += 1

		# find the closest SSW flare based on the spatial locations of the flares
		ssw_flare_id, ssw_dist, ssw_x, ssw_y, ssw_ar = find_closest(ssw_results, fl_xhpc, fl_yhpc)

		# find the closest Hinode flare based on the spatial locations of the flares
		hinode_flare_id, h_dist, hinode_x, hinode_y, hinode_ar = find_closest(hinode_results, fl_xhpc, fl_yhpc)



		#There may be multiple results returned both from ssw and Hinode due to the fact that many GOES flares do not
		# have a location. Many of those multiple results are near-duplicates (either location or time corrected in the
		# respective flare data frames. We eliminate those first, and later pick the two closest to one another in SSW
		# and Hinode results.
		ssw_flare_id, ssw_dist, ssw_ar, ssw_x, ssw_y, hinode_flare_id, h_dist, hinode_ar, hinode_x, hinode_y = \
			resolve_duplicates_from_secondary_sources(ssw_flare_id, ssw_dist, ssw_ar, ssw_x, ssw_y,
			                                          hinode_flare_id, h_dist, hinode_ar, hinode_x, hinode_y)

		# print(ssw_x, ssw_y, type(hinode_x), hinode_y)

		if isinstance(ssw_flare_id, list):
			ssw_flare_id = ssw_flare_id[0]
		if isinstance(ssw_x, np.ndarray):
			ssw_x = ssw_x[0]
		if isinstance(ssw_y, np.ndarray):
			ssw_y = ssw_y[0]
		if isinstance(ssw_ar, (list, np.ndarray)):
			ssw_ar = ssw_ar[0]

		if isinstance(hinode_flare_id, list):
			hinode_flare_id = hinode_flare_id[0]
		if isinstance(hinode_x, np.ndarray):
			hinode_x = hinode_x[0]
		if isinstance(hinode_y, np.ndarray):
			hinode_y = hinode_y[0]
		if isinstance(hinode_ar, (list, np.ndarray)):
			hinode_ar = hinode_ar[0]

		ssw_hinode_dist = np.sqrt((ssw_x -hinode_x )**2 + (ssw_y -hinode_y )**2 )
		ssw_hinode_dist_list.append(ssw_hinode_dist)
		# print(ssw_x, ssw_y, hinode_x, hinode_y)

		ssw_fl_id_list.append(ssw_flare_id)
		hinode_fl_id_list.append(hinode_flare_id)
		ssw_dist_list.append(ssw_dist)
		hinode_dist_list.append(h_dist)


		ssw_x_list.append(ssw_x)
		ssw_y_list.append(ssw_y)
		ssw_ar_list.append(ssw_ar)

		hinode_x_list.append(hinode_x)
		hinode_y_list.append(hinode_y)
		hinode_ar_list.append(hinode_ar)

	goesf['ssw_flare_id'] = ssw_fl_id_list
	goesf['min_ssw_dist'] = ssw_dist_list
	goesf['ssw_x_hpc'] = ssw_x_list
	goesf['ssw_y_hpc'] = ssw_y_list
	goesf['ssw_ar'] = ssw_ar_list


	goesf['hinode_flare_id'] = hinode_fl_id_list
	goesf['min_hinode_dist'] = hinode_dist_list
	goesf['hinode_x_hpc'] = hinode_x_list
	goesf['hinode_y_hpc'] = hinode_y_list
	goesf['hinode_ar'] = hinode_ar_list

	goesf['ssw_hinode_dist'] = ssw_hinode_dist_list

	ssw_verification(goesf, threshold=275)
	hinode_verification(goesf, threshold=275)
	goes_primary_verification(goesf)
	hinode_ssw_secondary_verification(goesf, threshold=275)

	goesf = add_missing_locations(goesf)

	goesf['candidate_ars'] = goesf[['noaa_active_region', 'ssw_ar', 'hinode_ar']].values.tolist()
	# goesf.loc[(~(goesf['ssw_verified']) & ~(goesf['hinode_verified'])) & (goesf['secondary_verified']), 'x_hpc'] = goesf['hinode_x_hpc']
	# goesf.loc[(~(goesf['ssw_verified']) & ~(goesf['hinode_verified'])) & (goesf['secondary_verified']), 'y_hpc'] = goesf['hinode_y_hpc']

	print("Number of flares with no correspondence", no_correspondence_count)
	goesf.to_csv('goes_flares_integrated.csv')


def add_missing_locations(fdf):
	fl_location_list = []
	fl_lon_list = []
	fl_lat_list = []
	fl_loc_src_list = []
	for index, row in fdf.iterrows():
		#     print(index,row['fl_location'], row['ssw_x_hpc'], row['ssw_y_hpc'],
		#                   row['hinode_x_hpc'], row['hinode_y_hpc'] )
		fl_location = row['fl_location']
		fl_lon = row['fl_lon']
		fl_lat = row['fl_lat']
		ssw_x = row['ssw_x_hpc']
		ssw_y = row['ssw_y_hpc']
		hinode_x = row['hinode_x_hpc']
		hinode_y = row['hinode_y_hpc']
		event_time = row['peak_time']
		if type(fl_location) is str:
			loc_source = 'GOES'
		elif np.isnan(fl_location):
			if not np.isnan(ssw_x):
				fl_lon, fl_lat = HPC_to_HGS(ssw_x, ssw_y, event_time)
				loc_source = 'SSW'
				fl_location = '(' + str(fl_lon) + ', ' + str(fl_lat) + ')'
			elif not np.isnan(hinode_x):
				fl_lon, fl_lat = HPC_to_HGS(hinode_x, hinode_y, event_time)
				loc_source = 'XRT'
				fl_location = '(' + str(fl_lon) + ', ' + str(fl_lat) + ')'
			else:
				lon = np.nan
				lat = np.nan
				loc_source = 'NoLocation'
				fl_location = np.nan

		fl_location_list.append(fl_location)
		fl_loc_src_list.append(loc_source)
		fl_lon_list.append(fl_lon)
		fl_lat_list.append(fl_lat)

	fdf.drop(columns=['fl_location', 'fl_lon', 'fl_lat'], inplace=True)
	fdf['fl_location'] = fl_location_list
	fdf['fl_lon'] = fl_lon_list
	fdf['fl_lat'] = fl_lat_list
	fdf['fl_loc_src'] = fl_loc_src_list

	return fdf

import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

# def append_hpc_coord(fdf):
#     fdf['x_hpc'] = fdf.apply(x_HPC_to_HGS, axis=1) # x coordinates of hpc
#     fdf['y_hpc'] = fdf.apply(ycoord_transformer, axis=1) # y coordinates of hpc
#     return fdf

def HPC_to_HGS(x_hpc, y_hpc, event_time):
#     event_time = x['start_time']
    c = SkyCoord(x_hpc*u.arcsec, y_hpc*u.arcsec, frame=frames.Helioprojective, obstime=event_time, observer='earth')
    c_hgs = c.transform_to(frames.HeliographicStonyhurst)
    return c_hgs.lon.degree, c_hgs.lat.degree

def resolve_duplicates_from_secondary_sources(ssw_flare_id, ssw_dist, ssw_ar, ssw_x, ssw_y, hinode_flare_id, h_dist,
                                              hinode_ar, hinode_x, hinode_y):
	"""
	Function to resolve duplicates from secondary flare resources (SSW and Hinode)
	:param ssw_flare_id: flare id list of SSW flares
	:param ssw_dist: distance(s) of SSW flare(s) to GOES flare
	:param ssw_ar: NOAA AR number for SSW flare(s)
	:param ssw_x: X coordinate of SSW flare(s)
	:param ssw_y: Y coordinate of SSW flare(s)
	:param hinode_flare_id: flare id list of Hinode flares
	:param h_dist: distance(s) of Hinode flare(s) to GOES flare
	:param hinode_ar: NOAA AR number for SSW flare(s)
	:param hinode_x: X coordinate of Hinode flare(s)
	:param hinode_y: Y coordinate of Hinodeflare(s)
	:return: all the above stated parameters resolved and returned as a tuple consisting information about one Hinode
				and one SSW flare including their distance to GOES flare, NOAA AR number, and X&Y locations.
	"""

	if not np.isnan(ssw_x).all():  # if there are ssw results.
		if len(ssw_x) > 1:  # if there are multiple ssw results
			if is_near_duplicate(ssw_x, ssw_y):  # if near duplicate get the first one
				ssw_flare_id = ssw_flare_id[0]
				if not np.isnan(ssw_dist).any():
					ssw_dist = ssw_dist[0]
				ssw_x = ssw_x[0]
				ssw_y = ssw_y[0]
				ssw_ar = ssw_ar[0]
			else:  # if they are not near duplicate, then search for the closest pair between SSW and Hinode flares
				# pick the Hinode flare and SSW flare pair that is closest to one another
				# print('SSW NOT DUPLICATE (ORIGINALS): ', ssw_x, ssw_y)
				ssw_flare_id, ssw_x, ssw_y, ssw_ar, hinode_flare_id, hinode_x, hinode_y, hinode_ar = \
					get_closest_secondary_correspondence(ssw_flare_id, ssw_x, ssw_y, ssw_ar,
					                                     hinode_flare_id, hinode_x, hinode_y, hinode_ar)
			# print(ssw_flare_id, ssw_dist, ssw_x, ssw_y)
			# print('Hinode: ', hinode_x, hinode_y)
			# print('\n')
		else:  # there is only one SSW results, check if there are multiple Hinode results
			if not np.isnan(hinode_x).all():  # if there are hinode results that are not null
				if len(hinode_x) > 1:  # if there are multiple hinode results
					if is_near_duplicate(hinode_x, hinode_y):  # if they are near duplicate pick one
						hinode_flare_id = hinode_flare_id[0]
						if not np.isnan(h_dist).any():
							h_dist = h_dist[0]
						hinode_x = hinode_x[0]
						hinode_y = hinode_y[0]
					else:  # if not near duplicate, find the pair that is closest to one another
						# print('HINODE NOT DUPLICATE (ORIGINAL)', hinode_x, hinode_y)
						# print(hinode_flare_id, h_dist, hinode_x, hinode_y)
						# print('SSW:', ssw_x, ssw_y)
						hinode_flare_id, hinode_x, hinode_y, ssw_flare_id, ssw_x, ssw_y = \
							get_closest_secondary_correspondence(hinode_flare_id, hinode_x, hinode_ar,
							                                     hinode_y, ssw_flare_id, ssw_x, ssw_y, ssw_ar)
					# print('\n')
	return ssw_flare_id, ssw_dist, ssw_ar, ssw_x, ssw_y, hinode_flare_id, h_dist, hinode_ar, hinode_x, hinode_y


def ssw_verification(fdf, threshold=250):
	fdf['ssw_verified'] = fdf['min_ssw_dist'] < threshold


def hinode_verification(fdf, threshold=250):
	fdf['hinode_verified'] = fdf['min_hinode_dist'] < threshold


def goes_primary_verification(fdf):
	fdf['primary_verified'] = (fdf['hinode_verified']) | (fdf['ssw_verified'])


def hinode_ssw_secondary_verification(fdf, threshold=250):
	fdf['secondary_verified'] = fdf['ssw_hinode_dist'] < threshold


def is_near_duplicate(xlist, ylist, threshold=50):
	"""
	Function for checking if two points represented as list of X and Y coordinates are close-by
	:param xlist: list of X coordinates ideally representing two points
	:param ylist: list of Y coordinates ideally representing two points
	:param threshold: threshold for being close by
	:return: if lists contains only one, return True
			 if lists contains two, then return True if the two points are less than threshold apart from one another
		                            else return False
			 if list contains more than two elements, return False
	"""
	if len(xlist) == 1:
		return True
	elif len(xlist) == 2:
		return np.sqrt((xlist[0 ] -xlist[1] )**2 + (ylist[0] - ylist[1] )**2) < threshold
	else:
		return False


def get_closest_secondary_correspondence(flare_ids, orig_x, orig_y, orig_ar, query_ids, query_x, query_y, query_ar):
	idxmin = 0
	xlist = [(x - query_x) ** 2 for x in orig_x]
	ylist = [(y - query_y) ** 2 for y in orig_y]
	query_dist_list = np.array( [sum(r) for r in zip(xlist, ylist)] )

	result = np.where(query_dist_list== np.amin(query_dist_list))

	print(query_dist_list)
	fli = result[0][0]
	qi = result[1][0]

	# print('Returned value', query_dist_list[ result[0][0], result[1][0] ])
	return flare_ids[fli], orig_x[fli], orig_y[fli], orig_ar[fli], \
	       query_ids[qi], query_x[qi], query_y[qi], query_ar[qi]


def search_fl_mag(df, mag):
	"""
	Filter a flare data frame based on 'goes_class' (magnitude) attribute with a given magnitude (mag)
	:param df: flare data frame to be searched
	:param mag: the magnitude string [A|B|C|M|X].[0-9][0-9]
	:return: The filtered data frame
	"""
	mf_df = df[ df['goes_class'] == mag ]  # magnitude filtered df
	return mf_df


def search_fl_time(df, qs, qe):
	"""
	Search a flare data frame (df) given as an input based on a query interval (temporal overlap)
	:param df: flare data frame
	:param qs: query start time
	:param qe: query end time
	:return: Filtered flare data frame
	"""
	tf_df = df[df['start_time'] < qe]
	tf_df = tf_df[tf_df['end_time'] > qs]
	# tf_df = df[ (df['start_time'] < qe) & (df['end_time'] > qs)] # time filtered df
	return tf_df


def find_closest(df, x, y):
	"""
	Filter a flare data frame (df) to find the closest flare to a point location represented by x and y coordinates.
	:param df: flare data frame to be searched, must include HPC (x and y) coordinates and noaa ar number.
	:param x: target flare's X coordinate (HPC)
	:param y: target flare's Y coordinate (HPC)
	:return: a tuple containing (1) id of the flare in the target DB (2) distance (L2 in HPC) to the given x&y locations
				(3) X coordinate of closest flare in df (4) Y coordinate of the closest flare in df, (5) NOAA active
				region number in the searched flare dataframe df. Return a tuple of None and nan's if df is empty. If x
				and y parameters are nan values, then return all elements in the df as a list in each tuple.
	"""
	if df.shape[0] == 0: # to be queried df is empty return nothing
		return (None, np.nan, np.nan, np.nan, np.nan)

	if np.isnan(x) or np.isnan(y):  # the queried flare does not have any location, return nan for distance
		return (df.index.tolist(), np.nan, df['x_hpc'].values, df['y_hpc'].values, df['noaa_active_region'].values)
	else: # calculate distance for the min and return it
		hpc_distance = ((df['x_hpc'] - x )**2 + (df['y_hpc'] - y )**2 )**( 1 /2)

		# print(hpc_distance.idxmin(), df)

		return (hpc_distance.idxmin(), hpc_distance.min(),
		        df.loc[[hpc_distance.idxmin()], ['x_hpc']].values[0],
		        df.loc[[hpc_distance.idxmin()], ['y_hpc']].values[0],
		        df.loc[[hpc_distance.idxmin()], ['noaa_active_region']].values[0])


def main():
	initialize()
	print('DONE!')


if __name__ == "__main__":
	main()
