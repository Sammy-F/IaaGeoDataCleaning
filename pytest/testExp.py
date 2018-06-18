from IaaGeoDataCleaning.IaaGeoDataCleaning import experiment as exp
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





testCheckInput()