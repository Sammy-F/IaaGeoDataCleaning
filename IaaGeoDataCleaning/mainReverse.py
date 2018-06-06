import pandas as pd
import datetime
import re
import math
from pandas import ExcelWriter
import string
import reverse_geocoder as rg

"""
GeocodeValidator allows the user to perform reverse geocoding
on a .xlsx or .csv to ensure that input locations correspond to
the correct latitude and longitude. If not, then basic data cleaning
is performed to check for human error.

Created by Jonathan Scott

Modified by: Samantha Fritsche, Thy Nguyen 6/5/2018
"""

# TODO: handle exceptions when making API calls

parenNumRegex = re.compile('\(\d\)')
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")
geoID = "thytng"


class GeocodeValidator:
    def __init__(self, fileName, flagDistance=12.):
        self.geoID = geoID
        self.fileName = fileName
        self.flagDistance = flagDistance

        self.flaggedLocations = []  # flagged indexes in dataframe
        self.geocodedLocations = {}  # key :loc,val:(lat,long) reduce API calls
        self.log = {'index': [], 'location': [], 'type': []}

        self.countryCodes = {}
        self.createCountryCodeDict()

        if fileName.endswith('xlsx'):
            self.tobeValidatedLocation = pd.read_excel(fileName)
        else:
            self.tobeValidatedLocation = pd.read_csv(fileName)

    def run(self):
        """
        Iterates through every row of the data and validates the locational information of each entry
        :return:
        """

        for (index, row) in self.tobeValidatedLocation.iterrows():
            row['Location'] = parenNumRegex.sub("", row['Location'])  # removes (num) can now try API call
            country = string.capwords(str(row["Country"]).lower())
            location = string.capwords(str(row["Location"]).lower())
            geocodeTarget = (location, country)

            lat = float(row['Latitude'])
            long = float(row['Longitude'])

            print(lat)
            print(long)

            location = rg.search((lat, long), mode=1)[0]

            country = location['cc']
            print(country)

            self.validateLocation(index, row, actualCountry=country, targetLoc=location)

        self.logResults()

        # g = geocoder.geonames("Minneapolis", key=self.geoID)
        # if g.ok:
        #     for (index, row) in self.tobeValidatedLocation.iterrows():
        #         try:
        #             row['Location'] = parenNumRegex.sub("", row['Location'])  # removes (num) can now try API call
        #             country = string.capwords(str(row["Country"]).lower())
        #             location = string.capwords(str(row["Location"]).lower())
        #             geocodeTarget = (location, country)
        #
        #             # Saves template information to reduce the number of API calls
        #             if geocodeTarget not in self.geocodedLocations:
        #                 coded = self.reverseGeocode(index, geocodeTarget)
        #                 if coded:
        #                     if not row['Latitude'] == 0 and not row['Longitude'] == 0:
        #                         self.validateLocation(index, row, geocodeTarget)
        #                     else:
        #                         print("Index: " + str(index) + " is missing latitude/longitude.(Index flagged.) \n")
        #                         self.flaggedLocations.append(index)
        #                         self.log['location'].append(geocodeTarget)
        #                         self.log['index'].append(index)
        #                         self.log['type'].append('missing latitude and longitude')
        #                 else:
        #                     continue
        #
        #         except:
        #             print("Index: " + str(index) + " had an error.(Index flagged.) \n")
        #             self.flaggedLocations.append(index)
        #             self.log['location'].append(geocodeTarget)
        #             self.log['index'].append(index)
        #             self.log['type'].append('generic error')
        #             continue
        #
        #     self.logResults()
        # else:
        #     print("Invalid ID")

    def validateLocation(self, index, row, actualCountry, targetLoc):
        """
        Checks to see whether the latitude and longitude entered corresponds to that of the entered location
        by comparing their countries
        :param index: the index of the entry
        :param row: the row of the entry
        :return:
        """
        if not self.countryCodes[row['Country']] == actualCountry:
            print("Index: " + str(index) + " lat/lon don't correspond \n")
            self.flaggedLocations.append(index)  # mark index in original data frame
            self.log['location'].append(targetLoc)
            self.log['index'].append(index)
            self.log['type'].append('distance flag')


    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        loggedDF = pd.DataFrame(data=self.log)
        loggedDF.to_csv('validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')
        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

    # def reverseGeocode(self, index, locationTuple):
    #     """
    #     Retrieves the latitude and longitude of the location entered in the data, and
    #     saves that information in the dictionary: (location, country) : (latitude, longitude)
    #     :param locationTuple: (location, country)
    #     :return: whether the location entered was valid for geocoding
    #     """
    #     try :
    #         geoInfo = geocoder.geonames(location=locationTuple[0],
    #                                     key=self.geoID)
    #         # Handles cases where (location, country) does not return a result
    #         if not geoInfo.ok:
    #             print("Index: " + str(index) + " location and country not found.(Index flagged.) \n")
    #             self.flaggedLocations.append(index)
    #             self.log['location'].append(locationTuple)
    #             self.log['index'].append(index)
    #             self.log['type'].append('location not found')
    #             return False
    #         self.geocodedLocations[locationTuple] = (geoInfo.lat, geoInfo.lng)
    #         return True
    #     except KeyError:
    #         print("Index: " + str(index) + " country not found.(Index flagged.) \n")
    #         self.flaggedLocations.append(index)
    #         self.log['location'].append(locationTuple)
    #         self.log['index'].append(index)
    #         self.log['type'].append('country not found')
    #         return False

    # def calculateDistance(self, lat1, lng1, lat2, lng2):
    #     """
    #     Uses the haversine formula to calculate the distance between two points given their latitudes and longitudes.
    #     :param lat1:
    #     :param lng1:
    #     :param lat2:
    #     :param lng2:
    #     :return: the distance (miles)
    #     """
    #     r = 3959
    #
    #     lat1 = math.radians(lat1)
    #     lat2 = math.radians(lat2)
    #     dlat = lat2 - lat1
    #
    #     dlng = math.radians(lng2) - math.radians(lng1)
    #
    #     a = math.pow(math.sin(dlat/2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlng/2), 2)
    #     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    #     d = r * c
    #
    #     return d

    def createCountryCodeDict(self):
        """
        Creates a dictionary whose (key, value) pairs are a country and its country code
        in order to utilize the geocoder API calls.
        :return:
        """
        countriesData = pd.read_csv("countryInfo.txt", delimiter="\t")

        for (index, row) in countriesData.iterrows():
            countryCode = str(row.loc["ISO"])
            country = str(row.loc["Country"])
            self.countryCodes[country.upper()] = countryCode

        print(self.countryCodes)

    def handleBadDistance(self, inputLat, inputLng, correctLat, correctLng):
        """
        If the calculated distance is greater than the flag distance,
        perform operations to check for human input errors.

        Errors checked for: Flipped long/lat, +/-
        :param inputLat:
        :param inputLng:
        :param correctLat:
        :param correctLng:
        :return:
        """
        checkLat = inputLat
        checkLng = inputLng

        # (lng - lat)
        checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)

        if checkDist > self.flagDistance:
            # (flipped lat - lng)
            checkLat = checkLat * -1
            checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
            if checkDist > self.flagDistance:
                # (lng - flipped lat)
                checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
                if checkDist > self.flagDistance:
                    # (flipped lat - flipped lng)
                    checkLng = checkLng * -1
                    checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
                    if checkDist > self.flagDistance:
                        # (flipped lng - flipped lat)
                        checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
                        if checkDist > self.flagDistance:
                            # (lat - flipped lng)
                            checkLat = checkLat * -1
                            checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
                            if checkDist > self.flagDistance:
                                # (flipped lng - lat)
                                checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
                                if checkDist > self.flagDistance:
                                    return False

        return True

validator1 = GeocodeValidator("NaNtblLocations.xlsx")
validator1.run()

