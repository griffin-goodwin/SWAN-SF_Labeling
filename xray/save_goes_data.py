#! /bin/python
# use this script for downloading GOES X-ray flux data using 'wget' utility and python
# replace URL field with the current URL to the ngdc/swpc download page
# Author: Sushant S. Mahajan
# May 18, 2018

# Our period of concern is during the lifetime of SDO (starting May 2010). Two main GOES have been operational during this time:
# GOES 14 : May 2010 to May 2018, still operational
# GOES 15 : Sept 2010 to May 2018, still operational


# 1. Download data for GOES 14:

# filestr="g14_xrs_2s_20100501_20100501.csv"
# URL="https://satdat.ngdc.noaa.gov/sem/goes/data/full/2010/05/goes14/csv/"
#
# yy_start = 2010
# mm_start = 05
#
# yy_end = 2018
# mm_end = 05
#
# # Days in months during the year
# dom=np.array([31,28,31,30,31,30,31,31,30,31,30,31])
#
# for yy in range (yy_start,yy_end+1):
# 	if yy == yy_start:
# 		mm0 = mm_start
# 	else:
# 		mm0 = 1
#
# 	if yy == yy_end:
# 		mm1 = mm_end+1
# 	else:
# 		mm1 = 13
#
# 	# Adjust for a leap day in February
# 	if yy%4 == 0:
# 		dom[1]=29
# 	else:
# 		dom[1]=28
#
# 	for mm in range (mm0,mm1):
# 		for dd in range (1,dom[mm-1]+1):
# 			# ammend the filename
# 			filename=filestr[0:11]+str(yy)+str(mm).zfill(2)+str(dd).zfill(2)+"_"+str(yy)+str(mm).zfill(2)+str(dd).zfill(2)+".csv"
# 			# create a wget command
# 			command="wget -Nrkpl 0 "+URL[0:48]+str(yy)+"/"+str(mm).zfill(2)+URL[55:]+filename
# 			#print(command)
# 			# Call bash
# 			subprocess.call(command,shell=True)

     
# wget flags and their functions
# -r = recursive: follows the links
# -k = changes links adresses to their local file adress
# -p = downloads images
# -l = recursion level. 0 for infinite.

import subprocess

# 2. Download data for GOES 15: (started operations in Sept, 2010)
import numpy as np

filestr="g15_xrs_2s_20100501_20100501.csv"
URL="https://satdat.ngdc.noaa.gov/sem/goes/data/full/2010/05/goes15/csv/"

yy_start = 2011
mm_start = 9

yy_end = 2018
mm_end = 5

# Days in months during the year
dom=np.array([31,28,31,30,31,30,31,31,30,31,30,31])	

for yy in range (yy_start,yy_end+1):
	if yy == yy_start:
		mm0 = mm_start
	else:
		mm0 = 1

	if yy == yy_end:
		mm1 = mm_end+1
	else:
		mm1 = 13
	
	# Adjust for a leap day in February
	if yy%4 == 0:
		dom[1]=29
	else:
		dom[1]=28

	for mm in range (mm0,mm1):
		for dd in range (1,dom[mm-1]+1):
			# ammend the filename
			filename=filestr[0:11]+str(yy)+str(mm).zfill(2)+str(dd).zfill(2)+"_"+str(yy)+str(mm).zfill(2)+str(dd).zfill(2)+".csv"
			# create a wget command
			command="wget -Nrkpl 0 "+URL[0:48]+str(yy)+"/"+str(mm).zfill(2)+URL[55:]+filename
			#print(command)
			# Call bash
			subprocess.call(command,shell=True)

     
# wget flags and their functions
# -r = recursive: follows the links
# -k = changes links adresses to their local file adress
# -p = downloads images
# -l = recursion level. 0 for infinite.
