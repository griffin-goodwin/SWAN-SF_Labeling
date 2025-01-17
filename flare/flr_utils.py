
from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd

import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

def get_noaa_ar_df(file_path):
    noaa_ar = pd.read_csv(file_path)
    noaa_ar = noaa_ar.rename(columns={'Unnamed: 0': 'id'})
    noaa_ar = noaa_ar.set_index("id")
    noaa_ar['year'] = noaa_ar['year'].astype(str)
    noaa_ar['month'] = noaa_ar['month'].astype(str)
    noaa_ar['day'] = noaa_ar['day'].astype(str)
    noaa_ar['ar_time'] = pd.to_datetime(noaa_ar[['year', 'month', 'day']].apply(lambda x: '-'.join(x), axis=1))
    return noaa_ar


def get_aia_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter='\t', parse_dates=True)
    df['end_time'] = fix_timestamps(df['end_time'], format='%Y-%m-%dT%H:%M:%S')
    df['start_time'] = fix_timestamps(df['start_time'], format='%Y-%m-%dT%H:%M:%S')
    df['peak_time'] = fix_timestamps(df['peak_time'], format='%Y-%m-%dT%H:%M:%S')
    return df

def get_ssw_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',', index_col='id', parse_dates=True)
    df['end_time'] = fix_timestamps(df['end_time'], format='%Y-%m-%d %H:%M:%S')
    df['start_time'] = fix_timestamps(df['start_time'], format='%Y-%m-%d %H:%M:%S')
    df['peak_time'] = fix_timestamps(df['peak_time'], format='%Y-%m-%d %H:%M:%S')
    df['noaa_active_region'] = df['noaa_active_region'] + 10000
    df.loc[ (df['noaa_active_region']==10000) , 'noaa_active_region'] = np.nan

    df = df[ df['ssw_location'] != 'POINT(nan nan)']

    return df

def get_hinode_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',', index_col='Event_number', parse_dates=True)
    df['end_time'] = fix_timestamps(df['end_time'], format='%Y-%m-%d %H:%M:%S')
    df['start_time'] = fix_timestamps(df['start_time'], format='%Y-%m-%d %H:%M:%S')
    df['peak_time'] = fix_timestamps(df['peak_time'], format='%Y-%m-%d %H:%M:%S')
    return df


def get_goes_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',', parse_dates=True)
    df['end_time'] = fix_timestamps(df['end_time'], format='%Y-%m-%d %H:%M:%S')
    df['start_time'] = fix_timestamps(df['start_time'], format='%Y-%m-%d %H:%M:%S')
    df['peak_time'] = fix_timestamps(df['peak_time'], format='%Y-%m-%d %H:%M:%S')
    return df


def fix_timestamps(ds, format=None):
    if format is None:
        ds_fixed = pd.to_datetime(ds, format="%Y%m%d_%H%M%S")
    else:
        ds_fixed = pd.to_datetime(ds, format=format)
    return ds_fixed


def remove_duplicates_from_goes_flares(goes_df):
    # remove all totally duplicated rows from goes df
    duplicates = goes_df.duplicated(
        subset=['start_time', 'end_time', 'peak_time', 'noaa_active_region', 'goes_class', 'goes_location'],
        keep='first')
    duplicated = goes_df[duplicates]
    goes_df = goes_df[~duplicates]
    return goes_df, duplicated


def remove_duplicates_from_aia_flares(aia_df):
    duplicates = aia_df.duplicated(
        subset=['start_time', 'end_time', 'peak_time', 'noaa_active_region', 'goes_class', 'goes_location'],
        keep='first')
    duplicated = aia_df[duplicates]
    aia_df = aia_df[~duplicates]
    return aia_df, duplicated


def get_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',',
                     parse_dates=['start_time', 'end_time', 'peak_time', 'peak_time_aia', 'peak_time_goes'])
    new_columns = df.columns.values
    new_columns[0] = 'flare_id'
    df.columns = new_columns
    df = df.set_index('flare_id')

    # return fix_noaa_ar_numbers( pd.read_csv(file_path, delimiter='\t', parse_dates=True) )
    df = fix_end_times(fix_peak_times(fix_flare_locations(fix_noaa_ar_numbers(df))))
    # df = df[ df['goes_class'] > 'C9.9' ]
    return df


def fix_peak_times(df):
    """ Gets the flare dataframe and consolidates the peaktimes from aia and goes using the following strategy
        if the is a valid peak time from goes, it uses that. If not it uses the aia one"""

    # for each null (nan) peak time, get the peak time from goes
    df.loc[pd.isnull(df['peak_time']), 'peak_time'] = df.loc[pd.isnull(df['peak_time']), 'peak_time_goes']

    # for each null (nan) peak time, get the peak time from aia
    df.loc[pd.isnull(df['peak_time']), 'peak_time'] = df.loc[pd.isnull(df['peak_time']), 'peak_time_aia']

    return df


def fix_end_times(df):
    """ Gets the flare dataframe and consolidates the end times from aia and goes using the following strategy
        if the is a valid peak time from goes, it uses that. If not it uses the aia one"""

    # for each null (nan) peak time, get the peak time from goes
    df.loc[pd.isnull(df['end_time']), 'end_time'] = df.loc[pd.isnull(df['end_time']), 'end_time_y']

    # for each null (nan) peak time, get the peak time from aia
    df.loc[pd.isnull(df['end_time']), 'end_time'] = df.loc[pd.isnull(df['end_time']), 'end_time_x']

    return df


def fix_noaa_ar_numbers(df):
    """ Gets the flare dataframe and consolidates the noaa ar numbers from aia and goes using the following strategy
        if the is a valid goes active region, that is not 0, it uses that. If not it uses a valid aia number"""

    # set goes noaa numbers as primary source
    df['noaa_active_region'] = df['noaa_active_region_goes']
    # if noaa ar no from goes is zero, set it to NaN
    df.loc[df['noaa_active_region'] == 0, 'noaa_active_region'] = np.nan

    # for each null (nan) noaa ar number, get the ar number from aia
    df.loc[pd.isnull(df['noaa_active_region']), 'noaa_active_region'] = \
        df.loc[pd.isnull(df['noaa_active_region']), 'noaa_active_region_aia']
    # for each noaa ar number that is still zero, set it to nan
    df.loc[df['noaa_active_region'] == 0, 'noaa_active_region'] = np.nan

    # print len(df['noaa_active_region'].unique())
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
    df = df.apply(reformat_locations, axis=1)

    # print df.to_csv('flares_flares.csv')
    return df

def fix_ssw_flare_locations(df):
    """ Gets the SSW flare dataframe and consolidates the flare locations from aia and goes using the following strategy
        if there is a valid aia location, that is not NaN, it uses that. If not it uses the goes location if valid"""

    # set goes location as primary source
    df['fl_location'] = df['ssw_location']



    # for each goes location that is still invalid --(0, 0), set it to nan
    df.loc[df['fl_location'] == '(0, 0)', 'fl_location'] = np.nan
    # create two new columns fl_lat and fl_lon for latitude and longitude
    df = df.reindex(columns=np.append(df.columns.values, ['fl_lat', 'fl_lon']))
    # extract the locations from either aia or goes location strings
    df = df.apply(reformat_locations, axis=1)

    # print df.to_csv('flares_flares.csv')
    return df



def reformat_locations(row):
    gloc = row['fl_location']
    # print pd.isnull(gloc),gloc
    if pd.isnull(gloc):
        row['fl_lon'] = np.nan
        row['fl_lat'] = np.nan
    elif gloc.startswith('POINT'):
        row['fl_lon'] = float(gloc.strip('POINT(').strip(')').split(' ')[0])
        row['fl_lat'] = float(gloc.strip('POINT(').strip(')').split(' ')[1])
    elif gloc.startswith('('):
        row['fl_lon'] = float(gloc.strip('(').strip(')').split(', ')[0])
        row['fl_lat'] = float(gloc.strip('(').strip(')').split(', ')[1])
    else:
        row['fl_lon'] = np.nan
        row['fl_lat'] = np.nan
    return row


def transform_fl_lat_lon(fdf):
    lat = fdf['fl_lat']
    lon = fdf['fl_lon']
    fdf['y'] = np.sin(np.deg2rad(lat))
    fdf['x'] = np.sin(np.deg2rad(lon)) * np.cos(np.deg2rad(lat))
    return fdf


def append_hpc_coord(fdf):
    fdf['x_hpc'] = fdf.apply(xcoord_transformer, axis=1) # x coordinates of hpc
    fdf['y_hpc'] = fdf.apply(ycoord_transformer, axis=1) # y coordinates of hpc
    return fdf

def xcoord_transformer(x):
    lon = x['fl_lon']
    lat = x['fl_lat']
    event_time = x['start_time']
    c = SkyCoord(lon*u.deg, lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=event_time)
    c_hpc = c.transform_to(frames.Helioprojective)
    return c_hpc.Tx.arcsec #tx

def ycoord_transformer(x):
    lon = x['fl_lon']
    lat = x['fl_lat']
    event_time = x['start_time']
    c = SkyCoord(lon*u.deg, lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=event_time)
    c_hpc = c.transform_to(frames.Helioprojective)
    return c_hpc.Ty.arcsec #Ty

