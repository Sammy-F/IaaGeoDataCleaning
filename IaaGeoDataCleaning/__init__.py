# coding: utf-8

import pandas as pd
import numpy as np
import datetime
import googlemaps as gm
import re #Regex to remove (num)

parenNumRegex = re.compile('\(\d\)')
mo = parenNumRegex.search('(4)  (5)')
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")
"""
This function has limited data cleaning abilities.
"""
#TODO search working directory for file
#TODO use pickle to save API dictionary
def geocodeValidation(fileName,api_key,flag_distance=12.):
    """
    Args:
        fileName: An excel file or csv file with columns with the name of
                  'Location','Country','Latitude' and 'Longitude'.

        api_key: Google Maps api key.
        flag_distance: Default 12. , this is the distance used to flag a row.
        returns Percentage of corrupt rows.

        This function works by geocoding each row's 'Latitude' and 'Longitude'
        These two values are inputed into the Google Maps api, to get latitude and longitude points.
        These points are then compared against the 'Latitude' and 'Longitude'
        entries in the table and if the distance of the points returned from Google Maps'
        api is greater than the distance_threshold then this data entry is flagged with a 'distance flag'.
        Previously geocode locations are recorded in a dictionary to be used again to save API calls.
        Other cases for flagging include:
          i)  When the Google Maps api does not recognize the inputs given.
              If this is the case, it is recorded in a dictionary with the error 'Could not geocode'.
          ii) When the reason for error is not completely clear it is flagged as a 'generic error'.
          iii) If the status of the api is not 'OK' this is also flagged because sometimes it is not fully clear.
    """
    if fileName.endswith('xlsx'):
        tobe_validated_location = pd.read_excel(fileName)
    else:
        tobe_validated_location = pd.read_csv(fileName)
    #Look for google plot with Latitude and Longitude data
    gmaps = gm.Client(api_key)
    flagged_locations = [] # flagged indexes in dataframe
    geocoded_locations = {}# key :loc,val:(lat,long) reduce API calls
    log = {'index': [] ,'location': [], 'type': []}
    #Getting an address by iterating through each row in the pandas dataframe
    for index,row in tobe_validated_location.iterrows():
        try:
            row['Location'] = parenNumRegex.sub("",row['Location']) #removes (num) can now try API call
            geocode_target = str(row['Country'] + " , " + row['Location'])
        except:
            print("Index: " + str(index) + " had an error.(Index flagged.) \n")
            flagged_locations.append(index)
            log['location'].append(geocode_target)
            log['index'].append(index)
            log['type'].append('generic error')
            continue
        tobe_validated_lat = row['Latitude']
        tobe_validated_lng = row['Longitude']
        if geocode_target not in geocoded_locations.keys():
            geocoded_result = gmaps.geocode(geocode_target)
            if geocoded_result == []:
                print("Index: " + str(index) + " could not be geocoded.(Index flagged.) \n")
                flagged_locations.append(index)
                log['location'].append(geocode_target)
                log['index'].append(index)
                log['type'].append('Could not geocode')
                continue
            #TODO
            #No way to get the status right now
            # elif(geocoded_result[0]['status'] != "OVER_QUERY_LIMIT"):
            #     print('MAXED OUT CALLS, saving flagged so far.')
            #     break
            correct_lat = geocoded_result[0]['geometry']['location']['lat']
            correct_lng = geocoded_result[0]['geometry']['location']['lng']
            geocoded_locations[geocode_target] = (correct_lat,correct_lng)
        distance = gmaps.distance_matrix((tobe_validated_lat,tobe_validated_lng),geocoded_locations[geocode_target])
        top_level_distance_status = str(distance['status'])#needs to be OK to check threshold
        print("distance matrix API Status: " + top_level_distance_status + '\n')
        element_level_distance_status = str(distance['rows'][0]['elements'][0]['status'])
        distance_status = top_level_distance_status == 'OK' and element_level_distance_status == 'OK'
        if(distance_status):
            flag_threshold = distance['rows'][0]['elements'][0]['distance']['value'] * 0.000621371 #convert to miles
            if flag_threshold > flag_distance:
                print("Index: " + str(index) + " distance between points is too large.(Index flagged.) \n")
                flagged_locations.append(index) #mark index in original dataframe
                log['location'].append(geocode_target)
                log['index'].append(index)
                log['type'].append('distance flag')
        else: #status is anything but 'OK'
            flagged_locations.append(index)
            log['location'].append(geocode_target)
            log['index'].append(index)
            log['type'].append('google api status not ok')
    print("Flagged locations are at indicies: " + str(flagged_locations))
    log_df = pd.DataFrame(data=log)
    log_df.to_csv('validation_log_'+str(now)+'.csv', sep=',', encoding='utf-8')
    return len(flagged_locations)/(1e-10+tobe_validated_location.shape[0])
