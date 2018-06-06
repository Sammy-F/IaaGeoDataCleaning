import pandas as pd
import datetime
import re
import reverse_geocoder as rg
import string

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


class GeocodeValidator:
    def __init__(self, fileName):
        self.fileName = fileName

        self.flaggedLocations = []  # flagged indexes in data frame
        self.log = {'index': [], 'location': [], 'type': [], 'comment': []}

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
                    if nearestLocation['cc'] != self.countryCodes[country] and inputCoordinates != (0, 0):
                        self.handleBadCountryy(index, countryName=country, recordedLat=row.loc["Latitude"],
                                               recordedLong=row.loc["Longitude"], location=location)
                        # print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
                        # self.flaggedLocations.append(index)
                        # self.log['location'].append((location, country))
                        # self.log['index'].append(index)
                        # self.log['type'].append(' mismatched country')
                        # self.log['comment'].append(' ' + nearestLocation['cc'])
                    elif inputCoordinates == (0, 0):
                        print("Index: " + str(index) + " Longitude and latitude missing \n")
                        self.flaggedLocations.append(index)
                        self.log['location'].append((location, country))
                        self.log['index'].append(index)
                        self.log['type'].append(' invalid long/lat')
                        self.log['comment'].append(' ' + nearestLocation['cc'])
                except KeyError:
                    print("Index: " + str(index) + " incorrect country format.(Index flagged.) \n")
                    self.flaggedLocations.append(index)
                    self.log['location'].append((location, country))
                    self.log['index'].append(index)
                    self.log['type'].append(' wrong format')
                    self.log['comment'].append(' ' + country)

            except (TypeError, IndexError) as error:
                print("Index: " + str(index) + " no entered coordinates.(Index flagged.) \n")
                self.flaggedLocations.append(index)
                self.log['location'].append((location, country))
                self.log['index'].append(index)
                self.log['type'].append(' coords NA')
                self.log['comment'].append(' NA')

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

        coordinates = [(recordedLong, recordedLat), (-recordedLong, recordedLat), (-recordedLong, -recordedLat),
                       (recordedLong, -recordedLat), (-recordedLat, recordedLong), (-recordedLat, -recordedLong),
                       (recordedLat, -recordedLong)]

        for coordinate in coordinates:
            code = rg.get(coordinate, mode=1)
            if code['cc'] == recordedCode:
                return True
        print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
        self.flaggedLocations.append(index)
        self.log['location'].append((location, countryName))
        self.log['index'].append(index)
        self.log['type'].append(' mismatched country')
        self.log['comment'].append(' ' + code['cc'])
        return False

validator2 = GeocodeValidator("NaNtblLocations.xlsx")
validator2.run()

