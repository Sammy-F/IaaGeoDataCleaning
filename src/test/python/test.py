from src.main.python.ConnectionUtils import DatabaseConnector, Table
import pytest
from random import choice
from string import ascii_uppercase

# def testConnectingWithGoodParams():
#     mConnector = cu.DatabaseConnector()
#
#     mConnector.getConnectFromConfig(filePath='D:\\config.ini')
#     assert mConnector.connection is not None    # Check that a connection from config is made properly.
#     assert mConnector.connection.closed == 0   # Check that the connection is open
#     connTest = mConnector.connection
#     print(mConnector.connection.status)
#     mConnector.closeConnection()
#     assert mConnector.connection is None    # Check that a connection is removed.
#     assert connTest.status > 0  # Check that the connection is closed
#
# def testTableGeneration():
#     mConnector = cu.DatabaseConnector()
#     mConnector.getConnectFromConfig(filePath='D:\\config.ini')
#     name = ''.join(choice(ascii_uppercase) for i in range(16))
#
#     mTable = cu.Table(name, mConnector)
#     mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-14-2.csv')
#
#     assert len(mTable.getTable(10)) == 10
#     assert len(mTable.getTable(0)) == 1407   # Test data has 1407 entries.
#
#     print(mTable.getTable(10))  # Visual test
#     print(mTable.getTable(0))   # Visual test
#     mConnector.closeConnection()
#
# def testGetTable():
#     mConnector = cu.DatabaseConnector()
#
#     mConnector.getConnectFromConfig(filePath='D:\\config.ini')
#     name = ''.join(choice(ascii_uppercase) for i in range(16))
#
#     mTable = cu.Table(name, mConnector)
#     mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-15.csv')
#     rows = mTable.getTable(limit=10)
#     print(rows) # Visual test
#     assert len(rows) == 10
#     rows = mTable.getTable()
#     assert len(rows) == 1407
#
#     mConnector.closeConnection()

# TODO: THIS TEST IS NOT WORKING
def testMakeSpatial():
    mConnector = DatabaseConnector()

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')
    name = ''.join(choice(ascii_uppercase) for i in range(16))

    mTable = Table(name, mConnector)
    mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-20.csv')

    mConnector.connection.commit()

    cmmnd = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + name + "' AND column_name = 'geom';";
    cur = mConnector.connection.cursor()
    cur.execute(cmmnd)
    result = cur.fetchall()
    cur.close()
    print(result)
    assert len(result) == 0

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')

    mTable.makeTableSpatial()
    mConnector.connection.commit()

#     cmmnd2 = "SELECT column_name FROM information_schema.columns WHERE table_name='" + name + "' AND column_name='geom';"
#     cur = mConnector.connection.cursor()
#     cur.execute(cmmnd2)
#     result = cur.fetchall()
#     cur.close()
#     print(result)
#     assert len(result) > 0
#     mConnector.closeConnection()

# def testGetEntries():
#     mConnector = cu.DatabaseConnector()
#
#     mConnector.getConnectFromConfig(filePath='D:\\config.ini')
#     name = ''.join(choice(ascii_uppercase) for i in range(16))
#
#     mTable = cu.Table(name, mConnector)
#     mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-15.csv')
#     mTable.makeTableSpatial()
#
#     check = mTable.checkForEntryByLatLon(lat=34.48845, lon=69.20288)
#     assert check[0] is True
#     print(str(check[1]))    # Visual check
#     check = mTable.checkForEntryByLatLon(lat=-133, lon=0.1)
#     assert check[0] is False
#
#     check = mTable.checkForEntryByCountryLoc(countryName='Afghanistan', locationName='Darul Aman')
#     assert check[0] is True
#     print(str(check[1]))    # Visual check
#     check = mTable.checkForEntryByCountryLoc(countryName='Afghanfeedistan', locationName='Darugl Aman')
#     assert check[0] is False
#     check = mTable.checkForEntryByCountryLoc(countryName='Afghasdsnistan', locationName='Darul Aman')
#     assert check[0] is False
#     check = mTable.checkForEntryByCountryLoc(countryName='Afghanistan', locationName='Dedsarul Aman')
#     assert check[0] is False
#
#     mConnector.closeConnection()
#
# def testUpdateTable():
#     mConnector = cu.DatabaseConnector()
#
#     mConnector.getConnectFromConfig(filePath='D:\\config.ini')
#     name = ''.join(choice(ascii_uppercase) for i in range(16))
#
#     mTable = cu.Table(name, mConnector)
#     mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-14-2.csv')
#     mTable.makeTableSpatial()
#
#     rows = mTable.getTable()
#     assert len(rows) == 1407
#
#     # Modified data where an entry has different lat/long, different country, and both different lat/lon and country
#     # Only one should be inserted
#     mTable.updateEntries('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-14.csv')
#
#     rows = mTable.getTable()
#     assert len(rows) == 1408
#     mConnector.closeConnection()

# TODO: THIS TEST IS NOT WORKING
def testGetEntriesByInput():
    mConnector = DatabaseConnector()

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')
    name = ''.join(choice(ascii_uppercase) for i in range(16))

    mTable = Table(name, mConnector)
    mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-20.csv')
    # vals1 = ['Tanzania', 'no lat/lng entered - geocoded location']
    # cols1 = ['country', 'type']
    vals1 = ['Tanzania']
    cols1 = ['Country']

    results = mTable.getEntriesByInput(vals=vals1, columnNames=cols1)

    assert len(results) == 19

    mConnector.closeConnection()

