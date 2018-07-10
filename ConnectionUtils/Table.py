import psycopg2 as psy
import pandas as pd
import xlrd
import csv
import numpy as np
from os import path

from tkinter import Tk, filedialog
from ConnectionUtils.DatabaseConnector import DatabaseConnector

mConnector = DatabaseConnector(filepath='hi')

class Table:

    def __init__(self, tableName, databaseConnector):
        self.tableName = tableName
        self.connector = databaseConnector
        self.table = None

        if databaseConnector.connection is None:
            print("Your connection does not exist. Please instantiate a connection using the DatabaseConnector and try again.")

    def table_from_tuple(self, commandTuple):
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

    def xlsx_to_csv(self, filePath):
        print("Converting .xlsx to .csv")
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

    def table_from_file(self, filePath=False):
        """
        Create a table on the database from a .xlsx or
        .csv file.
        :param filePath:
        :return:
        """
        if filePath is False or filePath == '':
            Tk().withdraw()
            filePath = filedialog.askopenfilename(title='Please select a .csv or .xlsx file')

        if filePath.endswith('xlsx'):
            tableFile = self.xlsx_to_csv(filePath)
        elif filePath.endswith('csv'):
            tableFile = pd.read_csv(filePath)
        else:
            print('This tool currently only supports .csv files.')
            return

        print("Constructing query from file.")
        schemaTuple = self.__load_schema(tableFile)
        schemaStr = self.__build_schema_string(schemaTuple)

        print("Creating table.")
        schemaStr = "CREATE TABLE " + self.tableName + " " + schemaStr
        print(schemaStr)

        try:
            cur = self.connector.connection.cursor()
            cur.execute(schemaStr)
            self.__load_data(cur, filePath)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Building table failed.")
            print(error)

    def make_spatial(self, lngColName='Longitude', latColName='Latitude', geomColName='geom'):
        """
        Add a geometry column and make it spatial
        :return:
        """

        addGeom = "ALTER TABLE " + self.tableName + " ADD COLUMN " + geomColName + " geometry(POINT, 4326);"
        updateTable = "UPDATE " + self.tableName + " SET geom = ST_SETSRID(ST_MakePoint(" + lngColName + ", " + latColName + "), 4326);"

        try:
            print("Adding geometry column to table.")
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

    def __load_schema(self, tableFile):
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

    def __build_schema_string(self, schemaTuple):
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

    def __load_data(self, cur, filePath):
        """
        Load data from a file into an empty table.
        :param cur:
        :param filePath:
        :return:
        """
        try:
            print("Loading data from file.")
            cur.execute("COPY " + self.tableName + " FROM " + "'" + filePath + "'" + " DELIMITER ',' CSV HEADER")
            cur.close()
        except (Exception, psy.DatabaseError) as error:
            print("Failed to load data.")
            print(error)

    def check_by_latlng(self, lat, lon, searchRadius=300000, geomColName='geom'):
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
            print("Attempting to find entry.")
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.tableName + " WHERE ST_DWITHIN(ST_TRANSFORM(ST_GEOMFROMTEXT('POINT(" + str(lon) + " " + str(lat) + ")', 4326),4326)::geography, ST_TRANSFORM(" + geomColName + ", 4326)::geography, " + str(searchRadius) + ", true);"
                cur.execute(command)
                rows = cur.fetchall()

                cur.close()

                if len(rows) > 0:
                    print("Found")
                    tBool = True
                else:
                    print("No matching entries found.")
            else:
                print(
                    "No connection open. Did you open a connection using getConnectFromKeywords() or getConnectFromConfig()?")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to get entry.")
            print(error)

        return tBool, rows

    def check_by_countryloc(self, countryName, locationName, countryColName='country', locationColName='location'):
        """
        Check if an entry exists with the given country and location. If so, return all rows that match in a
        tuple where the first value is True or False for whether an entry exist, and the second value is the the rows.
        :param countryName:
        :param locationName:
        :return:
        """
        try:
            print("Attempting to find entry.")
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.tableName + " WHERE " + countryColName + " = '" + countryName + "' AND " + locationColName + " = '" + locationName + "';"
                cur.execute(command)
                rows = cur.fetchall()
                for row in rows:
                    print(row)
                cur.close()
                if len(rows) > 0:
                    return True, rows
                else:
                    print("No matching entries found.")
                    return False, rows
            else:
                print("""No connection open. Did you open a connection using getConnectFromKeywords() 
                        or getConnectFromConfig()?""")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to get entries.")
            print(error)

    def change_table(self, newName):
        """
        Switch to a different table without creating a new
        DatabaseConnector
        :param newName:
        :return:
        """
        print("Active table is now " + newName)
        self.tableName = newName

    def update_entries(self, lngColName='longitude', latColName='latitude', countryColName='country', locationColName='location', filePath=False):
        """
        Insert or update entries from a .csv file.
        :param filePath:
        :return:
        """
        if filePath is False or filePath == '':
            Tk().withdraw()
            filePath = filedialog.askopenfilename(title='Please select a file')

        if filePath.endswith('xlsx'):
            tableFile = self.xlsx_to_csv(filePath)
        elif filePath.endswith('csv'):
            tableFile = pd.read_csv(filePath)
        else:
            print('This tool currently only supports .csv and .xlsx files.')
            return
        try:
            for (index, row) in tableFile.iterrows():
                lat = row[latColName]
                long = row[lngColName]
                countryName = row[countryColName]
                locName = row[locationColName]
                if not self.check_by_countryloc(countryName, locName)[0]:
                    # Entry does not exist
                    print("Entry does not exist.")
                    print("Inserting new entry")
                    cmndArr = []
                    for item in row.values:
                        cmndArr.append(item)
                    cmnd = "INSERT INTO " + self.tableName + " VALUES (" + self.__build_insertion_string(cmndArr) + " );"
                    cur = self.connector.connection.cursor()
                    cur.execute(cmnd)
                    cur.close()
                else:
                    print("Entry exists.")
                    print("Updating existing entry")
                    cmmnd = "UPDATE " + self.tableName + " SET " + latColName + " = '" + str(lat) + "', " + lngColName + " = '" + str(long) + """' WHERE 
                    """ + countryColName + " = '" + countryName + "' AND " + locationColName + " = '" + locName + "';"
                    cur = self.connector.connection.cursor()
                    cur.execute(cmmnd)
                    cmmnd2 = "UPDATE " + self.tableName + " SET geom = ST_SETSRID(ST_MakePoint(" + lngColName + ", " + latColName + """), 4326) 
                    WHERE """ + countryColName + " = '" + countryName + "' AND " + locationColName + " = '" + locName + "';"
                    cur.execute(cmmnd2)
                    cur.close()
            self.connector.connection.commit()
            self.__check_geom_nulls()
        except (Exception, psy.DatabaseError) as error:
            print("Updating failed.")
            print(error)

    def __build_insertion_string(self, valsArr):
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

    def __check_geom_nulls(self, lngColName='Longitude', latColName='Latitude', geomColName='geom'):
        """
        Check for null values in a spatial table and, if they exist, check the lat and lng
        values to generate geometry.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            if self.is_spatial():
                updateTable = "UPDATE " + self.tableName + """ SET """ + geomColName + """= ST_SETSRID(ST_MakePoint(""" + lngColName + """, 
                            """ + latColName + """), 4326) WHERE """ + geomColName + """ IS NULL;"""
                cur.execute(updateTable)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Failed to check for nulls.")
            print(error)

    def is_spatial(self, geomColName='geom'):
        """
        Check if the given table is spatial.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "' AND column_name = '" + geomColName + "';")
            names = cur.fetchall()
            cur.close()
            if len(names) > 0:
                return True
            return False
        except (Exception, psy.DatabaseError) as error:
            print("Unable to determine if table is spatial.")
            print(error)

    def commit_changes(self):
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

    def entries_by_input(self, vals, columnNames):
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
            if not self.__validate_columns(columnNames):
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

    def __validate_columns(self, columnNames):
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
            cur = self.connector.connection.cursor()
            cur.execute(cmmnd)
            nameList = list(cur.fetchall())
            print(nameList)
            cur.close()
            for name in columnNames:
                print(name)
                if not (name,) in nameList:
                    return False
        return True

    def get_table(self, limit=5):
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

    def check_validity(self, worldTableName, setTypeColName='dtype', setFoundCountryName='dbCountry', pointsGeomColName='geom', worldGeomColName='geom', worldCountryCodeColName='gid_0', pointsCountryCodeColName='country_code', worldCountryNameColName='name_0'):
        """
        Validate using data in the database whether the entries in the table
        have the correct country.
        :param worldTableName:
        :return:
        """
        cur = self.connector.connection.cursor()
        cmmnd1 = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "' AND column_name = '" + setTypeColName + "';"
        cur.execute(cmmnd1)
        name = cur.fetchall()
        cur.close()

        if len(name) > 0:
            print("Already validated once. Revalidating.")
            cur = self.connector.connection.cursor()
            cmmnd = "UPDATE " + self.tableName + " SET " + setTypeColName + "='Invalid' FROM " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET " + setFoundCountryName + "=" + worldTableName + "." + worldCountryNameColName + " FROM " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.tableName + ", " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()
        else:
            print("Not validated yet. Generating dtype column.")
            cur = self.connector.connection.cursor()
            cmmnd = "ALTER TABLE " + self.tableName + " ADD " + setTypeColName + " varchar;"
            cur.execute(cmmnd)
            cmmnd = "ALTER TABLE " + self.tableName + " ADD " + setFoundCountryName + " varchar;"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET " + setTypeColName + "='Valid'"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET " + setTypeColName + "='Invalid' FROM " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.tableName + " SET " + setFoundCountryName + "=" + worldTableName + "." + worldCountryNameColName + " FROM " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.tableName + ", " + worldTableName + " WHERE ST_WITHIN(" + self.tableName + "." + pointsGeomColName + ", " + worldTableName + "." + worldGeomColName + ") AND " + worldTableName + "." + worldCountryCodeColName + "  != " + self.tableName + "." + pointsCountryCodeColName + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()

        self.connector.connection.commit()

        return rows

    def table_to_csv(self, fileName):
        namesList = []
        valsList = []
        cmmnd1 = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.tableName + "';"
        cmmnd2 = "SELECT * FROM " + self.tableName + ";"

        cur = self.connector.connection.cursor()
        cur.execute(cmmnd1)
        names = cur.fetchall()
        cur.close()

        cur = self.connector.connection.cursor()
        cur.execute(cmmnd2)
        rows = cur.fetchall()
        cur.close()

        for tTuple in names:
            namesList.append(tTuple[0])

        i = 0
        for row in rows:
            print(row)
            valsList.append(row)
            i += 1
        df = pd.DataFrame(data=valsList, columns=namesList)
        filePath = str(path.abspath(path.join(path.dirname(__file__), '..', 'resources', 'csv', fileName)))

        df.to_csv(filePath, sep=',', encoding='utf-8', index=False)

