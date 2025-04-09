import pandas as pd
import urllib.request
import lxml.html
from lxml import etree, html
from urllib.error import URLError


flare_items = []
broken_flares = []


def scrape(start, end):
    ssw_base_url = "https://www.lmsal.com/solarsoft/latest_events_archive.html"
    daterange = pd.date_range(start, end)
    flr_url_list = fetch_daily_flare_links(ssw_base_url, daterange)
    print(flr_url_list)

    if len(flr_url_list) > 0:
        print("Downloading " + str(len(flr_url_list)) + " flare items for the date " + date_link_suffix + " from URL:" + ssw_url)
        scrape_flare_items(flr_url_list)


def fetch_daily_flare_links(ssw_url, date_range):
    try:
        with urllib.request.urlopen(ssw_url) as connection:
            dom = lxml.html.fromstring(connection.read())

        # Extract all href links
        all_links = dom.xpath('//a/@href')
        # Filter links based on date range
        filtered_links = []
        for link in all_links:
            try:
            # Extract date from link format
                if '/' in link and len(link.split('/')) > 2:
                    date_part = link.split('/')[2].split('_')[2]
                    dt = pd.to_datetime(date_part, format='%Y%m%d')
                    if dt in date_range:
                        filtered_links.append(link)
            except (IndexError, ValueError):
            # Skip links that don't match the expected format
                pass
        
        print(f"Found {len(filtered_links)} links in date range")
        flr_url_list = []
        for link in filtered_links:
            with urllib.request.urlopen("https://www.lmsal.com/solarsoft/"+str(link)) as connection:
                sub_dom = lxml.html.fromstring(connection.read())
                for sub_link in sub_dom.xpath('//a/@href'):
                    if 'gev' in sub_link:
                        # Create full URL by adding base URL if it's a relative link
                        flr_url_list.append("https://www.lmsal.com/solarsoft/"+str(link).replace('index.html', '') + sub_link)
        return flr_url_list

    except URLError as urle:
        print(urle.code, ' for ', ssw_url)
        if urle.code == 404:
            print('\tNo flare reports for ' + ssw_url)
        return []


def scrape_flare_items(flr_url_list):
    for fl_url in flr_url_list:

        try:
            with urllib.request.urlopen(fl_url) as fl_connection:
                page = html.parse(fl_connection)

                theader = page.xpath('//tr/th//text()')
                tcontent = page.xpath('//tr/td//text()')

                indices_of_previous_tags=[i for i, x in enumerate(tcontent) if x == 'Previous']
                #delete 6 tags from content (previous, current, next, id1, id2, id3)
                for index in sorted(indices_of_previous_tags, reverse=True):
                    del tcontent[index:index+6]

                # fixing header for NOAA AR number
                for i in range(len(theader)):
                    if str(theader[i]).startswith('Derived Position'):
                        theader[i] = 'Derived Position'
                    theader[i] = theader[i].strip()
                theader.append('NOAA_AR')

                if len(tcontent) >= 13: # this is when you got SECCHI or EIT flares
                    tcontent = tcontent[-8:]
                    theader = theader[-8:]
                    if tcontent[0].startswith('gev'):
                        tcontent = tcontent[1:]
                    if not tcontent[1].startswith('gev'):
                        tcontent = tcontent[1:]

                if len(tcontent) == 7:
                    tcontent.append('')

                if len(tcontent) == 8 and len(theader) == 8: #this is supposedly my standard
                    # print(theader, tcontent)
                    flare_item = {}
                    for i in range(len(theader)):
                        flare_item[theader[i]] = tcontent[i]

                    #fixing their stupid date conventions, because standards mean nothing
                    fl_date = flare_item['Start'].split(' ')[0]
                    flare_item['Peak'] = fl_date  + ' ' + flare_item['Peak']
                    flare_item['Stop'] = fl_date  + ' ' + flare_item['Stop']

                    flare_items.append(flare_item)
                else:
                    print("There was a problem (a potential broken flare item) for URL: " + fl_url)
                    broken_flares.append([theader, tcontent, fl_url])
        except urllib.error.HTTPError as http_e:
            print(http_e.code, ' for ', fl_url)


def fix_peak_time(ssw_fl):
    for index, row in ssw_fl.iterrows():
        if row['start_time'] > row['peak_time']:
            ssw_fl.loc[index, 'peak_time'] = row['peak_time'] + pd.DateOffset(days=1)

    return ssw_fl


def fix_end_time(ssw_fl):
    for index, row in ssw_fl.iterrows():
        if row['peak_time'] > row['end_time']:
            ssw_fl.loc[index, 'end_time'] = row['end_time'] + pd.DateOffset(days=1)

    return ssw_fl


def post_process_ssw_flares(ssw_fl):
    ssw_fl['NOAA_AR'] = ssw_fl['NOAA_AR'].apply(lambda x: x.strip(' ( ').rstrip(' ) '))
    ssw_fl['peak_time'] = pd.to_datetime(ssw_fl['Peak'], infer_datetime_format=True)
    ssw_fl['start_time'] = pd.to_datetime(ssw_fl['Start'], infer_datetime_format=True)
    ssw_fl['end_time'] = pd.to_datetime(ssw_fl['Stop'], infer_datetime_format=True)
    ssw_fl = fix_peak_time(ssw_fl)
    ssw_fl = fix_end_time(ssw_fl)

    # TODO: Instead of checking for "*" in the entire column, each cell should be checked!
    if '*' in ssw_fl['Derived Position']:
        print('Potential Error:\n\t{}'.format(ssw_fl['Derived Position']))
        ssw_fl['goes_location'] = 'N/A'
    else:
        lat = pd.to_numeric(
            ssw_fl['Derived Position'].str.strip().str.slice(start=0, stop=3).str.replace('N', '').str.replace('S', '-'), errors='coerce')
        lon = pd.to_numeric(
            ssw_fl['Derived Position'].str.strip().str.slice(start=3, stop=6).str.replace('W', '').str.replace('E', '-'), errors='coerce')
        ssw_fl['goes_location'] = 'POINT(' + lon.astype(str) + ' ' + lat.astype(str) + ')'
    ssw_fl['NOAA_AR'] = pd.to_numeric(ssw_fl['NOAA_AR'], errors='coerce')
    ssw_fl['NOAA_AR'].fillna(value=0, inplace=True)
    ssw_fl['NOAA_AR'] = ssw_fl['NOAA_AR'].astype(int)
    ssw_fl = ssw_fl.drop(columns=['Derived Position', 'Event#', 'Peak', 'Start', 'Stop'])
    ssw_fl = ssw_fl.rename(columns={'GOES Class': 'goes_class', 'NOAA_AR': 'noaa_active_region'})
    ssw_fl = ssw_fl.set_index('EName')
    return ssw_fl


def main():
    start = '2010-01-01'
    end = '2010-01-31'
    scrape(start, end)

    ssw_fl = pd.DataFrame(flare_items)
    print(ssw_fl)
    ssw_fl = post_process_ssw_flares(ssw_fl)

    # reorder columns for consistency
    ssw_fl = ssw_fl[['start_time', 'peak_time', 'end_time', 'goes_class', 'goes_location', 'noaa_active_region']]

    out_filename_1 = 'aia_ssw_flares_scraped_{}.csv'.format(start[0:4])
    out_filename_2 = 'broken_aia_flares_{}.csv'.format(start[0:4])
    with open(out_filename_1, 'a') as f:  # write without a header, we can add later
        ssw_fl.to_csv(f, header=False)

    pd.DataFrame(broken_flares).to_csv(out_filename_2)

    print('DONE!')


if __name__ == "__main__":
    main()



