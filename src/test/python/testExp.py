from src.main.python.IaaGeoDataCleaning import experiment as exp
import pytest
import pandas as pd
from os import path

# entryType = {0: 'correct location data', 1: 'entered (lat, -lng)', 2: 'entered (-lat, lng)',
#              3: 'entered (-lat, -lng)', 4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
#              6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)', 8: 'no lat/lng entered - geocoded location',
#              -1: 'incorrect location data/cannot find coordinates', -2: 'no latitude and longitude entered',
#              -3: 'country not found/wrong country format', -4: 'no location/country entered',
#              -5: 'no location/country entered / wrong country format'}

validator = exp.GeocodeValidator()
di = exp.DatabaseInitializer()


def testCheckInput():
    # Missing location information
    missingCountry = validator.formatInformation('Puebla', None, 19.042, -98.21)
    missingLocation = validator.formatInformation(None, 'Mexico', 20.6, -105.25)

    check = validator.checkInput(missingCountry)
    assert check[0] == -3
    check = validator.checkInput(missingLocation)
    assert check[0] == -3

    # Should be Kingdom of Swaziland
    wrongCountryFormat = validator.formatInformation('Mangcongo', 'Republic of Swaziland', None, None)
    check = validator.checkInput(wrongCountryFormat)
    assert check[0] == -3
    # Should be Republic of South Africa
    wrongCountryFormat = validator.formatInformation('Cedara', 'South Africa Republic', None, None)
    check = validator.checkInput(wrongCountryFormat)
    assert check[0] == -3
    assert isinstance(check[1], dict)

    # Missing latitude and longitude but should pass location because the names will be found in nameHandler
    missingLng = validator.formatInformation('Touba', "Cote d'Ivoire", 8.366, None)
    missingLat = validator.formatInformation('Mvuazi', 'Zaire', None, 14.9)
    missingBoth = validator.formatInformation('El Carmen', 'Trinidad Y Tobago', None, 0)

    check = validator.checkInput(missingLng)
    assert check[0] != -3
    assert check[0] == -2
    check = validator.checkInput(missingLat)
    assert check[0] == -2
    check = validator.checkInput(missingBoth)
    assert check[0] == -2
    assert isinstance(check[1], dict)

    # If only lat or lng is 0 then it should pass
    validLng = validator.formatInformation('Touba', "Cote d'Ivoire", 8.366, 0)
    validLat = validator.formatInformation('Mvuazi', 'Zaire', 0, 14.9)
    check = validator.checkInput(validLng)
    assert check[0] == 0
    check = validator.checkInput(validLat)
    assert check[0] == 0
    assert isinstance(check[1], dict)


def testVerifyCoordinates():
    # Should be (12.0, -7.0)
    flipped = validator.formatInformation('Rue Mohamed', 'Mali', -12.0, -7)
    check = validator.checkInput(flipped)
    assert check[0] == 0
    verified = validator.verifyCoordinates(check[1])
    assert verified[0] == 2
    assert verified[1]['Recorded_Lat'] == 12.0

    # Incorrect coordinates
    incorrect = validator.formatInformation('Gwebi', 'Zimbabwe', 89.8, -13.2)
    check = validator.checkInput(incorrect)
    verified = validator.verifyCoordinates(check[1])
    assert verified[0] == -1
    assert verified[1] == check[1]

    # Correct coordinates
    correct = validator.formatInformation('Hudson', 'USA', 41.239, -81.441)
    check = validator.checkInput(correct)
    verified = validator.verifyCoordinates(check[1])
    assert verified[0] == 0
    assert verified[1]['Recorded_Lat'] == verified[1]['Latitude']
    assert verified[1]['Recorded_Lng'] == -81.441


def testGeocodeCoordinates():
    # Correct coordinates
    correct = validator.formatInformation('Rampur', 'Nepal', 27.848, 83.9)
    check = validator.checkInput(correct)
    geocoded = validator.geocodeCoordinates(check[1])
    assert geocoded[0] == 8
    assert pytest.approx(geocoded[1]['Recorded_Lng'], 1e-2) == geocoded[1]['Longitude']
    assert pytest.approx(geocoded[1]['Recorded_Lat'], 1e-2) == geocoded[1]['Latitude']

    # No coordinates entered
    missing = validator.formatInformation('Greytown', 'South Africa Rep.', 0, 0)
    check = validator.checkInput(missing)
    assert check[0] == -2
    geocoded = validator.geocodeCoordinates(check[1])
    assert geocoded[0] == 8
    assert pytest.approx(geocoded[1]['Recorded_Lng'], 1e-2) == 30.608
    assert pytest.approx(geocoded[1]['Recorded_Lat'], 1e-2) == -29.054


def testVerifyInfo():
    # 5 cases in total
    # Correct inputs, country is in a different format
    correct = validator.verifyInfo('Greytown', 'Republic of South Africa', -29.054, 30.608)
    assert correct[0] == 0
    assert pytest.approx(correct[1]['Recorded_Lat'], 1e-2) == correct[1]['Latitude']
    assert pytest.approx(correct[1]['Recorded_Lng'], 1e-2) == correct[1]['Longitude']

    # Missing location and country
    missing = validator.verifyInfo(country='Zaire')
    assert missing[0] == -3
    missing = validator.verifyInfo(location='Jashipur')
    assert missing[0] == -3

    # Missing latitude and longitude
    missing = validator.verifyInfo('New Delhi', 'India', 0, None)
    assert missing[0] == 8
    assert pytest.approx(missing[1]['Recorded_Lat'], 1e-2) == 28.6139
    assert pytest.approx(missing[1]['Recorded_Lng'], 1e-2) == 77.2090

    # Flipped lat/lng
    flipped = validator.verifyInfo('Jashipur', 'India', 86.075, 21.968)
    assert flipped[0] == 4
    assert pytest.approx(flipped[1]['Recorded_Lat'], 1e-2) == flipped[1]['Longitude']
    assert pytest.approx(flipped[1]['Recorded_Lng'], 1e-2) == flipped[1]['Latitude']

    # Incorrect coordinates, geocode
    incorrect = validator.verifyInfo('Kulumsa', 'Ethiopia', 17.8, 20.24)
    assert incorrect[0] == 8
    assert pytest.approx(incorrect[1]['Recorded_Lat'], 1e-1) == 8.0
    assert pytest.approx(incorrect[1]['Recorded_Lng'], 1e-1) == 39.15


def testAddLocation():
    # Entries already in the data
    inDB = validator.addLocation('College Station', 'United States')
    assert isinstance(inDB, list)
    inDB = validator.addLocation(latitude=19.67, longitude=-103.6)
    assert len(inDB) > 0

    # Location and country entered, no latitude and longitude
    newEntry = validator.addLocation('Hudson Ohio', 'USA')
    assert isinstance(newEntry, tuple)
    assert newEntry[0] == 8

    # Flipped coordinates
    newEntry = validator.addLocation('SICILY', 'ITALY', -37.6, -14.01)
    assert isinstance(newEntry, tuple)
    assert newEntry[0] == 3
    assert pytest.approx(newEntry[1]['Recorded_Lat'], 1e-2) == -newEntry[1]['Latitude']
    assert pytest.approx(newEntry[1]['Recorded_Lng'], 1e-2) == -newEntry[1]['Longitude']

    # Entry in the pending database
    validator.addLocation('Yezin', 'Myanmar', 23.03, 95.47)
    df = pd.read_csv('test_pending.csv')
    assert df.shape[0] == 67
    df = pd.read_csv('test_verified.csv')
    assert df.shape[0] == 1404

    # Cannot be added, no location and country provided
    newEntry = validator.addLocation(latitude=0, longitude=0)
    assert newEntry[0] == -5


def testLocationInDatabase():
    locList = ['Darul Aman', 'Kilombo', 'Ishurdi', 'Sids']
    ctyList = ['Afghanistan', 'Angola', 'Bangladesh', 'Egypt']

    inDB = di.locationInDatabase('DARUL AMAN (2)', 'AFGHANISTAN', locList, ctyList)
    assert inDB[0] is True and inDB[1][0] == 0
    inDB = di.locationInDatabase('SIDS (1)', 'eGyPt', locList, ctyList)
    assert inDB[0] is True and inDB[1][0] == 3
    notInDB = di.locationInDatabase('Darul Aman Kabul (2)', 'Afghanistan', locList, ctyList)
    assert notInDB[0] is False


def testCoordinatesInDatabase():
    latList = [23.41, 23.41, 23.5, 30.00, 87.12]
    lngList = [53.78, -12.09, -12.00, 9.44, 71.31]

    inDB = di.coordinatesInDatabase(23.42, 53.77, latList, lngList)
    assert inDB[0] is True and inDB[1][0] == 0
    inDB = di.coordinatesInDatabase(23.40, -12.1, latList, lngList)
    assert inDB[0] is True and inDB[1][0] == 1
    notInDB = di.coordinatesInDatabase(33.02, 9.54, latList, lngList)
    assert notInDB[0] is False
    notInDB = di.coordinatesInDatabase(87.11, -12.08, latList, lngList)
    assert notInDB[0] is False


def setUpFiles():
    verified = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..', 'IaaGeoDataCleaning',
                                          'src', 'test', 'resources', 'verified_entries-06-22.xlsx')))
    pending = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..', 'IaaGeoDataCleaning',
                                         'src', 'test', 'resources', 'pending_entries-06-22.xlsx')))
    repeated = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..', 'IaaGeoDataCleaning',
                                          'src', 'test', 'resources', 'repeated_entries-06-22.xlsx')))

    return verified, pending, repeated


files = setUpFiles()


def testQueryByLocation():
    # Burura - Kenya
    inDB = di.queryByLocation(files[0], 'BURURA (2)', 'KENYA', 'Location', 'Country')
    assert inDB[0] is True
    notInDB = di.queryByLocation(files[1], 'BURURA (2)', 'KENYA', 'Location', 'Country')
    assert notInDB[0] is False

    wrongColName = di.queryByLocation(files[0], 'MAROS', 'INDONESIA', 'LOCATION', 'COUNTRY')
    assert wrongColName[1] == []

    # re.search is True for re.search('United States', 'United States of America') but not the other way around
    wrongCty = di.queryByLocation(files[0], 'BARNUM MN (2)', 'UNITED STATES OF AMERICA', 'Location', 'Country')
    assert wrongCty[0] is False

    # VALLE DE MAGDALENA (2) - COLOMBIA
    inDB = di.queryByLocation(files[2], 'Valle de Magdalena', 'Colombia', 'Location', 'Country')
    print(inDB)
    assert inDB[1] == [10, 11, 12]


def testQueryByCoordinates():
    # (9.3154, -75.4329)
    inDB = di.queryByCoordinates(files[0], 9.32, -75.4, 'Recorded_Lat', 'Recorded_Lng')
    assert inDB[1][0] == 157
    # (14.92, 37.83)
    inDB = di.queryByCoordinates(files[0], 14.9, 37.8, 'Recorded_Lat', 'Recorded_Lng')
    assert inDB[1][0] == 228
    notInDB = di.queryByCoordinates(files[0], 14.8, 37.8, 'Recorded_Lat', 'Recorded_Lng')
    assert notInDB[0] is False
    # (-0.5359, 37.6653)
    notInDB = di.queryByCoordinates(files[0], -0.5, 37.7, 'Latitude', 'Longitude')  # Geocoded this one, lat/lng empty
    assert notInDB[0] is False
    inDB = di.queryByCoordinates(files[0], 1.06, 35, 'Recorded_Lat', 'Recorded_Lng')
    assert len(inDB[1]) > 0


def testQueryByAll():
    # Location and coordinates do not match
    # 395: Embu - Kenya (-0.5, 37.45)
    mismatched = di.queryByAll(files[0], 'EMBU', 'KENYA', 0.1, 34.5, 'Location', 'Country', 'Latitude', 'Longitude')
    assert mismatched[0] is False
    # 597: Uach, Campo Experimental - Mexico (19.48933,	-98.89365)
    inDB = di.queryByAll(files[0], 'UACH', 'MEXICO', 19.49, -98.8, 'Location', 'Country', 'Recorded_Lat', 'Recorded_Lng')
    assert inDB[1][0] == 597
    # Harare - Zimbabwe
    inDB = di.queryByAll(files[0], 'HARARE (2)', 'ZIMBABWE', -17.78, 31.00, 'Location', 'Country', 'Recorded_Lat', 'Recorded_Lng')
    assert len(inDB[1]) > 0


testCheckInput()
testVerifyCoordinates()
testGeocodeCoordinates()
testVerifyInfo()
testLocationInDatabase()
testCoordinatesInDatabase()
testQueryByLocation()
testQueryByCoordinates()
testQueryByAll()