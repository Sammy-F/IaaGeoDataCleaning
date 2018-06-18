from ConnectionUtils import databaseConnector as cu
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
#     mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-15.csv')
#
#     assert len(mTable.getTable(10)) == 10
#     assert len(mTable.getTable(0)) == 1402   # Test data has 734 entries.
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
#     assert len(rows) == 1402
#
#     mConnector.closeConnection()

def testMakeSpatial():
    mConnector = cu.DatabaseConnector()

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')
    name = ''.join(choice(ascii_uppercase) for i in range(16))

    mTable = cu.Table(name, mConnector)
    mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-15.csv')

    mConnector.connection.commit()

    cmmnd = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + name + "' AND column_name = 'geom';";
    cur = mConnector.connection.cursor()
    cur.execute(cmmnd)
    result = cur.fetchall()
    cur.close()
    print(result)
    assert len(result) == 0

    mTable.makeTableSpatial()

    cmmnd = "SELECT column_name FROM information_schema.columns WHERE table_name='" + name + "' AND column_name='geom'"
    cur = mConnector.connection.cursor()
    cur.execute(cmmnd)
    result = cur.fetchall()
    cur.close()
    print(result)
    assert len(result) > 0

def testGetEntries():
    mConnector = cu.DatabaseConnector()

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')
    name = ''.join(choice(ascii_uppercase) for i in range(16))

    mTable = cu.Table(name, mConnector)
    mTable.buildTableFromFile('D:\\IaaGeoDataCleaning\\IaaGeoDataCleaning\\verified_data_2018-06-15.csv')
    mTable.makeTableSpatial()

    check = mTable.checkForEntryByLatLon(lat=34.48845, lon=69.20288)
    assert check[0] is True
    print(str(check[1]))    # Visual check
    check = mTable.checkForEntryByLatLon(lat=-133, lon=0.1)
    assert check[0] is False

    check = mTable.checkForEntryByCountryLoc(countryName='Afghanistan', locationName='Darul Aman')
    assert check[0] is True
    print(str(check[1]))    # Visual check
    check = mTable.checkForEntryByCountryLoc(countryName='Afghanfeedistan', locationName='Darugl Aman')
    assert check[0] is False
    check = mTable.checkForEntryByCountryLoc(countryName='Afghasdsnistan', locationName='Darul Aman')
    assert check[0] is False
    check = mTable.checkForEntryByCountryLoc(countryName='Afghanistan', locationName='Dedsarul Aman')
    assert check[0] is False

    mConnector.closeConnection()
