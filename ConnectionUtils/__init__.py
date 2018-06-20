import psycopg2 as psy
from configparser import ConfigParser
import pandas as pd
import xlrd
import csv
import numpy as np

"""
TODO: Create tool for checking if a given row/entry already exists and insert it if it doesn't
Otherwise, decide whether to update (?)
"""

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

    def __init__(self, tableName, databaseConnector):
        self.tableName = tableName
        self.connector = databaseConnector
        self.table = None

        if databaseConnector.connection is None:
            print("Your connection does not exist. Please instantiate a connection using the DatabaseConnector and try again.")

    def buildTableFromTuple(self, commandTuple):
        """
        Build table(s) from a command(s)
        :return:
        """
        print("Attempting to build table.")

        commands = (commandTuple)
        try:
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                for command in commands:
                    cur.execute(command)
                cur.close()
                self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Building table failed.")
            print(error)

    def csvToXlsx(self, filePath):
        wb = xlrd.open_workbook(filePath)
        sh = wb.sheet_by_name(wb.sheet_names()[0])
        fileString = filePath[:-5]
        fileString += ".csv"
        csvfile = open(fileString, 'w', encoding='utf8')
        wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))

        csvfile.close()
        filePath = fileString
        return pd.read_csv(filePath)

    def buildTableFromFile(self, filePath):
        """
        Create a table on the database from a .xlsx or
        .csv file.
        :param filePath:
        :return:
        """
        if filePath.endswith('xlsx'):
            tableFile = self.csvToXlsx(filePath)
        elif filePath.endswith('csv'):
            tableFile = pd.read_csv(filePath)
        else:
            print('This tool currently only supports .csv files.')
            return

        print("Constructing query from file.")
        schemaTuple = self.loadTableSchema(tableFile)
        schemaStr = self.buildSchemaString(schemaTuple)

        schemaStr = "CREATE TABLE " + self.tableName + " " + schemaStr
        print(schemaStr)

        try:
            cur = self.connector.connection.cursor()

            cur.execute(schemaStr)

            self.loadData(cur, filePath)

            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Building table failed.")
            print(error)

    def makeTableSpatial(self):
        """
        Add a geometry column and make it spatial
        :return:
        """

        addGeom = "ALTER TABLE " + self.tableName + " ADD COLUMN geom geometry(POINT, 4326);"
        updateTable = "UPDATE " + self.tableName + " SET geom = ST_SETSRID(ST_MakePoint(Recorded_Lng, Recorded_Lat), 4326);"

        try:
            cur = self.connector.connection.cursor()
            cur.execute(addGeom)
            cur.close()
            cur = self.connector.connection.cursor()
            cur.execute(updateTable)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Unable to alter table.")
            print(error)

    def loadTableSchema(self, tableFile):
        """
        Use the pandas dataframe to generate a list of headers and types
        :param tableFile:
        :return:
        """
        names = list(tableFile.columns.values)
        keepArr = []
        i = 0
        for (index, row) in tableFile.iterrows():
            if i == 0:
                i = i + 1
                continue
            elif i == 1:
                for name in names:
                    typeStr = type(row[name]).__name__.capitalize()
                    keepArr.append(typeStr)
                i = i + 1
            else:
                typeArr = []
                for name in names:
                    typeStr = type(row[name]).__name__.capitalize()
                    typeArr.append(typeStr)

                for i in range(len(keepArr)):
                    if keepArr[i] != typeArr[i]:
                        keepArr[i] = "Str"

        return names, keepArr

    def buildSchemaString(self, schemaTuple):
        """
        Return string for use in queries
        :param schemaTuple:
        :return:
        """
        schemaStr = """("""
        for i in range(len(schemaTuple[0])):
            print(schemaTuple[1][i])
            if schemaTuple[1][i] == "Int":
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "integer,"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "integer"
            elif schemaTuple[1][i] == "Float":
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "numeric,"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "numeric"
            else:
                if not i == len(schemaTuple[0]) - 1:
                    schemaStr += schemaTuple[0][i] + " " + "varchar,"
                else:
                    schemaStr += schemaTuple[0][i] + " " + "varchar"


        schemaStr += """)"""

        return schemaStr

    def loadData(self, cur, filePath):
        """
        Load data from a file into an empty table.
        :param cur:
        :param filePath:
        :return:
        """
        try:
            cur.execute("COPY " + self.tableName + " FROM " + "'" + filePath + "'" + " DELIMITER ',' CSV HEADER")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to load data.")
            print(error)

    def checkForEntryByLatLon(self, lat, lon, searchRadius=0.5):
        """
        Check if an entry with the given lat, lon exists. If so, return all rows that match in a tuple where the first
        value is True or False for whether an entry exist, and the second value is the the rows.
        :param lat:
        :param lon:
        :return:
        """
        tBool = False
        rows = []
        try:
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.tableName + " WHERE ST_DWITHIN(ST_TRANSFORM(ST_GEOMFROMTEXT('POINT(" + str(lon) + " " + str(lat) + ")', 4326),4326)::geography, ST_TRANSFORM(geom, 4326)::geography, " + str(searchRadius) + ", true)"
                cur.execute(command)
                rows = cur.fetchall()

                cur.close()

                if len(rows) > 0:
                    tBool = True

            else:
                print(
                    "No connection open. Did you open a connection using getConnectFromKeywords() or getConnectFromConfig()?")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to get entry.")
            print(error)

        return tBool, rows

    def checkForEntryByCountryLoc(self, countryName, locationName):
        """
        Check if an entry exists with the given country and location. If so, return all rows that match in a
        tuple where the first value is True or False for whether an entry exist, and the second value is the the rows.
        :param countryName:
        :param locationName:
        :return:
        """
        print("Went to country")
        try:
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.tableName + " WHERE country = '" + countryName + "' AND location = '" + locationName + "';"
                cur.execute(command)
                rows = cur.fetchall()
                for row in rows:
                    print(row)
                cur.close()
                if len(rows) > 0:
                    return True, rows
                else:
                    return False, rows
            else:
                print("""No connection open. Did you open a connection using getConnectFromKeywords() 
                        or getConnectFromConfig()?""")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to get entries.")
            print(error)

    def changeTable(self, newName):
        """
        Switch to a different table without creating a new
        DatabaseConnector
        :param newName:
        :return:
        """
        self.tableName = newName

    def updateEntries(self, filePath):
        """
        Insert or update entries from a .csv file.
        :param filePath:
        :return:
        """
        if filePath.endswith('xlsx'):
            tableFile = self.csvToXlsx(filePath)
        elif filePath.endswith('csv'):
            tableFile = pd.read_csv(filePath)
        else:
            print('This tool currently only supports .csv files.')
            return
        try:
            for (index, row) in tableFile.iterrows():
                lat = row['Recorded_Lat']
                long = row['Recorded_Lng']
                if not self.checkForEntryByLatLon(lat, long)[0]:
                    countryName = row['Country']
                    locName = row['Location']
                    if not self.checkForEntryByCountryLoc(countryName, locName)[0]:
                        # Entry does not exist
                        print("Inserting")
                        cmndStr = ""
                        cmndArr = []
                        for item in row.values:
                            cmndArr.append(item)
                        cmnd = "INSERT INTO " + self.tableName + " VALUES (" + self.makeInsertionString(cmndArr) + " );"
                        cur = self.connector.connection.cursor()
                        cur.execute(cmnd)
                        cur.close()
            self.connector.connection.commit()
            self.checkGeomNulls()
        except (Exception, psy.DatabaseError) as error:
            print("Updating failed.")
            print(error)

    def makeInsertionString(self, valsArr):

        valsStr = ''
        for i in range(len(valsArr)-2):
            if isinstance(valsArr[i], str):
                valsStr += "'" + str(valsArr[i]) + "', "
            else:
                if valsArr[i] is None or pd.isnull(valsArr[i]) or valsArr[i] == np.nan:
                    valsStr += "NULL,"
                else:
                    valsStr += str(valsArr[i]) + ", "
        if isinstance(valsArr[len(valsArr)-1], str):
            valsStr += "'" + str(valsArr[len(valsArr)-1]) + "' "
        else:
            if valsArr[len(valsArr)-1] is None or pd.isnull(valsArr[len(valsArr)-1]) or valsArr[len(valsArr)-1] == np.nan:
                valsStr += "NULL"
            else:
                valsStr += str(valsArr[len(valsStr)-1]) + " "
        return valsStr

    def checkGeomNulls(self):
        """
        Check for null values in a spatial table and, if they exist, check the lat and lng
        values to generate geometry.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            if self.isSpatial():
                updateTable = "UPDATE " + self.tableName + """ SET geom = ST_SETSRID(ST_MakePoint(Recorded_Lng, 
                            Recorded_Lat), 4326) WHERE geom IS NULL;"""
                cur.execute(updateTable)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Failed to check for nulls.")
            print(error)

    def isSpatial(self):
        """
        Check if the given table is spatial.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "' AND column_name = 'geom';")
            names = cur.fetchall()
            cur.close()
            if len(names) > 0:
                return True
            return False
        except (Exception, psy.DatabaseError) as error:
            print("Unable to determine if table is spatial.")
            print(error)

    def commitChanges(self):
        """
        Commit changes made to the database.
        :return:
        """
        try:
            confirmation = input("Once these changes are committed, they cannot be undone. Proceed? (y/n): ")
            while confirmation is "y" or confirmation is "Y":
                confirmation = "n"
                if self.connector.connection is not None:
                    try:
                        self.connector.connection.commit()
                    except (Exception, psy.DatabaseError) as error:
                        print(error)
        except (Exception, psy.DatabaseError) as error:
            print("Failed to commit!")
            print(error)

    def getEntriesByInput(self, vals, columnNames):
        """
        Return all entries that match ALL search terms. Returns False
        if an error occurs
        :param vals:
        :return:
        """
        try:
            if not (isinstance(vals, list) and isinstance(columnNames, list)):
                print("Keywords must be passed in as a list of strings")
                return False
            if not len(vals) == len(columnNames):
                print("Keywords and columnNames lists must have the same length.")
                return False
            if not self.validateColumns(columnNames):
                print("Input column names are invalid.")
                return False
            else:
                requestVals = "(SELECT * FROM " + self.tableName + " WHERE "
                for i in range(len(vals)):
                    if not i == len(vals) - 1:
                        requestVals += columnNames[i] + "=" + "'" + vals[i] + "' AND "
                    else:
                        requestVals += columnNames[i] + "=" + "'" + vals[i] + "');"
                print("Request cmmnd is: " + requestVals)
                cur = self.connector.connection.cursor()
                cur.execute(requestVals)
                try:
                    rows = cur.fetchall()
                    cur.close()
                    print(rows)
                    return rows
                except AttributeError:
                    print("None found")
        except (Exception, psy.DatabaseError) as error:
            print("Getting entries failed.")
            print(error)

    def validateColumns(self, columnNames):
        """
        Validates whether all string in a list correlate to a valid
        column name in the table.
        :param columnNames:
        :return: True if all names exist in table, False if not
        """
        if not isinstance(columnNames, list):
            print("Names must be passed in as a list of strings.")
        else:
            cmmnd = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "';"
            print("validate cmmnd is: " + cmmnd)
            cur = self.connector.connection.cursor()
            cur.execute(cmmnd)
            nameList = list(cur.fetchall())
            cur.close()
            for name in columnNames:
                if not (name,) in nameList:
                    return False
        return True

    def getTable(self, limit=0):
        """
        Return a number of rows of the table. If limit=0, return all.
        :param limit:
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            if limit == 0:
                cmmnd = "SELECT * FROM " + self.tableName + ";"
            else:
                cmmnd = "SELECT * FROM " + self.tableName + " LIMIT " + str(limit) + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            return rows
        except (Exception, psy.DatabaseError) as error:
            print("Fetching table failed.")
            print(error)

    def checkValidity(self, worldTableName):
        """
        Validate using data in the database whether the entries in the table
        have the correct country.
        :param worldTableName:
        :return:
        """
        cur = self.connector.connection.cursor()
        cmmnd1 = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "' AND column_name = 'dtype';"
        cur.execute(cmmnd1)
        name = cur.fetchall()
        cur.close()

        if len(name) > 0:
            print("Already validated once. Revalidating.")
            cur = self.connector.connection.cursor()
            cmmnd = "UPDATE " + self.tableName + " SET dtype='Invalid' FROM " + self.tableName + ", " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + ".geom, " + worldTableName + ".geom) AND " + worldTableName + ".name_0  != " + self.tableName + ".country;"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.tableName + ", " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + ".geom, " + worldTableName + ".geom) AND " + worldTableName + ".name_0  != " + self.tableName + ".country;"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()
        else:
            cur = self.connector.connection.cursor()
            cmmnd = "ALTER TABLE " + self.tableName + " ADD dtype varchar;"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET dtype='Valid'"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET dtype='Invalid' FROM " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + ".geom, " + worldTableName + ".geom) AND " + worldTableName + ".name_0  != " + self.tableName + ".country;"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.tableName + ", " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + ".geom, " + worldTableName + ".geom) AND " + worldTableName + ".name_0  != " + self.tableName + ".country;"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()

        self.connector.connection.commit()

        return rows

mConnector = DatabaseConnector()
mConnector.getConnectFromConfig(filePath='D:\\config.ini')
mTable = Table('tester4', mConnector)
lines = mTable.checkValidity('world_map')
for line in lines:
    print(line)
print(len(lines))
mConnector.closeConnection()