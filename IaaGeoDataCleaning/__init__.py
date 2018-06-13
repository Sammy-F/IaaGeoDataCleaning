import pandas as pd
import datetime
import string
import re
import pycountry as pc
from os import path

import geopandas as gpd
import numpy as np
import geopy as gp
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

class GeocodeValidator:
    def __init__(self, filePath):
        self.now = datetime.datetime.now()
        self.now = self.now.strftime("%Y-%m-%d")

        self.filePath = filePath

        self.map = gpd.read_file("mapinfo/TM_WORLD_BORDERS-0.3.shp")
        self.pht = gp.Photon(timeout=3)

        self.flaggedLocations = []  # flagged indexes in data frame
        self.incorrectLog = {'index': [], 'location': [], 'type': []}
        self.correctLog = {'index': [], 'location': [], 'type': []}
        self.geocodeLog = {'index': [], 'location': [], 'found_lat': [], 'found_lng': [], 'matched_location': []}


        self.entryType = {0: 'correct location data', 1: 'entered (lng, lat)',
                          2: 'entered (-lng, lat)', 3: 'entered (-lng, -lat)',
                          4: 'entered (lng, -lat)', 5: 'entered (-lat, lng)',
                          6: 'entered (-lat, -lng', 7: 'entered (lat, -lng)',
                          -1: 'incorrect location data', -2: 'no latitude and longitude entered',
                          -3: 'country not found/wrong country format', -4: 'no location entered',
                          -5: 'cannot find coordinates'}

        self.countryCodes = {}
        self.createCountryCodeDict()

        if self.filePath.endswith('xlsx'):
            self.tobeValidatedLocation = pd.read_excel(self.filePath)
        else:
            self.tobeValidatedLocation = pd.read_csv(self.filePath)

    def run(self):
        """
        Iterates through every row of the data and validates the locational information of each entry
        """
        for (index, row) in self.tobeValidatedLocation.iterrows():
            print("Validating " + str(index))
            dataEntered = self.checkInputLocation(index)

            country = string.capwords(str(row['Country']).lower())
            location = string.capwords(str(row['Location']).lower())

            if isinstance(dataEntered, tuple):
                enteredLat = float(row['Latitude'])
                enteredLng = float(row['Longitude'])

                result = self.validateCoordinates(enteredLat, enteredLng, dataEntered[1])

                self.logEntry(result, index, location, country)

            else:
                if dataEntered == -2:
                    coords = self.findCoordinates(location, country)
                    if isinstance(coords, tuple):
                        self.logGeocode(index, location, country, coords[0][0], coords[0][1], coords[1])
                    else:
                        self.logEntry(coords, index, location, country)

                else:
                    self.logEntry(dataEntered, index, location, country)

        self.logResults()
        percent = len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])
        print(percent)
        return percent

    def checkInputLocation(self, index):
        """
        For an entry at a given index, attempt to validate if the input country
        are correct for the given lat/lon and return the code to log the outcome
        :param index:
        :return: log type code
        """
        if pd.isnull(self.tobeValidatedLocation.loc[index, 'Location']) or pd.isnull(self.tobeValidatedLocation.loc[index, 'Country']):
            return -4

        country = string.capwords(str(self.tobeValidatedLocation.loc[index, 'Country']))
        lat = self.tobeValidatedLocation.loc[index, 'Latitude']
        lng = self.tobeValidatedLocation.loc[index, 'Longitude']

        try:
            # Looking up with pycountry
            countryCode = pc.countries.lookup(country).alpha_2
            if pd.isnull(lat) or pd.isnull(lng):
                return -2
            elif lat == 0 and lng == 0:
                return -2
            return (0, countryCode)

        except LookupError:
            try:
                # Looking up in the dictionary
                countryCode = self.countryCodes[country]
                if pd.isnull(lat) or pd.isnull(lng):
                    return -2
                elif lat == 0 and lng == 0:
                    return -2
                return (0, countryCode)

            except KeyError:
                # Checking for the correct format
                formatted = self.findFormattedName(country)
                if formatted == False:
                    return -3
                else:
                    countryCode = pc.countries.lookup(formatted).alpha_2
                    if pd.isnull(lat) or pd.isnull(lng):
                        return -2
                    elif lat == 0 and lng == 0:
                        return -2
                    return (0, countryCode)

    def findFormattedName(self, alternativeName):
        """
        If a country name is invalid, assume it is an alternative name
        and attempt to find and return the official one
        :param alternativeName:
        """

        finder = nh.NameHandler()
        return finder.findName(alternativeName)

    def validateCoordinates(self, lat, lng, countryCode):
        """
        Use geocoding to identify valid/invalid coordinates
        :param lat: entry's input latitude
        :param lng: entry's input longitude
        :param countryCode: determined country code for entry's input country
        :return: log type code
        """

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

    def findCoordinates(self, location, country):
        try:
            matches = self.pht.geocode(location + " " + country, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matchedCountry = match.address.split()[-1]
                    if re.search(country, matchedCountry, re.IGNORECASE):
                        return ((match.latitude, match.longitude), match.address)
            matches = self.pht.geocode(location, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matchedCountry = match.address.split()[-1]
                    if re.search(country, matchedCountry, re.IGNORECASE):
                        return ((match.latitude, match.longitude), match.address)
            return -5
        except:
            return -5

    def logEntry(self, type, index, location, country):
        """
        Generate an entry in one of the log dictionaries
        based on the input parameters
        :param type: error type, see entryType dict for details
        :param index: index of entry
        :param location: entry location
        :param country: entry country
        """
        if type >= 0:
            self.correctLog['index'].append(index)
            self.correctLog['location'].append((location, country))
            self.correctLog['type'].append(' ' + self.entryType[type])
        else:
            self.flaggedLocations.append(index)
            self.incorrectLog['index'].append(index)
            self.incorrectLog['location'].append((location, country))
            self.incorrectLog['type'].append(' ' + self.entryType[type])

    def logGeocode(self, index, location, country, latitude, longitude, foundLocation):
        self.geocodeLog['index'].append(index)
        self.geocodeLog['location'].append((location, country))
        self.geocodeLog['found_lat'].append(latitude)
        self.geocodeLog['found_lng'].append(longitude)
        self.geocodeLog['matched_location'].append(foundLocation)


    def logResults(self):
        """
        Generate two .csv log files from correct and incorrect
        log dictionaries.
        """
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        incorrectEntriesDF = pd.DataFrame(data=self.incorrectLog)
        incorrectEntriesDF.to_csv('incorrect_validation_log_' + str(self.now) + '.csv', sep=',', encoding='utf-8')

        correctEntriesDF = pd.DataFrame(data=self.correctLog)
        correctEntriesDF.to_csv('correct_validation_log_' + str(self.now) + '.csv', sep=',', encoding='utf-8')

        geocodeDF = pd.DataFrame(data=self.geocodeLog)
        geocodeDF.to_csv('geocode_log_' + str(self.now) + '.csv', sep=',', encoding='utf-8')

        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

    def createCountryCodeDict(self):
        """
        Creates a dictionary whose (key, value) pairs are a country and its country code
        in order to utilize the geocoder API calls.
        """
        countriesData = pd.read_csv("countryInfo.txt", delimiter="\t")

        for (index, row) in countriesData.iterrows():
            countryCode = str(row.loc["ISO"])
            country = str(row.loc["Country"])
            self.countryCodes[country] = countryCode

validator = GeocodeValidator('/Users/thytnguyen/Desktop/tblLocation.xlsx')
validator.run()