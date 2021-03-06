from datetime import datetime
import time
import requests

def parse_hydrodata(jdata):
    
    """ 
    Parses json Hydrodata from NWIS webservice
    and formats for D3 charting library. This method handles
    data that may be missing from the request with dummy data
    points. Upon failure, this will return empty data list.

    ARGS: 
        jdata (list of one dictonary) - json object in a list which contains 
        time series data for all sites listed in config.py SITE_IDs.
    
    RETURNS:
        All series data correctly formated for D3.
        This is also a list of python dictonaries.

    """
    all_series_data = []

    gap_threshold = 1800000   # 30 minutes
    increment_ms = 900000     # 15 minutes

    if jdata is not None:
        for site in jdata:
            site_name = site['sourceInfo']['siteName']
            site_id = site['sourceInfo']['siteCode'][0]['value']
            timezone = site['sourceInfo']['timeZoneInfo']['defaultTimeZone']['zoneAbbreviation']
            prev_date_ms = None

            # Fill data for this series
            for obj in site['values'][0]['value']:
                value = obj['value']
                dt = obj['dateTime']
                date = dt.split('T')[0]
                t = dt.split('T')[1].split('.')[0]
                # reformat datetime for python datetime #
                dt = datetime.strptime(date + ' ' + t, '%Y-%m-%d %H:%M:%S')
                # Convert to milliseconds for use with d3 x axis format
                dt_ms = time.mktime(dt.timetuple()) * 1000
                # handle missing data
                if prev_date_ms:
                    # Size of potential gap in data
                    gap = dt_ms - prev_date_ms
                    """
                      We only consider data to be missing if the gap between adjacent data points 
                      is greater than 30 minutes. All dummy data points will be added in 15 minute increments.
                    """
                    if gap > gap_threshold:
                        num_dummy_points = gap/increment_ms - 1
                        added = 0
                        while added < num_dummy_points:
                            # correct time for this dummy point
                            new_dt_ms = prev_date_ms + (increment_ms * (added + 1))
                            new_dt = str(datetime.fromtimestamp(new_dt_ms / 1000.0))
                            new_d = new_dt.split()[0]
                            new_t = new_dt.split()[1]
                            # covert new_dt_ms to date time here!
                            all_series_data.append({'key': site_id, 'name': site_name, 'date': new_d, "time": new_t,
                                        'timezone': timezone, "time_mili": new_dt_ms, 'value': 'NA'})
                            added += 1
                # append regular (not missing) data
                all_series_data.append({'key': site_id, 'name': site_name, 'date': date, "time": t,
                                        'timezone': timezone, "time_mili": dt_ms, 'value': value})
                prev_date_ms = dt_ms

    return all_series_data


def req_hydrodata(sites, start_date, end_date, url_top):

    """ 
    Requests hydrodata from nwis web service based on passed in parameters.
    Upon request failure, this will return None. 

    ARGS: 
        sites - List of site IDs to request
        start_date - start date for the time series data
        end_date - end date for the time series data
        url_top - URL endpoint for the nwis web service
    
    RETURNS:
        returns a list of one dictonary with the requested data for
        all series from the nwis service
    
    """
    ret = None
    if len(sites) is not 0 and start_date and end_date and url_top:
        # Form URL
        sites = [str(site) for site in sites]
        sites_string = ','.join(sites)
        url =  url_top +'iv/?site=' + sites_string + '&startDT=' + \
              start_date + '&endDT=' + end_date + '&parameterCD=00060&format=json'

        try:
            r = requests.get(url)
            if r.status_code is 200:
                ret = r.json()['value']['timeSeries']
            else:
                print('\n - Bad Request -\n')

        except requests.exceptions.RequestException as e:
            print('\n - Malformed URL - \n')

    else:
        print('\nConfig Varibles Empty\n')
    
    return ret
