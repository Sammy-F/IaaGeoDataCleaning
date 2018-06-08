import pandas as pd
import datetime
import string
import pycountry as pc

import geopandas as gpd
import numpy as np

import nameHandler as nh

# import country_bounding_boxes as cbb
from shapely.geometry import Point

"""
GeocodeValidator allows the user to perform reverse geocoding
on a .xlsx or .csv to ensure that input locations correspond to
the correct latitude and longitude. If not, then basic data cleaning
is performed to check for human error.

Created by Jonathan Scott

Modified by: Samantha Fritsche, Thy Nguyen 6/7/2018

Some code by Martin Valgur @ StackOverflow was adapted to create this program.
See his original at: https://gis.stackexchange.com/questions/212796/get-lat-lon-extent-of-country-from-name-using-python

Note that some borders used are disputed
"""

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")


class GeocodeValidator:
    def __init__(self, fileName):
        self.map = gpd.read_file("mapinfo/TM_WORLD_BORDERS-0.3.shp")
        self.fileName = fileName

        self.flaggedLocations = []  # flagged indexes in data frame
        self.incorrectLog = {'index': [], 'location': [], 'type': []}
        self.correctLog = {'index': [], 'location': [], 'type': []}

        self.entryType = {0: 'correct location data', 1: 'entered (lng, lat)',
                          2: 'entered (-lng, lat)', 3: 'entered (-lng, -lat)',
                          4: 'entered (lng, -lat)', 5: 'entered (-lat, lng)',
                          6: 'entered (-lat, -lng', 7: 'entered (lat, -lng)',
                          -1: 'incorrect location data', -2: 'no latitude and longitude entered',
                          -3: 'country not found/wrong country format', -4: 'no location entered'}

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
            dataEntered = self.checkInputLocation(index)

            country = string.capwords(str(row['Country']).lower())
            location = string.capwords(str(row['Location']).lower())

            try:
                if dataEntered[0] >= 0:
                    enteredLat = float(row['Latitude'])
                    enteredLng = float(row['Longitude'])

                    result = self.validateCoordinates(enteredLat, enteredLng, dataEntered[1])

                    self.logEntry(result, index, location, country)
                else:
                    self.logEntry(dataEntered, index, location, country)

            except TypeError:
                if dataEntered >= 0:
                    enteredLat = float(row['Latitude'])
                    enteredLng = float(row['Longitude'])

                    result = self.validateCoordinates(enteredLat, enteredLng, country)

                    self.logEntry(result, index, location, country)
                else:
                    self.logEntry(dataEntered, index, location, country)

        self.logResults()

    def checkInputLocation(self, index):
        if pd.isnull(self.tobeValidatedLocation.loc[index, 'Location']) or pd.isnull(self.tobeValidatedLocation.loc[index, 'Country']):
            return -4

        country = string.capwords(str(self.tobeValidatedLocation.loc[index, 'Country']))
        lat = self.tobeValidatedLocation.loc[index, 'Latitude']
        lng = self.tobeValidatedLocation.loc[index, 'Longitude']

        try:
            countryCode = pc.countries.lookup(country).alpha_2
            print("Passed pycountry")
            if pd.isnull(lat) or pd.isnull(lng):
                return -2
            elif lat == 0 and lng == 0:
                return -2
            return (0, countryCode)

        except LookupError:
            try:
                countryCode = self.countryCodes[country]
                print("passed dictionary")
                if pd.isnull(lat) or pd.isnull(lng):
                    return -2
                elif lat == 0 and lng == 0:
                    return -2
                return (0, countryCode)

            except KeyError:
                formatted = self.findFormattedName(country)
                print(formatted)
                if formatted == False:
                    print("no country")
                    return -3
                else:
                    countryCode = pc.countries.lookup(formatted).alpha_2
                    print("foundalternative")
                    return (0, countryCode)

    def findFormattedName(self, alternativeName):

        finder = nh.NameHandler()
        return finder.findName(alternativeName)

    def validateCoordinates(self, lat, lng, countryCode):

        lat = float(lat)
        lng = float(lng)

        possibleCoords = [(lat, lng), (lng, lat), (-lng, lat), (-lng, -lat),
                          (lng, -lat), (-lat, lng), (-lat, -lng), (lat, -lng)]

        for i in range(len(possibleCoords)):
            try:
                shapePoint = np.array([possibleCoords[i][1], possibleCoords[i][0]])
                point = Point(shapePoint)
                filter = self.map['geometry'].contains(point)
                mLoc = self.map.loc[filter, 'ISO2']
                foundCountry = mLoc.iloc[0]

                if (countryCode == foundCountry):
                    return i

            except IndexError:
                continue

        return -1

    def logEntry(self, type, index, location, country):
        if type >= 0:
            self.correctLog['location'].append((location, country))
            self.correctLog['index'].append(index)
            self.correctLog['type'].append(' ' + self.entryType[type])
        else:
            self.flaggedLocations.append(index)
            self.incorrectLog['location'].append((location, country))
            self.incorrectLog['index'].append(index)
            self.incorrectLog['type'].append(' ' + self.entryType[type])

    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        incorrectEntriesDF = pd.DataFrame(data=self.incorrectLog)
        incorrectEntriesDF.to_csv('incorrect_validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')

        correctEntriesDF = pd.DataFrame(data=self.correctLog)
        correctEntriesDF.to_csv('correct_validation_lol_' + str(now) + '.csv', sep=',', encoding='utf-8')

        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

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


validator = GeocodeValidator("NaNtblLocations.xlsx")
validator.run()

# Formatted long, lat
# mPoint = np.array((6.1833333970000695, 11.21666718))
# mPoint = Point(mPoint)
# map = gpd.read_file("D:\IaaGeoDataCleaning\IaaGeoDataCleaning\mapinfo\TM_WORLD_BORDERS_SIMPL-0.3.shp")
# filter = map['geometry'].contains(mPoint)
# mLoc = map.loc[filter, 'NAME']
# print(mLoc.iloc[0])
#
# zaire = validator.checkInputLocation(1005)
# print(zaire)