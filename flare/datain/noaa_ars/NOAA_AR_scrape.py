from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd

def location_string_to_lon_lat(loc_str):
    lat = loc_str.strip()[0:3].replace('N', '').replace('S', '-')
    lon = loc_str.strip()[3:6].replace('W', '').replace('E', '-')
    return int(lon), int(lat)

def convert_to_int(int_str):
    try:
        return int(int_str)
    except ValueError:
        return np.nan

noaa_dir_path = './from_noaa_scrapes'


all_files = [f for f in listdir(noaa_dir_path) if isfile(join(noaa_dir_path, f))]
noaa_files = [join(noaa_dir_path, f) for f in all_files]
noaa_files.sort(reverse = False)
# print(noaa_files[1:5])
# quit()
# In[4]:

ar_columns = ['year', 'month', 'day', 't_in_t', 'noaa_ar_no', 'greenwich', 'mcintosh', 'obs_whole_spot_area',
                       'number_of_spots', 'corr_whole_spot_area', 'distance_from_center', 'position_angle_north',
                       'carrington_longitude', 'latitude', 'central_meridian_dist']
# file name: year month day
# available columns = Nmbr Location  Lo  Area  Z   LL   NN Mag Type
all_noaa_ars = []

for f in noaa_files:
    date_str = f.split('/')[-1].strip('SRS.txt')
    is_plage = False
    with open(f) as fp:
        for cnt, line in enumerate(fp):
            if cnt < 9:
                continue

            if line.startswith('I.  Regions with Sunspots.'):
                is_plage = False
                continue

            if line.startswith('IA. H-alpha Plages without Spots.'):
                is_plage = True
                continue

            if line.startswith('II. Regions Due to Return'):
                break

            line_values = line.split(' ')
            line_values = [attr for attr in line_values if attr!='']
            if line_values[0].startswith('None') or line_values[0].startswith('Nmbr'):
                continue

            print(line_values)
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            noaa_number = int(line_values[0]) + 10000

            location = line_values[1]
            lon, lat = location_string_to_lon_lat(location)

            Lo = convert_to_int(line_values[2].strip('\n'))

            if not is_plage:
                area = int(line_values[3])
                Z = line_values[4]
                LL = int(line_values[5])
                NN = int(line_values[6])
                mag_type = line_values[7].strip('\n')
            else:
                area = np.nan
                Z = 'None'
                LL = np.nan
                NN = np.nan
                mag_type = 'Plage'

            # print(year, month, day, noaa_number, location, Lo)
            # if not is_plage:
            # print(area, Z, LL, NN, mag_type)

            # noaa_ar = int(line[12:20])
            # greenwich_group_type = str(line[20:24]).strip()
            # mcintosh_group_type = str(line[25:29]).strip()
            #
            # obs_whole_spot_area = float(line[30:34])
            # number_of_spots_in_group = float(line[35:39])
            # corrected_whole_spot_area = float(line[40:44])
            #
            # distance_from_center_of_solar_disk = float(line[45:50])
            # position_angle_from_heliographic_north = float(line[51:56])
            # carrington_longitude_in_degrees = float(line[57:62])
            # latitude  = float(line[63:68]) # _negative_to_the_south
            # central_meridian_distance = float(line[69:74]) # , negative to the East
            #
            ar_tuple = (year, month, day, noaa_number, lon, lat, Lo, area, Z, LL, NN, mag_type)
            print(ar_tuple)
            all_noaa_ars.append(ar_tuple)
            print('==========================================')


noaa_df= pd.DataFrame(data=all_noaa_ars,
                      columns = ['year', 'month', 'day', 'noaa_ar_no', 'central_meridian_dist', 'latitude',
                                 'carrington_longitude', 'corr_whole_spot_area', 'mcintosh', 'LL', 'number_of_spots',
                                 'greenwich'])
noaa_df = noaa_df.sort_values(by=['year', 'month', 'day'])

noaa_df.to_csv('./noaa_ars_plages.csv')

