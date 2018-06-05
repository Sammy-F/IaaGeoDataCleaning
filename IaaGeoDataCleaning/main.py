import pandas as pd
import datetime
import re
import math
import geocoder

parenNumRegex = re.compile('\(\d\)')
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")
geoID = "thytng"


class GeocodeValidator:
    def __init__(self, geoID, fileName, flagDistance=12.):
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
            self.validateLocation(index, row)
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

    def validateLocation(self, index, row):
        """
        Checks to see whether the latitude and longitude entered corresponds to that of the entered location
        by comparing their distance to the standard distance.
        :param index: the index of the entry
        :param row: the row of the entry
        :return:
        """

        # Creates a tuple containing the location and corresponding country
        country = str(row.loc["Country"]).lower().capitalize()
        location = str(row.loc["Location"]).lower().capitalize()
        geocodeTarget = (location, country)

        # Saves template information to reduce the number of API calls
        if geocodeTarget not in self.geocodedLocations:
            self.reverseGeocode(geocodeTarget)

        # Calculates the distance
        inputLat = float(row.loc['Latitude'])
        inputLng = float(row.loc['Longitude'])
        correctLat = float(self.geocodedLocations[geocodeTarget][0])
        correctLng = float(self.geocodedLocations[geocodeTarget][1])

        distance = self.calculateDistance(inputLat, inputLng, correctLat, correctLng)

        # Compares the distance to the standard flagged distance
        if distance > self.flagDistance:
            print("Index: " + str(index) + " distance between points is too large.(Index flagged.) \n")
            self.flaggedLocations.append(index)  # mark index in original data frame
            self.log['location'].append(geocodeTarget)
            self.log['index'].append(index)
            self.log['type'].append('distance flag')

    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        loggedDF = pd.DataFrame(data=self.log)
        loggedDF.to_csv('validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')
        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

    def reverseGeocode(self, locationTuple):
        """
        Retrieves the latitude and longitude of the location entered in the data, and
        saves that information in the dictionary: (location, country) : (latitude, longitude)
        :param locationTuple: (location, country)
        :return:
        """
        geoInfo = geocoder.geonames(location=locationTuple[0],
                                    country=self.countryCodes[locationTuple[1].lower().capitalize()],
                                    key=self.geoID)
        # TODO: handle errors and exceptions
        # invalid geoIDs (error), invalid locations (no error)
        self.geocodedLocations[locationTuple] = (geoInfo.lat, geoInfo.lng)

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

        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        dlat = lat2 - lat1

        dlng = math.radians(lng2) - math.radians(lng1)

        a = math.pow(math.sin(dlat/2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlng/2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = r * c

        return d

validator = GeocodeValidator(geoID, "test.xlsx")
validator.run()
