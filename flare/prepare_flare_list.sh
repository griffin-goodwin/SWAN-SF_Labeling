#!/bin/bash

#Scrape SSW reports
echo Scraping SSW flare reports...
python ssw_latest_event_scraper.py

echo Pre-processing scraped SSW flare reports...
python ssw_goes_preprocess.py

# #Download the XRT flares from https://xrt.cfa.harvard.edu/flare_catalog/xrt_flarecat.csv and pre-process them
echo Pre-processing XRT-Hinode flare reports...
python HinodeXRT_rearrangement.py


# echo SSW, Hinode and GOES flare reports are ready...
# echo Augmenting NOAA AR locations...
# python noaa_ar_loc_augmentation.py >> _out/noaa_ar_loc_augmentation_out

# echo Cross-checking GOES flares with SSW and Hinode-XRT
# python flare_cross_checking.py >> _out/flare_cross_checking_out