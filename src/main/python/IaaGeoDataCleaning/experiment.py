from os import path
import pandas as pd
import numpy as np
import math
import string
import re

import pycountry as pc
import geopandas as gpd
import geopy as gp
from shapely.geometry import Point

# TODO: Make a case that has coordinates but no location info
# TODO: Expand country checking method (split and contain?)
# TODO: Document code
# TODO: Query class? Database Utils?

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

regex = re.compile(' \(\d\)')


class GeocodeValidator:
    def __init__(self):
        self.pht = gp.Photon(timeout=3)
        self.dbi = DatabaseInitializer()

        self.entryType = {0: 'correct location data', 1: 'entered (lat, -lng)',
                          2: 'entered (-lat, lng)', 3: 'entered (-lat, -lng)',
                          4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
                          6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)',
                          8: 'no lat/lng entered / incorrect lat/lng - geocoded location',
                          -1: 'incorrect location data/cannot find coordinates',
                          -2: 'no latitude and longitude entered',
                          -3: 'no location/country entered / wrong country format'}

        mapFile = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..',
                                             'resources', 'mapinfo', 'TM_WORLD_BORDERS-0.3.shp')))
        self.map = gpd.read_file(mapFile)

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
        if inpType == -3:
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
        if pd.notnull(location):
            location = string.capwords(location)
        if pd.notnull(country):
            country = string.capwords(country)
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
            return -3, locationDict

        # Looking up with pycountry
        try:
            locationDict['Country_Code'] = pc.countries.lookup(locationDict['Country']).alpha_3
            locationDict['Country'] = pc.countries.lookup(locationDict['Country']).name

        except LookupError:
            altCountryName = self.findFormattedName(locationDict['Country'])
            if not altCountryName:
                return -3, locationDict
            else:
                locationDict['Country'] = altCountryName
                locationDict['Country_Code'] = pc.countries.lookup(altCountryName).alpha_3

        # Checking if lat/lng were entered
        if (pd.isnull(locationDict['Latitude']) or pd.isnull(locationDict['Longitude'])) or (
                locationDict['Latitude'] == 0 and locationDict['Longitude'] == 0):
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
                mLoc = self.map.loc[filter, 'ISO3']
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

    def findFormattedName(self, alternativeName):
        """
        If a country name is invalid, assume it is an alternative name
        and attempt to find and return the official one
        :param alternativeName:
        """
        finder = NameHandler()
        return finder.findName(alternativeName)


class DatabaseInitializer:
    def createNewDB(self, originalDB, locationCol, countryCol, latitudeCol, longitudeCol, validator):
        # Reading the original data
        data = self.readFile(originalDB)
        if data is None:
            return

        # Variables to save entries
        verifiedEntries = {'Type': [], 'Location': [], 'Country': [], 'Latitude': [], 'Longitude': [],
                           'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [], 'Country_Code': []}
        pendingEntries = {'Type': [], 'Location': [], 'Country': [], 'Latitude': [], 'Longitude': [],
                          'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [], 'Country_Code': []}
        repeatedEntries = {'Location': [], 'Country': [], 'Latitude': [], 'Longitude': [],
                           'ver_Index': [], 'ver_Loc': [], 'ver_Cty': [], 'ver_Lat': [], 'ver_Lng': []}
        flaggedLocations = []

        # Cleaning the data
        self.cleanData(data, locationCol, countryCol, latitudeCol, longitudeCol, validator,
                       verifiedEntries, pendingEntries, repeatedEntries, flaggedLocations)

        # Exporting the data
        extension = ''
        pendingDB = input('Enter file name for pending entry data frame (without extension): ')
        verifiedDB = input('Enter file name for verified entry data frame (without extension): ')
        repeatedDB = input('Enter file name for repeated entry data frame (without extension): ')
        while extension != 'csv' and extension != 'xlsx':
            extension = input('Enter file extension (csv/xlsx): ').lower()
        self.exportFile(verifiedEntries, verifiedDB, extension)
        self.exportFile(pendingEntries, pendingDB, extension)
        self.exportFile(repeatedEntries, repeatedDB, extension)

    def cleanData(self, data, locCol, ctyCol, latCol, lngCol, validator, verified, pending, repeated, flagged):
        for (index, row) in data.iterrows():
            print('Verifying row at index: ' + str(index))
            location = row[locCol]
            country = row[ctyCol]
            latitude = row[latCol]
            longitude = row[lngCol]

            locInDB = self.locationInDatabase(location, country, verified['Location'], verified['Country'])
            # TODO: TEST THIS !!
            if locInDB[0]:
                for verIdx in locInDB[1]:
                    verLoc = verified['Location'][verIdx]
                    verCty = verified['Country'][verIdx]
                    verLat = verified['Recorded_Lat'][verIdx]
                    verLng = verified['Recorded_Lng'][verIdx]
                    entry = {'Location': location, 'Country': country, 'Latitude': latitude, 'Longitude': longitude,
                             'ver_Index': verIdx, 'ver_Loc': verLoc, 'ver_Cty': verCty, 'ver_Lat': verLat, 'ver_Lng': verLng}
                    self.logToDict(repeated, entry)
            else:
                entry = validator.verifyInfo(location, country, latitude, longitude)
                if entry[0] < 0:
                    flagged.append(index)
                    self.logToDict(pending, entry[1])
                else:
                    self.logToDict(verified, entry[1])

    def getIncorrectPercent(self, data, flagged):
        return len(flagged) / (1e-10 + data.shape[0])

    def logToDict(self, log, rowDict):
        for key in rowDict.keys():
            log[key].append(rowDict[key])

    def exportFile(self, dataDict, fileName, type):
        fileName = fileName + '.' + type
        filePath = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..', 'resources', type, fileName)))

        df = pd.DataFrame(dataDict)
        if fileName.endswith('.csv'):
            df.to_csv(filePath, index_label='Index', sep=',', encoding='utf-8')
        elif fileName.endswith('.xlsx'):
            df.to_excel(filePath, index_label='Index')

        print('Finished exporting. File can be found at: ')
        print(filePath)

    def readFile(self, filePath):
        """
        Reads in csv or excel file.
        :param filePath:
        :return: a pandas data frame.
        """
        if filePath.endswith('xlsx'):
            data = pd.read_excel(filePath)
        elif filePath.endswith('csv'):
            data = pd.read_csv(filePath)
        else:
            print('Support is only available for .xlsx and .csv files.')
            data = None
        return data

    def queryByAll(self, filePath, loc, cty, lat, lng, locCol, ctyCol, latCol, lngCol, printRes=True):
        results = []
        tBool = False
        locInDB = self.queryByLocation(filePath, loc, cty, locCol, ctyCol, printRes=False)
        if locInDB[0]:
            locIndices = locInDB[1]
            coordIndices = self.queryByCoordinates(filePath, lat, lng, latCol, lngCol, printRes=False)[1]
            for idx in locIndices:
                if idx in coordIndices:
                    results.append(idx)
                    tBool = True

            if printRes:
                if len(results) > 0:
                    print('Entry is found at indices: ' + str(results))

                print('Location and coordinates do not correspond:')
                print('\t' + loc + ', ' + cty + ' is found at indices: ' + str(locIndices))
                print('\t(' + str(lat) + ', ' + str(lng) + ') is found at indices: ' + str(coordIndices))
            return tBool, results

        print('Entry is not in database.')
        return tBool, results

    def queryByLocation(self, filePath, loc, cty, locCol, ctyCol, printRes=True):
        database = self.readFile(filePath)
        if database is None:
            return False, []

        try:
            locList = database[locCol].tolist()
            ctyList = database[ctyCol].tolist()
            result = self.locationInDatabase(loc, cty, locList, ctyList)
            if printRes:
                if result[0]:
                    print(loc + ', ' + cty + ' is found at indices: ' + str(result[1]))
                else:
                    print(loc + ', ' + cty + ' is not in database.')
            return result

        except KeyError:
            print("Cannot find columns with names: '" + locCol + "' and '" + ctyCol + "'")
            return False, []

    def queryByCoordinates(self, filePath, lat, lng, latCol, lngCol, printRes=True):
        database = self.readFile(filePath)
        if database is None:
            return False, []

        try:
            latList = database[latCol].tolist()
            lngList = database[lngCol].tolist()
            result = self.coordinatesInDatabase(lat, lng, latList, lngList)
            if printRes:
                if result[0]:
                    print('(' + str(lat) + ', ' + str(lng) + ') is found at indices: ' + str(result[1]))
                else:
                    print('(' + str(lat) + ', ' + str(lng) + ') is not in database.')
            return result

        except KeyError:
            print("Cannot find columns with names: '" + latCol + "' and '" + lngCol + "'")
            return False, []

    def coordinatesInDatabase(self, latitude, longitude, latitudeList, longitudeList):
        results = []
        if pd.isnull(latitude) or pd.isnull(longitude):
            return False, results
        inLat = any(math.isclose(latitude, latInList, abs_tol=1e-1) for latInList in latitudeList)
        if inLat:
            indices = [i for i, v in enumerate(latitudeList) if math.isclose(latitude, v, abs_tol=1e-1)]
            for index in indices:
                if math.isclose(longitude, longitudeList[index], abs_tol=1e-1):
                    results.append(index)
            if len(results) > 0:
                return True, results
        return False, results

    def locationInDatabase(self, location, country, locationList, countryList):
        results = []
        if pd.isnull(location) or pd.isnull(country):
            return False, results
        location = regex.sub('', location)
        inLoc = any(re.search(location, str(loc), re.IGNORECASE) for loc in locationList)
        if inLoc:
            indices = [i for i, v in enumerate(locationList) if re.search(location, str(v), re.IGNORECASE)]
            for index in indices:
                if re.search(country, countryList[index], re.IGNORECASE):
                    results.append(index)
            if len(results) > 0:
                return True, results
        return False, results

    # def addRowToDB(self, rowDF, databasePath):
    #     """
    #     Adds a row to the database the file path points to,
    #     overwrites the file with the new database file in csv format.
    #     :param newDF: the new row as a data frame
    #     :param databasePath: the file path to the database to update
    #     :return: True if updated.
    #     """
    #     database = self.readFile(databasePath)
    #     if database is None:
    #         return False
    #
    #     database = pd.concat([database, rowDF], ignore_index=True, sort=True)
    #
    #     if databasePath.endswith('xlsx'):
    #         database.to_excel(databasePath, index=False)
    #     else:
    #         database.to_csv(databasePath, sep=',', encoding='utf-8', index=False)
    #     return True
    #
    # def deleteRowFromDB(self, rowIndex, databasePath):
    #     """
    #     Deletes a row from the database the file path points to,
    #     overwrites the file with the new database file in csv format.
    #     :param rowIndex: the index of the row to be deleted
    #     :param databasePath: the file path to the database to update
    #     :return: True if updated.
    #     """
    #     database = self.readFile(databasePath)
    #     if database is None:
    #         return False
    #
    #     database = database.drop(database.index[rowIndex])
    #
    #     if databasePath.endswith('xlsx'):
    #         database.to_excel(databasePath, index=False)
    #     else:
    #         database.to_csv(databasePath, sep=',', encoding='utf-8', index=False)
    #     return True

    # def addEntry(self, validator, filePath, loc, cty, locCol, ctyCol, latCol, lngCol, lat=None, lng=None):
    #     if lat is None or lng is None:
    #         results = self.queryByLocation(filePath, loc, cty, locCol, ctyCol, False)
    #     else:
    #         results = self.queryByAll(filePath, loc, cty, lat, lng, locCol, ctyCol, latCol, lngCol, False)
    #
    #     if results[0]:
    #         print('Entry exists in the database at indices: ' + str(results[1]))
    #         return False
    #
    #     entry = validator.verifyInfo(loc, cty, lat, lng)
    #     if entry >= 0:


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
#
# validator = GeocodeValidator()
# initializer = DatabaseInitializer()
# initializer.createNewDB('/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/xlsx/tblLocation.xlsx',
#                         'Location', 'Country', 'Latitude', 'Longitude', validator)