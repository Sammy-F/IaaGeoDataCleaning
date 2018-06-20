from IaaGeoDataCleaning.IaaGeoDataCleaning import experiment as exp
import pytest
import pandas as pd

# entryType = {0: 'correct location data', 1: 'entered (lat, -lng)', 2: 'entered (-lat, lng)',
#              3: 'entered (-lat, -lng)', 4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
#              6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)', 8: 'no lat/lng entered - geocoded location',
#              -1: 'incorrect location data/cannot find coordinates', -2: 'no latitude and longitude entered',
#              -3: 'country not found/wrong country format', -4: 'no location/country entered',
#              -5: 'no location/country entered / wrong country format'}

validator = exp.GeocodeValidator()


def testCheckInput():
    # Missing location information
    missingCountry = validator.formatInformation('Puebla', None, 19.042, -98.21)
    missingLocation = validator.formatInformation(None, 'Mexico', 20.6, -105.25)

    check = validator.checkInput(missingCountry)
    assert check[0] == -5
    check = validator.checkInput(missingLocation)
    assert check[0] == -5

    # Should be Kingdom of Swaziland
    wrongCountryFormat = validator.formatInformation('Mangcongo', 'Republic of Swaziland', None, None)
    check = validator.checkInput(wrongCountryFormat)
    assert check[0] == -5
    # Should be Republic of South Africa
    wrongCountryFormat = validator.formatInformation('Cedara', 'South Africa Republic', None, None)
    check = validator.checkInput(wrongCountryFormat)
    assert check[0] == -5
    assert isinstance(check[1], dict)

    # Missing latitude and longitude but should pass location because the names will be found in nameHandler
    missingLng = validator.formatInformation('Touba', "Cote d'Ivoire", 8.366, None)
    missingLat = validator.formatInformation('Mvuazi', 'Zaire', None, 14.9)
    missingBoth = validator.formatInformation('El Carmen', 'Trinidad Y Tobago', None, 0)

    check = validator.checkInput(missingLng)
    assert check[0] != -5
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
    assert missing[0] == -5
    missing = validator.verifyInfo(location='Jashipur')
    assert missing[0] == -5

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


def testQueryAllFields():
    # In the database
    inDB = validator.queryAllFields('Ambo', 'Ethiopia', 8.96, 38.9)
    assert len(inDB) == 1

    # Location and country is in the database but wrong latitude/longitude
    missing = validator.queryAllFields('Ambo', 'Ethiopia', 10.31, -23.912)
    assert len(missing) == 0

    # Different country name
    dif = validator.queryAllFields('Tifton', 'United States', 31.45, -83.51)
    assert len(dif) == 2


def testQueryByLocation():
    inDB = validator.queryByLocation('Campos Azules', 'Nicaragua')
    assert len(inDB) == 2

    # Entry in pending data
    notInDB = validator.queryByLocation('Mungushi', 'Tanzania')
    assert len(notInDB) == 0
    inDB = validator.queryByLocation('Mungushi', 'Tanzania',
                                     '~/Desktop/geodata/IaaGeoDataCleaning/IaaGeoDataCleaning/pending_data_2018-06-15.csv')
    assert len(inDB) == 1


def testQuery():
    # Missing location and country
    inDB = validator.query(latitude=13.534, longitude=-85.926)
    assert len(inDB) > 0
    # Missing location and country but not in database
    notInDB = validator.query(latitude=42.12, longitude=0)
    assert len(notInDB) == 0

    # Missing latitude and longitude
    inDB = validator.query(location='LAYIN', country='Nigeria')
    assert len(inDB) == 1

    # All arguments are entered
    inDB = validator.query(location='LA TRINIDAD', country='NICARAGUA', latitude=12.96, longitude=-86.27)
    assert len(inDB) == 1

    # All arguments are entered but the latitude and longitude are wrong
    inDB = validator.query(location='Cuyuta', country='GUATEMALA', latitude=16.25, longitude=70.34)
    assert len(inDB) == 1
    assert inDB[0]['Country'] == 'Guatemala'
    assert inDB[0]['Recorded_Lat'] == 14.25
    assert inDB[0]['Recorded_Lng'] == -90.00


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


#  testCheckInput()
# testVerifyCoordinates()
# testGeocodeCoordinates()
# testVerifyInfo()
# testQueryAllFields()
# testQueryByLocation()
testQuery()
# testAddLocation()
