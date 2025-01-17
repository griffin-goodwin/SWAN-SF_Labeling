#!/usr/bin/env python
# coding: utf-8

# In[1]:


from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd

noaa_dir_path = './'


# In[2]:


all_files = [f for f in listdir(noaa_dir_path) if isfile(join(noaa_dir_path, f))]
noaa_files = [join(noaa_dir_path, f) for f in all_files if f.startswith('g')]


# In[4]:


noaa_files
all_noaa_ars = []
for f in noaa_files:
    with open(f) as fp:  
        for cnt, line in enumerate(fp):
            print(line)
            year = int(line[0:4])
            month = int(line[4:6])
            day = int(line[6:8])
            time_in_thousands = float(line[8:12])
            noaa_ar = int(line[12:20])
            greenwich_group_type = str(line[20:24]).strip()
            mcintosh_group_type = str(line[25:29]).strip()
            
            obs_whole_spot_area = float(line[30:34])
            number_of_spots_in_group = float(line[35:39])
            corrected_whole_spot_area = float(line[40:44])
            
            distance_from_center_of_solar_disk = float(line[45:50])
            position_angle_from_heliographic_north = float(line[51:56])
            carrington_longitude_in_degrees = float(line[57:62])
            latitude  = float(line[63:68]) # _negative_to_the_south
            central_meridian_distance = float(line[69:74]) # , negative to the East
            
            ar_tuple = (year,month,day,time_in_thousands,noaa_ar, greenwich_group_type, mcintosh_group_type, 
                        obs_whole_spot_area , number_of_spots_in_group, corrected_whole_spot_area,
                        distance_from_center_of_solar_disk, position_angle_from_heliographic_north, 
                        carrington_longitude_in_degrees, latitude, central_meridian_distance)
            all_noaa_ars.append(ar_tuple)
            print('==========================================')


# In[5]:


noaa_df= pd.DataFrame(data =all_noaa_ars, columns = ['year', 'month', 'day', 't_in_t', 'noaa_ar_no', 'greenwich', 'mcintosh', 'obs_whole_spot_area',
                       'number_of_spots', 'corr_whole_spot_area', 'distance_from_center', 'position_angle_north',
                       'carrington_longitude', 'latitude', 'central_meridian_dist'])
noaa_df = noaa_df.sort_values(by=['year', 'month', 'day', 't_in_t'])


# In[6]:


lat = noaa_df['latitude'] 
lon = noaa_df['central_meridian_dist']


# In[7]:




noaa_df['y'] = np.sin(np.deg2rad(lat))
noaa_df['x'] = np.sin(np.deg2rad(lon)) * np.cos(np.deg2rad(lat))


# In[79]:


# noaa_df.head(50)


# In[8]:


noaa_df.to_csv('noaa_ars.csv')

