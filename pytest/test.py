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

# testConnectingWithGoodParams()
# testTableGeneration()