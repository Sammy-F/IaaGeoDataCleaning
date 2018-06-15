from ConnectionUtils import databaseConnector as cu
import pytest

def testConnecting():
    mConnector = cu.DatabaseConnector()

    mConnector.getConnectFromConfig(filePath='D:\\config.ini')
    assert mConnector.connection is not None    # Check that a connection from config is made properly.
    assert mConnector.connection.closed == 0   # Check that the connection is open
    connTest = mConnector.connection
    print(mConnector.connection.status)
    mConnector.closeConnection()
    assert mConnector.connection is None    # Check that a connection is removed.
    assert connTest.status > 0  # Check that the connection is closed

testConnecting()