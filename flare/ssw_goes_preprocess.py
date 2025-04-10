from builtins import print

import numpy as np
import pandas as pd
import flr_utils as utils


SSW_FLARE_PATH = './aia_ssw_flares_scraped_2010.csv'
#HINODE_FLARE_PATH = './datain/Hinode/Hinode_may2010_dec2018.csv'
GOES_FLARE_PATH = './goes_flares_2025.csv'
#NO_LOC_FL_PATH = './datain/goes_fl_no_loc.csv'
#GOES_FL_OUT_PATH = '/datain/goes_fl_wloc.csv'


def initialize():
	prepare_ssw_flares()
	prepare_goes_flares()


def prepare_goes_flares():
	goesf = utils.get_goes_flare_dataframe(GOES_FLARE_PATH)
	goesf = utils.fix_flare_locations(goesf)
	goesf = utils.append_hpc_coord(goesf)
	goesf.to_csv("goes_hpc.csv")


# hdf = utils.get_hinode_flare_dataframe(HINODE_FLARE_PATH)

def prepare_ssw_flares():
	sswf = utils.get_ssw_flare_dataframe(SSW_FLARE_PATH)
	sswf = utils.fix_ssw_flare_locations(sswf)
	print(sswf)
	sswf = utils.append_hpc_coord(sswf)
	sswf.to_csv("ssw_hpc2.csv")


def main():
	initialize()
	print('DONE!')


if __name__ == "__main__":
	main()