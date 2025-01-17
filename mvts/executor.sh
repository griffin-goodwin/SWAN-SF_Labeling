#!/bin/bash
echo Executing location integration...
/home/baydin2/anaconda3/bin/python sharp_location_integration.py >> _out/sharp_location_integration_out

#echo Adding NOAA AR column...
#/home/baydin2/anaconda3/bin/python add_NOAA_AR_column.py >> _out/add_NOAA_AR_column_out

echo Executing MVTS time filler...
/home/baydin2/anaconda3/bin/python ar_mvts_time_filler.py >> _out/ar_mvts_filler_out

echo Adding TMFI column...
/home/baydin2/anaconda3/bin/python add_TMFI_column.py >> _out/add_TMFI_column_out

echo Integrating flare history series...
/home/baydin2/anaconda3/bin/python flare_hist_creator.py >> _out/flare_hist_creator_out

echo Integrating XR data series...
/home/baydin2/anaconda3/bin/python add_goes_xr.py >> _out/add_goes_xr_out

echo Filtering out columns
/home/baydin2/anaconda3/bin/python filter_columns.py >> _out/filter_columns_out

#/home/baydin2/anaconda3/bin/python custom_date_cleaning.py >> _out/custom_date_cleaning_out
