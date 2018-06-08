import pandas as pd
import datetime
import re
import reverse_geocoder as rg
import string
import math

import country_bounding_boxes as cbb

"""
GeocodeValidator allows the user to perform reverse geocoding
on a .xlsx or .csv to ensure that input locations correspond to
the correct latitude and longitude. If not, then basic data cleaning
is performed to check for human error.

Created by Jonathan Scott

Modified by: Samantha Fritsche, Thy Nguyen 6/5/2018
"""

parenNumRegex = re.compile('\(\d\)')
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")


class GeocodeValidator:
    def __init__(self, fileName, flagDistance=12.):
        self.fileName = fileName
        self.flagDistance = flagDistance

        self.flaggedLocations = []  # flagged indexes in data frame
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
            try:
                row['Location'] = parenNumRegex.sub("", row['Location'])
                country = string.capwords(str(row["Country"]).lower())
                location = string.capwords(str(row["Location"]).lower())

                inputCoordinates = (row.loc["Latitude"], row.loc["Longitude"])
                nearestLocation = rg.get(inputCoordinates, mode=1)

                try:
                    if inputCoordinates == (0, 0):
                        print("Index: " + str(index) + " Longitude and latitude missing \n")
                        self.flaggedLocations.append(index)
                        self.log['location'].append((location, country))
                        self.log['index'].append(index)
                        self.log['type'].append(' invalid long/lat')

                    else:
                        self.handleBadCountryy(index, countryName=country, recordedLat=row.loc["Latitude"],
                                               recordedLong=row.loc["Longitude"], location=location)

                except KeyError:
                    print("Index: " + str(index) + " incorrect country format.(Index flagged.) \n")
                    self.flaggedLocations.append(index)
                    self.log['location'].append((location, country))
                    self.log['index'].append(index)
                    self.log['type'].append(' wrong format')

            except (TypeError, IndexError) as error:

                print("Index: " + str(index) + " no entered coordinates.(Index flagged.) \n")
                self.flaggedLocations.append(index)
                self.log['location'].append((location, country))
                self.log['index'].append(index)
                self.log['type'].append(' coords NA')

        self.logResults()

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
            self.countryCodes[country] = countryCode

    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        loggedDF = pd.DataFrame(data=self.log)
        loggedDF.to_csv('validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')
        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

    def handleBadCountryy(self, index, recordedLat, recordedLong, countryName, location):

        recordedCode = self.countryCodes[countryName]

        coordinates = [(recordedLat, recordedLong), (recordedLong, recordedLat), (-recordedLong, recordedLat), (-recordedLong, -recordedLat),
                       (recordedLong, -recordedLat), (-recordedLat, recordedLong), (-recordedLat, -recordedLong),
                       (recordedLat, -recordedLong)]

        for coordinate in coordinates:
            correctMatch = self.validate(coordinate, recordedCode)
            if correctMatch:
                return True
        print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
        self.flaggedLocations.append(index)
        self.log['location'].append((location, countryName))
        self.log['index'].append(index)
        self.log['type'].append(' mismatched country')
        return False

    def validate(self, coord, countryCode):
        """
        Validate whether a location is valid based off of its distance from its nearest location.
        :param coord:
        :param countryCode:
        :return:
        """
        returnedLocation = rg.get(coord, mode=1)
        if returnedLocation['cc'] != countryCode:
            box = [c.bbox for c in cbb.country_subunits_by_iso_code(countryCode)]
            # formatted lon1, lat1, lon2, lat2 for box
            # coord formatted (lat, lon)
            if not (box[0][0] < coord[1] and box[0][1] < coord[0] and box[0][2] > coord[1] and box[0][3] > coord[0]):
                return False
        return True

    def calculateDistance(self, lat1, lng1, lat2, lng2):
        """
        Uses the haversine formula to calculate the distance between two points given their latitudes and longitudes.
        :param lat1:
        :param lng1:
        :param lat2:
        :param lng2:
        :return: the distance (miles)
        """
        r = 3959

        lat1 = float(lat1)
        lat2 = float(lat2)
        lng1 = float(lng1)
        lng2 = float(lng2)
        lat1 = math.radians(float(lat1))
        lat2 = math.radians(float(lat2))

        dlat = lat2 - lat1
        dlng = math.radians(lng2) - math.radians(lng1)

        a = math.pow(math.sin(dlat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlng / 2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = r * c

        return d

validator2 = GeocodeValidator("NaNtblLocations.xlsx")
validator2.run()

