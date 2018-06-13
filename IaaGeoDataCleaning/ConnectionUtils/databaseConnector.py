import psycopg2 as psy
from configparser import ConfigParser
import pandas as pd

class DatabaseConnector:

    def __init__(self):
        self.connection = None

    def __setConfig(self, filePath, section='postgresql'):
        """
        Load config file and return database params
        based off of it
        :param filePath:
        :param section:
        :return:
        """
        parser = ConfigParser()
        parser.read(filePath)

        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filePath))
        return db

    def getConnectFromConfig(self, filePath, section='postgresql'):
        """
        Connect to database from parameters
        :param filePath:
        :param section:
        :return:
        """
        if not self.connection is None:
            self.connection.close()
            self.connection = None
        try:
            params = self.__setConfig(filePath, section)

            print('Attempting connection to PostgreSQL database...')
            self.connection = psy.connect(**params)

            cur = self.connection.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            db_version = cur.fetchone()
            print(db_version)

            cur.close()

            print("Connection opened. Don't forget to call closeConnection() on the DatabaseConnector when you're done!")

            return self.connection
        except (Exception, psy.DatabaseError) as error:
            print(error)
            if self.connection is not None:
                self.connection.close()
                print('Connection closed.')
                self.connection = None

    def getConnectFromKeywords(self, host, dbname, username, password, port=5432):
        """
        Set up from keywords, not secure
        :param host:
        :param dbname:
        :param username:
        :param password:
        :param port:
        """

        if not self.connection is None:
            self.connection.close
            self.connection = None

        try:
            print('Attempting connection to PostgreSQL database...')
            self.connection = None
            self.connection = psy.connect(host=host, database=dbname, user=username, password=password, port=port)

            cur = self.connection.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            db_version = cur.fetchone()
            print(db_version)

            cur.close()

            return self.connection
        except (Exception, psy.DatabaseError) as error:
            print(error)
            if self.connection is not None:
                self.connection.close()
                print('Connection closed.')
                self.connection = None

    def getExistingConnection(self):
        return self.connection

    def closeConnection(self):
        """
        Close the connection to the database if it exists.
        :return:
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            print("Connection closed.")

class Table:

    def __init__(self, tableName, connection):
        self.tableName = tableName
        self.connection = connection

        self.table = None

    def loadTable(self):
        """
        Load an existing table from the db
        :return:
        """

    def buildTableFromTuple(self, commandTuple):
        """
        Build a table from a .csv file
        :return:
        """

        commands = (commandTuple)

        try:
            if not self.connection is None:
                cur = self.connection.cursor()
                for command in commands:
                    cur.execute(command)
                cur.close()
                self.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print(error)

    def buildTableFromFile(self, filePath):
        if filePath.endswith('xlsx'):
            tableFile = pd.read_excel(filePath)
        else:
            tableFile = pd.read_csv(filePath)

        schemaTuple = self.loadTableSchema(tableFile)

        schemaStr = self.buildSchemaString(schemaTuple)

        schemaStr = "CREATE TABLE " + self.tableName + " " + schemaStr
        print(schemaStr)

        try:
            cur = self.connection.cursor()

            cur.execute(schemaStr)

            self.loadData(cur, filePath)

            cur.close()
            self.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print(error)

    def loadTableSchema(self, tableFile):

        names = list(tableFile.columns.values)
        typeArr = []

        i = 0

        for (index, row) in tableFile.iterrows():
            if i == 0:
                i = i + 1
                continue
            elif i == 1:
                for name in names:
                    typeStr = type(row[name]).__name__.capitalize()
                    typeArr.append(typeStr)
                i = i + 1
            else:
                break

        return names, typeArr

    def buildSchemaString(self, schemaTuple):

        schemaStr = """("""
        for i in range(len(schemaTuple[0])):
            if schemaTuple[1][i] == "int":
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "integer,"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "integer"
            elif schemaTuple[1][i] == "float":
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "real,"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "real"
            else:
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "varchar(100),"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "varchar(100)"


        schemaStr += """)"""

        return schemaStr

    def loadData(self, cur, filePath):
        cur.execute("COPY " + self.tableName + " FROM " + "'" + filePath + "'" + " DELIMITER ',' CSV HEADER")

    def checkForEntryByLatLon(self, lat, lon):
        """
        Check if an entry with the given lat, lon exists. If so, return all rows that match..
        :param lat:
        :param lon:
        :return:
        """
        if not self.connection is None:
            cur = self.connection.cursor()
            command = "SELECT * FROM " + self.tableName + " WHERE latitude = '" + str(lat) + "' AND longitude = '" + str(lon) + "';"
            cur.execute(command)
            rows = cur.fetchall()

            for row in rows:
                print(row)

            return rows
        else:
            print(
                "No connection open. Did you open a connection using getConnectFromKeywords() or getConnectFromConfig()?")

    def changeTable(self, newName):
        self.tableName = newName

dc = DatabaseConnector()
mConn = dc.getConnectFromKeywords(host='localhost', dbname='spatialpractice', username='postgres', password='Swa!Exa4')
mTable = Table(tableName='correcteddata', connection=mConn)
# mTable.buildTableFromFile('D:\\realcorrected.csv')
mTable.changeTable("superkitties3")
mTable.checkForEntryByLatLon(34.48845, 69.20288)
dc.closeConnection()
