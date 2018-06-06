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
            try:
                row['Location'] = parenNumRegex.sub("", row['Location'])  # removes (num) can now try API call
                country = string.capwords(str(row["Country"]).lower())
                location = string.capwords(str(row["Location"]).lower())

                lat = float(row['Latitude'])
                long = float(row['Longitude'])

                print(lat)
                print(long)

                nearestLocation = rg.get((lat, long), mode=1)

                nearestCountry = location['cc']
                print(country)

                try:
                    self.validateLocation(index, row, actualCountry=nearestCountry, targetLoc=(location, country))
                except KeyError:
                    print("Index: " + str(index) + " lat/lon don't correspond \n")
                    self.flaggedLocations.append(index)  # mark index in original data frame
                    self.log['location'].append((location, country))
                    self.log['index'].append(index)
                    self.log['type'].append('distance flag')
            except TypeError:
                print("Index: " + str(index) + " missing country \n")
                self.flaggedLocations.append(index)  # mark index in original data frame
                self.log['location'].append((location, country))
                self.log['index'].append(index)
                self.log['type'].append('distance flag')

        self.logResults()

    def validateLocation(self, index, row, actualCountry, targetLoc):
        """
        Checks to see whether the latitude and longitude entered corresponds to that of the entered location
        by comparing their countries
        :param index: the index of the entry
        :param row: the row of the entry
        :return:
        """
        if not self.countryCodes[row['Country']] == actualCountry:

            # self.handleBadCountry(index, row, actualCountry, targetLoc)

            print("Index: " + str(index) + " lat/lon don't correspond \n")
            self.flaggedLocations.append(index)  # mark index in original data frame
            self.log['location'].append(targetLoc)
            self.log['index'].append(index)
            self.log['type'].append('distance flag')

    def isGood(self, index, row, actualCountry, targetLoc):

        if not self.countryCodes[row['Country']] == actualCountry:
            self.handleBadCountry(index, row, actualCountry, targetLoc)
            return False
        else:
            return True


    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        loggedDF = pd.DataFrame(data=self.log)
        loggedDF.to_csv('validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')
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
            self.countryCodes[country.upper()] = countryCode

        print(self.countryCodes)

    def handleBadCountry(self, index, row, actualCountry, targetLoc):
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
        checkLat = row['Latitude']
        checkLng = row['Longitude']
        helper = 0


        # if not self.isGood(index, row, actualCountry, targetLoc):
        #     # (flipped lat - lng)
        #     checkLat = checkLat * -1
        #     checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
        #     if checkDist > self.flagDistance:
        #         # (lng - flipped lat)
        #         checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
        #         if checkDist > self.flagDistance:
        #             # (flipped lat - flipped lng)
        #             checkLng = checkLng * -1
        #             checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
        #             if checkDist > self.flagDistance:
        #                 # (flipped lng - flipped lat)
        #                 checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
        #                 if checkDist > self.flagDistance:
        #                     # (lat - flipped lng)
        #                     checkLat = checkLat * -1
        #                     checkDist = self.calculateDistance(checkLat, checkLng, correctLat, correctLng)
        #                     if checkDist > self.flagDistance:
        #                         # (flipped lng - lat)
        #                         checkDist = self.calculateDistance(checkLng, checkLat, correctLat, correctLng)
        #                         if checkDist > self.flagDistance:
        #                             return False

        return True

validator1 = GeocodeValidator("NaNtblLocations.xlsx")
validator1.run()

