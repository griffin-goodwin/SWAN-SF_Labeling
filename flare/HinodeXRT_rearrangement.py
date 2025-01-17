import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

def fix_timestamps(ds, format=None):
    if format is None:
        ds_fixed = pd.to_datetime(ds, format="%Y%m%d_%H%M%S")
    else:
        ds_fixed = pd.to_datetime(ds, format=format)
    return ds_fixed

def fix_locations(hdf):
    lat = pd.to_numeric(hdf['loc1'].str.strip().str.slice(start=0, stop=3).str.replace('N', '').str.replace('S', '-'))
    lon = pd.to_numeric(hdf['loc1'].str.strip().str.slice(start=3, stop=6).str.replace('W', '').str.replace('E', '-'))
    hdf['fl_lat'] = lat
    hdf['fl_lon'] = lon
    hdf['ar_location'] = 'POINT(' + lon.astype(str) + ' ' + lat.astype(str) + ')'
    return hdf

def get_hinode_flare_dataframe(file_path, after=None, before=None):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',', index_col = 'Event number', parse_dates=True)
    
    hinode_timeformat = '%Y/%m%d %H:%M'
    df['end_time'] = fix_timestamps(df['end'], format='%Y-%m-%dT%H:%M:%S')
    df['start_time'] = fix_timestamps(df['start'], format='%Y-%m-%dT%H:%M:%S')
    df['peak_time'] = fix_timestamps(df['peak'], format='%Y-%m-%dT%H:%M:%S')
    df = fix_locations(df)
    # df = append_hpc_coord(df)
    df.rename(columns={'X':'x_hpc', 'Y':'y_hpc'}, inplace=True)
    df = df[['start_time', 'peak_time', 'end_time', 'goes_class', 'noaa_active_region', 'ar_location', 'fl_lat', 'fl_lon', 'x_hpc', 'y_hpc']]
    return df


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
    edate = x['start_time']
    c = SkyCoord(lon*u.deg, lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=edate)
    c_hpc = c.transform_to(frames.Helioprojective)
    return c_hpc.Tx.arcsec #tx

def ycoord_transformer(x):
    lon = x['fl_lon']
    lat = x['fl_lat']
    edate = x['start_time']
    c = SkyCoord(lon*u.deg, lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=edate)
    c_hpc = c.transform_to(frames.Helioprojective)
    return c_hpc.Ty.arcsec #Ty



def main():
    hinode_path = '/home/baydin2/workspace/flarepredictiondata/flare_reading/datain/Hinode/xrt_flarecat.csv'
    # file obtained from https://xrt.cfa.harvard.edu/flare_catalog/xrt_flarecat.csv
    hdf = get_hinode_flare_dataframe(hinode_path)
    hdf2010_2018 = hdf[hdf['start_time'] > '2010-05-01']

    hdf2010_2018.to_csv('/home/baydin2/workspace/flarepredictiondata/flare_reading/datain/Hinode/Hinode_fromXRT.csv',
               sep='\t')

    hdf.to_csv('/home/baydin2/workspace/flarepredictiondata/flare_reading/datain/Hinode/Hinode_all_fromXRT.csv',
               sep='\t')


if __name__ == "__main__":
	main()



