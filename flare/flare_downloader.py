import sys
import time
from datetime import datetime
from urllib.error import HTTPError

import pandas as pd
import sunpy.instr.goes
from dateutil.relativedelta import *
from sunpy.net import hek
from sunpy.time import TimeRange

startdate = datetime(2015, 1, 1)
enddate = datetime(2019, 1, 1)

# DAY_DELTA = 20
ofile_suffix = '_2015.csv'


# def daterange(start_date, end_date):
#     for n in range(int((end_date - start_date).days / DAY_DELTA )):
#         yield start_date + timedelta(n * DAY_DELTA )

def get_monthly_range(start_date):
    return TimeRange(start_date, start_date + relativedelta(months=+1))


def get_daily_range(start_date):
    return TimeRange(start_date, start_date + relativedelta(days=+1))


def download_goes_flares(start_date, end_date, ofile):
    # ofile = './datain/goesFlares2018.txt'
    # start_date = datetime(2018, 1, 1)
    # end_date = datetime(2018, 12, 31)
    # tr = get_monthly_range(start_date)
    listofresults = []
    temp_start = start_date
    while temp_start < end_date:
        print(type(temp_start))
        tr = get_monthly_range(temp_start)

        print('Downloading flares from ', tr.start, 'to', tr.end)
        temp = None
        try:
            temp = (sunpy.instr.goes.get_goes_event_list(tr))
        except HTTPError as http_error:
            max_tries = 1
            while True:
                print(("There is an HTTP Error trying again after 5 seconds--", str(http_error)))
                import time
                time.sleep(5)
                temp = (sunpy.instr.goes.get_goes_event_list(tr))

                if max_tries == 0:
                    sys.exit()
                else:
                    max_tries = max_tries - 1

        listofresults = listofresults + temp
        print(('\tGOES Downloaded {0} flares'.format(len(temp))))
        # update temp_start
        temp_start = tr.end.datetime

    print(('Length of total results: ', len(listofresults)))

    df = pd.DataFrame(listofresults)
    df.to_csv(ofile, sep='\t', index=False)


def download_aia_flares(start_date, end_date, ofile):
    client = hek.HEKClient()
    event_type = 'FL'
    FRM = 'SSW Latest Events'
    INSTRUMENT = 'AIA'

    failed_download_ranges = []
    listofresults = []
    columns = ['event_date', 'start_time', 'end_time', 'goes_class', 'goes_location', 'noaa_active_region', 'peak_time']

    temp_start = start_date
    while temp_start < end_date:
        tr = get_monthly_range(temp_start)

        print('Downloading flares from ', tr.start, 'to', tr.end)
        # temp = None
        results = []

        try:
            results = client.search(hek.attrs.Time(tr.start, tr.end), hek.attrs.EventType(event_type),
                                    hek.attrs.FRM.Name == FRM, hek.attrs.OBS.Instrument == INSTRUMENT)
        except HTTPError as http_error:
            print('I could not download for ', tr.start, 'to', tr.end)
            failed_download_ranges.append(tr)
            # max_tries = 3
            # while True:
            #     print("There is an HTTP Error trying again after 5 seconds--", str(http_error))
            #     import time
            #     time.sleep(5)
            #     results = client.search(hek.attrs.Time(tr.start, tr.end), hek.attrs.EventType(event_type),
            #                         hek.attrs.FRM.Name == FRM, hek.attrs.OBS.Instrument == INSTRUMENT)
            #

        print(('\tAIA Downloaded {0} flares'.format(len(results))))
        for result in results:
            # print result
            listofresults.append([result['event_starttime'].split('T')[0], result['event_starttime'],
                                  result['event_endtime'], result['fl_goescls'], result['hgs_coord'],
                                  result['ar_noaanum'], result['event_peaktime']])

        # update temp_start
        temp_start = tr.end

    print(('Length of total results: ', len(listofresults)))
    print(('Failed download ranges\n', str(failed_download_ranges)))
    df = pd.DataFrame(listofresults, columns=columns)
    df.to_csv(ofile, sep='\t', index=False)


def download_fldet_flares(start_date, end_date, ofile):
    client = hek.HEKClient()
    event_type = 'FL'
    # FRM = 'SSW Latest Events'
    INSTRUMENT = 'AIA'

    failed_download_ranges = []
    listofresults = []
    columns = ['event_date', 'start_time', 'end_time', 'goes_class', 'goes_location',
               'noaa_active_region', 'peak_time', 'frm_name', 'fl_peakflux', 'fl_peakfluxunit']

    temp_start = start_date
    while temp_start < end_date:
        tr = get_daily_range(temp_start)

        print('Downloading flares from ', tr.start, 'to', tr.end)
        # temp = None
        results = []

        try:
            results = client.search(hek.attrs.Time(tr.start, tr.end), hek.attrs.EventType(event_type),
                                    # hek.attrs.FRM.Name == FRM,
                                    hek.attrs.FRM.HumanFlag == 'false',
                                    hek.attrs.OBS.Instrument == INSTRUMENT)
        except HTTPError as http_error:
            print('I could not download for ', tr.start, 'to', tr.end)
            failed_download_ranges.append(tr)
            # max_tries = 3
            # while True:
            #     print("There is an HTTP Error trying again after 5 seconds--", str(http_error))
            #     import time
            #     time.sleep(5)
            #     results = client.search(hek.attrs.Time(tr.start, tr.end), hek.attrs.EventType(event_type),
            #                         hek.attrs.FRM.Name == FRM, hek.attrs.OBS.Instrument == INSTRUMENT)
            #

        print(('\tAIA Downloaded {0} flares'.format(len(results))))
        for result in results:
            print(result['hgs_coord'], result['frm_name'], result['event_probability'], \
                  result['fl_peakflux'], result['fl_peakfluxunit'], result['frm_humanflag'])
            listofresults.append([result['event_starttime'].split('T')[0], result['event_starttime'],
                                  result['event_endtime'], result['fl_goescls'], result['hgs_coord'],
                                  result['ar_noaanum'], result['event_peaktime'], result['frm_name'],
                                  result['fl_peakflux'], result['fl_peakfluxunit']])
        # print result.keys()
        # update temp_start
        temp_start = tr.end

    print(('Length of total results: ', len(listofresults)))
    print(('Failed download ranges\n', str(failed_download_ranges)))
    df = pd.DataFrame(listofresults, columns=columns)
    df.to_csv(ofile, sep='\t', index=False)


def run_main():
    start = time.time()
    download_goes_flares(startdate, enddate, './datain/goesFlares_from' + ofile_suffix)
    end = time.time()
    print("Finished downloading GOES flares in: %.2f minutes." % ((end - start) / 60.0))

    # start = time.time()
    # download_aia_flares(startdate, enddate, './datain/aiaFlares' + ofile_suffix)
    # end = time.time()
    #
    # print("Finished downloading AIA flares in: %.2f minutes." % ((end - start) / 60.0))

    # start = time.time()
    # download_fldet_flares(startdate, enddate, './datain/aiaFlares_nofrm' + ofile_suffix)
    # end = time.time()
    # print(("Finished downloading AIA no frm flares in: %.2f minutes." % ((end - start) / 60.0)))


if __name__ == "__main__":
    run_main()
