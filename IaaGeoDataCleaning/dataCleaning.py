import pandas as pd
import datetime
import re
import reverse_geocoder as rg
import string
import pycountry as pc

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
    def __init__(self, fileName):
        self.fileName = fileName

        self.flaggedLocations = []  # flagged indexes in data frame
        self.incorrectLog = {'index': [], 'location': [], 'type': []}
        self.correctLog = {'index': [], 'location': [], 'type': []}

        self.entryType = {0: 'correct location data', 1: 'entered (lng, lat)',
                          2: 'entered (-lng, lat)', 3: 'entered (-lng, -lat)',
                          4: 'entered (lng, -lat)', 5: 'entered (-lat, lng)',
                          6: 'entered (-lat, -lng', 7: 'entered (lat, -lng)',
                          -1: 'incorrect location data', -2: 'no latitude and longitude entered',
                          -3: 'country not found/wrong country format'}

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
                country = string.capwords(str(row['Country']).lower())
                location = string.capwords(str(row['Location']).lower())

                dataEntered = self.checkInputLocation(index, country)

                if dataEntered >= 0:
                    enteredLat = float(row['Latitude'])
                    enteredLng = float(row['Longitude'])

                    result = self.validateCoordinates(enteredLat, enteredLng, country)

                    self.logEntry(result, index, location, country)
                else:
                    self.logEntry(dataEntered, index, location, country)

            except:
                print("Index: " + str(index) + " no entered coordinates.(Index flagged.) \n")
                self.flaggedLocations.append(index)
                self.incorrectLog['location'].append((location, country))
                self.incorrectLog['index'].append(index)
                self.incorrectLog['type'].append(' coords NA')

        self.logResults()

    def checkInputLocation(self, index, country):
        lat = self.tobeValidatedLocation.loc[index, 'Latitude']
        lng = self.tobeValidatedLocation.loc[index, 'Longitude']
        try:
            pc.countries.lookup(country)
            print("Passed pycountry")
            if pd.isnull(lat) or pd.isnull(lng):
                return -2
            elif lat == 0 and lng == 0:
                return -2
            return 0
        except LookupError:
            print("lookup")
            try:
                self.countryCodes[country]
                print("passed dictionary")
                if pd.isnull(lat) or pd.isnull(lng):
                    return -2
                elif lat == 0 and lng == 0:
                    return -2
                return 0
            except KeyError:
                print("no country")
                return -3

    def validateCoordinates(self, lat, lng, countryName):

        countryCode = pc.countries.lookup(countryName).alpha_2

        possibleCoords = [(lat, lng), (lng, lat), (-lng, lat), (-lng, -lat),
                          (lng, -lat), (-lat, lng), (-lat, -lng), (lat, -lng)]

        for i in range(len(possibleCoords)):
            matchedCountryCode = rg.get(possibleCoords[i], mode=1)['cc']
            if countryCode == matchedCountryCode:
                return i
            else:
                box = [c.bbox for c in cbb.country_subunits_by_iso_code(countryCode)]
                # formatted lon1, lat1, lon2, lat2 for box
                if not (box[0][0] < lng and box[0][1] < lat and box[0][2] > lng and box[0][3] > lat):
                    return i
        return -1

    def logEntry(self, type, index, location, country):
        if type >= 0:
            self.correctLog['location'].append((location, country))
            self.correctLog['index'].append(index)
            self.correctLog['type'].append(' ' + self.entryType[type])
        else:
            print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
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
# sr = validator.checkInputLocation(1137)
# print(sr)
validator.run()