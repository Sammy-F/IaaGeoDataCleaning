import pandas as pd
import datetime
import string
import re
import pycountry as pc
import math
import geopandas as gpd
import numpy as np
import geopy as gp

# import country_bounding_boxes as cbb
from shapely.geometry import Point

# TODO: Document code

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
    def __init__(self):
        self.map = gpd.read_file("/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/mapinfo/TM_WORLD_BORDERS-0.3.shp")
        self.pht = gp.Photon(timeout=3)
        self.dbi = DatabaseInitializer()

        self.entryType = {0: 'correct location data', 1: 'entered (lat, -lng)',
                          2: 'entered (-lat, lng)', 3: 'entered (-lat, -lng)',
                          4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
                          6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)',
                          8: 'no lat/lng entered - geocoded location',
                          -1: 'incorrect location data/cannot find coordinates',
                          -2: 'no latitude and longitude entered',
                          -5: 'no location/country entered / wrong country format'}

        self.countryCodes = {}
        self.createCountryCodeDict()

    def verifyInfo(self, location=None, country=None, inpLat=None, inpLng=None):
        """
        Reads in data for a single location and verifies its information/checks for missing data.
        :param location:
        :param country:
        :param inpLat:
        :param inpLng:
        :return: the type of entry and the entry's information as a dictionary
        """
        locationInfo = self.formatInformation(location, country, inpLat, inpLng)
        checkedRow = self.checkInput(locationInfo)
        # tuple (inp_type, dict)
        inpType = checkedRow[0]
        locationInfo = checkedRow[1]

        # Location or country is not entered
        if inpType == -5:
            locationInfo['Type'] = self.entryType[inpType]
            return inpType, locationInfo

        # Everything is entered
        elif inpType == 0:
            # Validate entered coordinates
            checkedRowCoords = self.verifyCoordinates(locationInfo)

            coordType = checkedRowCoords[0]
            locationInfo = checkedRowCoords[1]

            # Attempt to find actual coordinates if the ones entered are not correct
            if coordType == -1:
                findAltCoords = self.geocodeCoordinates(locationInfo)
                coordType = findAltCoords[0]
                locationInfo = findAltCoords[1]

        # Attempt to find coordinates if not entered
        else:
            findAltCoords = self.geocodeCoordinates(locationInfo)
            coordType = findAltCoords[0]
            locationInfo = findAltCoords[1]

        locationInfo['Type'] = self.entryType[coordType]
        return coordType, locationInfo

    def formatInformation(self, location, country, latitude, longitude):
        """
        Formats the entered data in a standardized dictionary.
        :param location:
        :param country:
        :param latitude:
        :param longitude:
        :return:
        """
        return {'Location': location, 'Country': country, 'Latitude': latitude, 'Longitude': longitude,
                'Recorded_Lat': None, 'Recorded_Lng': None, 'Address': None, 'Country_Code': None}

    def checkInput(self, locationDict):
        """
        Checks to see if all the necessary fields are entered.
        :param locationDict:
        :return: a tuple containing 2 values:
        the type of entry as an integer and the (altered) location dictionary.
        """
        if pd.isnull(locationDict['Location']) or pd.isnull(locationDict['Country']):
            return -5, locationDict

        locationDict['Location'] = string.capwords(locationDict['Location'])
        locationDict['Country'] = string.capwords(locationDict['Country'])

        # Looking up with pycountry
        try:
            locationDict['Country_Code'] = pc.countries.lookup(locationDict['Country']).alpha_2
        except LookupError:
            # Looking up in the dictionary
            try:
                locationDict['Country_Code'] = self.countryCodes[locationDict['Country']]
            except KeyError:
                # Checking for alternative name format
                altCountryName = self.findFormattedName(locationDict['Country'])
                if not altCountryName:
                    return -5, locationDict
                else:
                    locationDict['Country'] = altCountryName
                    locationDict['Country_Code'] = pc.countries.lookup(altCountryName).alpha_2

        # Checking if lat/lng were entered
        if (pd.isnull(locationDict['Latitude']) or pd.isnull(locationDict['Longitude'])) or (locationDict['Latitude'] == 0 and locationDict['Longitude'] == 0):
            return -2, locationDict

        return 0, locationDict

    def verifyCoordinates(self, locationDict):
        """
        Uses a shapefile to determine whether the entered coordinates fall within the borders of the country entered.
        :param locationDict:
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """
        lat = locationDict['Latitude']
        lng = locationDict['Longitude']

        locationDict['Address'] = locationDict['Location'] + ', ' + locationDict['Country']

        possibleCoords = [(lat, lng), (lat, -lng), (-lat, lng), (-lat, -lng),
                          (lng, lat), (lng, -lat), (-lng, lat), (-lng, -lat)]

        for i in range(len(possibleCoords)):
            try:
                shapePoint = np.array([possibleCoords[i][1], possibleCoords[i][0]])
                point = Point(shapePoint)
                filter = self.map['geometry'].contains(point)
                mLoc = self.map.loc[filter, 'ISO2']
                foundCountry = mLoc.iloc[0]

                if locationDict['Country_Code'] == foundCountry:
                    locationDict['Recorded_Lat'] = possibleCoords[i][0]
                    locationDict['Recorded_Lng'] = possibleCoords[i][1]
                    return i, locationDict

            except IndexError:
                continue

        return -1, locationDict

    def geocodeCoordinates(self, locationDict):
        """
        Finds the coordinates of a location based on the entered location and country.
        :param locationDict:
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """
        location = locationDict['Location']
        country = locationDict['Country']

        try:
            matches = self.pht.geocode(location + " " + country, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matchedCountry = match.address.split(',')[-1]
                    if re.search(country, matchedCountry, re.IGNORECASE):
                        locationDict['Recorded_Lat'] = match.latitude
                        locationDict['Recorded_Lng'] = match.longitude
                        locationDict['Address'] = match.address
                        return 8, locationDict

            matches = self.pht.geocode(location, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matchedCountry = match.address.split()[-1]
                    if re.search(country, matchedCountry, re.IGNORECASE):
                        locationDict['Recorded_Lat'] = match.latitude
                        locationDict['Recorded_Lng'] = match.longitude
                        locationDict['Address'] = match.address
                        return 8, locationDict

            return -1, locationDict

        except:
            return -1, locationDict

    def queryAllFields(self, location, country, latitude, longitude,
                       filePath='/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/verified_data_2018-06-15.csv'):
        """
        Does a full search for entries matching the fields.
        :param location:
        :param country:
        :param latitude:
        :param longitude:
        :param filePath:
        :return: a list of matched rows as dictionaries.
        """
        database = self.dbi.readFile(filePath)
        if database is None:
            return None

        results = []

        locationInfo = self.formatInformation(location, country, latitude, longitude)
        # See whether location is in the database
        # TODO: Reverse contains
        closestDF = database[(database['Location'].str.contains(locationInfo['Location'], case=False, na=False) &
                            database['Country'].str.contains(locationInfo['Country'], case=False, na=False))]
        for (index, row) in closestDF.iterrows():
            if math.isclose(latitude, row['Recorded_Lat'], rel_tol=1e-1) and \
                    math.isclose(longitude, row['Recorded_Lng'], rel_tol=1e-1):
                loc = database.to_dict(orient='records')[index]
                results.append(loc)
        # That location is not yet inputted
        # What about asking for whether any of these locations are a match?
        return results

    def queryByLocation(self, location, country,
                        filePath='/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/verified_data_2018-06-15.csv'):
        """
        Finds all rows with the matching location and country.
        Can find locations that contain the query but not the other way around (sadly).
        :param location:
        :param country:
        :param filePath:
        :return: a list of matched rows as dictionaries.
        """
        database = self.dbi.readFile(filePath)
        if database is None:
            return None

        results = []

        locationInfo = self.formatInformation(location, country, None, None)

        closestDF = database[(database['Location'].str.contains(locationInfo['Location'], case=False, na=False) &
                              database['Country'].str.contains(locationInfo['Country'], case=False, na=False))]

        for (index, row) in closestDF.iterrows():
            loc = database.to_dict(orient='records')[index]
            results.append(loc)

        return results

    def queryByCoordinates(self, latitude, longitude,
                           filePath='/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/verified_data_2018-06-15.csv'):
        """
        Finds all rows with the matching latitude and longitude.
        :param latitude:
        :param longitude:
        :param filePath:
        :return: a list of matched rows as dictionaries.
        """
        database = self.dbi.readFile(filePath)
        if database is None:
            return None

        results = []

        closestDF = database.ix[(database['Recorded_Lat'] - latitude).abs().argsort()[:10]]
        for (index, row) in closestDF.iterrows():
            if math.isclose(latitude, row['Recorded_Lat'], rel_tol=1e-1) and \
                    math.isclose(longitude, row['Recorded_Lng'], rel_tol=1e-1):
                loc = database.to_dict(orient='records')[index]
                results.append(loc)
        return results

    def addLocation(self, location=None, country=None, latitude=None, longitude=None,
                    filePath='/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/verified_data_2018-06-15.csv'):
        querySearch = []
        if location is not None and country is not None:
            querySearch = self.queryByLocation(location, country, filePath)
        elif (location is None or country is None) and (latitude is not None and longitude is not None):
            querySearch = self.queryByCoordinates(latitude, longitude, filePath)

        if len(querySearch) > 0:
            print('Entry already exists in database.')
            return querySearch

        # Completely new entry
        else:
            verified = self.verifyInfo(location, country, latitude, longitude)
            # Location is valid
            if verified[0] >= 0:
                # Check to see whether it is an entry in the pending database
                queryInPending = self.queryByLocation(verified[1]['Location'], verified[1]['Country'],
                                                      '/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/pending_data_2018-06-15.csv')
                if len(queryInPending) > 0:
                    indices = [row['Index'] for row in queryInPending]
                    indices.sort(key=int)
                    indices.sort(reverse=True)
                    for index in indices:
                        print(index)
                        self.dbi.deleteRowFromDB(index,
                                                 '/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/pending_data_2018-06-15.csv')
                # Add to verified
                newRowDF = pd.DataFrame.from_dict([verified[1]])
                self.dbi.addRowToDB(newRowDF, filePath)
                return verified

    def findFormattedName(self, alternativeName):
        """
        If a country name is invalid, assume it is an alternative name
        and attempt to find and return the official one
        :param alternativeName:
        """
        finder = NameHandler()
        return finder.findName(alternativeName)

    def createCountryCodeDict(self):
        """
        Creates a dictionary whose (key, value) pairs are a country and its country code
        in order to utilize the geocoder API calls.
        """
        countriesData = pd.read_csv("/Users/thytnguyen/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/countryInfo.txt", delimiter="\t")

        for (index, row) in countriesData.iterrows():
            countryCode = str(row.loc["ISO"])
            country = str(row.loc["Country"])
            self.countryCodes[country] = countryCode

class DatabaseInitializer:
    def createNewDatabase(self, filePath):
        self.now = datetime.datetime.now()
        self.now = self.now.strftime("%Y-%m-%d")

        self.flaggedLocations = []  # flagged indexes in data frame
        self.verified = {'Type': [], 'Location': [], 'Country': [], 'Latitude': [], 'Longitude': [],
                         'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [],
                         'Country_Code': []}
        self.pending = {'Type': [], 'Location': [], 'Country': [], 'Latitude': [], 'Longitude': [],
                        'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [],
                        'Country_Code': []}

        self.verifiedDatabase = 'verified_data_' + str(self.now) + '.csv'
        self.pendingDatabase = 'pending_data_' + str(self.now) + '.csv'

        self.validator = GeocodeValidator()

        self.tobeValidatedLocation = self.readFile(filePath)

        self.run()

    def run(self):
        """
        Iterates through every row of the data and validates the locational information of each entry
        """
        for (index, row) in self.tobeValidatedLocation.iterrows():
            print('Verifying at index ' + str(index))
            location = self.tobeValidatedLocation.loc[index, 'Location']
            country = self.tobeValidatedLocation.loc[index, 'Country']
            latitude = self.tobeValidatedLocation.loc[index, 'Latitude']
            longitude = self.tobeValidatedLocation.loc[index, 'Longitude']

            rowInfo = self.validator.verifyInfo(location, country, latitude, longitude)

            if rowInfo[0] < 0:
                self.flaggedLocations.append(index)
                self.logEntry(self.pending, rowInfo[1])
            else:
                self.logEntry(self.verified, rowInfo[1])

        self.exportResults()

    def getVerifiedLog(self):
        return self.verified

    def getPendingLog(self):
        return self.pending

    def getIncorrectPercent(self):
        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])

    def getVerifiedFile(self):
        return self.verifiedDatabase

    def getPendingFile(self):
        return self.pendingDatabase

    def logEntry(self, log, rowDict):
        for key in rowDict.keys():
            log[key].append(rowDict[key])

    def exportResults(self):
        """
        Generate two .csv log files: verified locations and pending locations.
        """
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))

        pendingData = pd.DataFrame(data=self.pending)
        pendingData.to_csv(self.pendingDatabase, sep=',', encoding='utf-8', index_label='Index')

        verifiedData = pd.DataFrame(data=self.verified)
        verifiedData.to_csv(self.verifiedDatabase, sep=',', encoding='utf-8', index_label='Index')

    def readFile(self, filePath):
        if filePath.endswith('xlsx'):
            data = pd.read_excel(filePath)
        elif filePath.endswith('csv'):
            data = pd.read_csv(filePath)
        else:
            print('Support is only available for .xlsx and .csv files.')
            data = None
        return data

    def addRowToDB(self, newDF, databasePath):
        database = self.readFile(databasePath)
        if database is None:
            return False

        database = pd.concat([database, newDF], ignore_index=True, sort=True)
        if databasePath.endswith('xlsx'):
            databasePath = databasePath.replace('xlsx', 'csv')
        database.to_csv('test_verified.csv', sep=',', encoding='utf-8', index=False)
        return True

    def deleteRowFromDB(self, rowIndex, databasePath):
        database = self.readFile(databasePath)
        if database is None:
            return False

        database = database.drop(database.index[rowIndex])

        if databasePath.endswith('xlsx'):
            databasePath = databasePath.replace('xlsx', 'csv')
        database.to_csv(databasePath, sep=',', encoding='utf-8', index=False)

class NameHandler:
    def __init__(self):

        self.namesDict = {}
        self.namesDict['United States of America'] = ['United States', 'US', 'USA', 'America']
        self.namesDict['Congo'] = ['Republic of Congo']
        self.namesDict['Congo, The Democratic Republic of the'] = ['Zaire', 'DR Congo', 'DRC', 'East Congo',
                                                                   'Congo-Kinshasa', 'Democratic Republic Of Congo',
                                                                   'Democratic Republic of Congo']
        self.namesDict['Spain'] = ['España']
        self.namesDict["Côte d'Ivoire"] = ["Cote d’Ivoire", "Cote D'ivoire", "Cote D'Ivoire"]
        self.namesDict['South Africa'] = ['South Africa Rep.', 'Republic of South Africa']
        self.namesDict['Trinidad and Tobago'] = ['Trinidad Y Tobago']

    def findName(self, checkCountry):
        for formattedName, alternativeNames in self.namesDict.items():
            for alternativeName in alternativeNames:
                if (checkCountry.lower() == alternativeName.lower()):
                    return formattedName
        return False

# database = DatabaseInitializer("/Users/thytnguyen/Desktop/tblLocation.xlsx")
# database.run()
# correctLog = database.getVerifiedLog()
# incorrectLog = database.getPendingLog()

validator = GeocodeValidator()
# res = validator.queryAllFields(location='Kilombo', country='Angola', latitude=-8.9, longitude=14.75)
# print(res)
# #
# # queryLoc = validator.queryByLocation('El Ovejero', 'China')
# # print(queryLoc)
# #
# # queryCoord = validator.queryByCoordinates(-16.73, -179.87)
# # print(queryCoord)
#
# add = validator.addLocation('Toronto', 'Canada', 43.65, 79.38)
# print(add)

# inPending = validator.addLocation('Yala Swamp', 'Kenya', 0.03, 34.1)
# print(inPending)
#
# inVerified = validator.addLocation('Dholi', 'India')
# print(inVerified)