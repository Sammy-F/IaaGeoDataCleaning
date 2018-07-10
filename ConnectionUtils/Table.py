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
        self.table_name = tableName
        self.connector = databaseConnector
        self.table = None

        if databaseConnector.connection is None:
            print("Your connection does not exist. Please instantiate a connection using the DatabaseConnector and try again.")

    def table_from_tuple(self, command_tuple):
        """
        Build table(s) from a command(s)
        :return:
        """
        print("Attempting to build table.")

        commands = (command_tuple)
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

    def xlsx_to_csv(self, file_path):
        print("Converting .xlsx to .csv")
        wb = xlrd.open_workbook(file_path)
        sh = wb.sheet_by_name(wb.sheet_names()[0])
        fileString = file_path[:-5]
        fileString += ".csv"
        csvfile = open(fileString, 'w', encoding='utf8')
        wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))

        csvfile.close()
        file_path = fileString
        return pd.read_csv(file_path)

    def table_from_file(self, file_path=False):
        """
        Create a table on the database from a .xlsx or
        .csv file.
        :param file_path:
        :return:
        """
        if file_path is False or file_path == '':
            Tk().withdraw()
            file_path = filedialog.askopenfilename(title='Please select a .csv or .xlsx file')

        if file_path.endswith('xlsx'):
            tableFile = self.xlsx_to_csv(file_path)
        elif file_path.endswith('csv'):
            tableFile = pd.read_csv(file_path)
        else:
            print('This tool currently only supports .csv files.')
            return

        print("Constructing query from file.")
        schemaTuple = self.__load_schema(tableFile)
        schemaStr = self.__build_schema_string(schemaTuple)

        print("Creating table.")
        schemaStr = "CREATE TABLE " + self.table_name + " " + schemaStr
        print(schemaStr)

        try:
            cur = self.connector.connection.cursor()
            cur.execute(schemaStr)
            self.__load_data(cur, file_path)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Building table failed.")
            print(error)

    def make_spatial(self, lngcol_name='Longitude', latcol_name='Latitude', geomcol_name='geom'):
        """
        Add a geometry column and make it spatial
        :return:
        """

        addGeom = "ALTER TABLE " + self.table_name + " ADD COLUMN " + geomcol_name + " geometry(POINT, 4326);"
        updateTable = "UPDATE " + self.table_name + " SET geom = ST_SETSRID(ST_MakePoint(" + lngcol_name + ", " + latcol_name + "), 4326);"

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

    def __load_schema(self, table_file):
        """
        Use the pandas dataframe to generate a list of headers and types
        :param table_file:
        :return:
        """
        names = list(table_file.columns.values)
        keep_arr = []
        i = 0
        for (index, row) in table_file.iterrows():
            if i == 0:
                i = i + 1
                continue
            elif i == 1:
                for name in names:
                    type_str = type(row[name]).__name__.capitalize()
                    keep_arr.append(type_str)
                i = i + 1
            else:
                type_arr = []
                for name in names:
                    type_str = type(row[name]).__name__.capitalize()
                    type_arr.append(type_str)

                for i in range(len(keep_arr)):
                    if keep_arr[i] != type_arr[i]:
                        keep_arr[i] = "Str"

        return names, keep_arr

    def __build_schema_string(self, schema_tuple):
        """
        Return string for use in queries
        :param schema_tuple:
        :return:
        """
        schema_str = """("""
        for i in range(len(schema_tuple[0])):
            print(schema_tuple[1][i])
            if schema_tuple[1][i] == "Int":
                if not i == len(schema_tuple[0]) - 1:
                    schema_str += schema_tuple[0][i] + " " + "integer,"
                else:
                    schema_str += schema_tuple[0][i] + " " + "integer"
            elif schema_tuple[1][i] == "Float":
                if not i == len(schema_tuple[0]) - 1:
                    schema_str += schema_tuple[0][i] + " " + "numeric,"
                else:
                    schema_str += schema_tuple[0][i] + " " + "numeric"
            else:
                if not i == len(schema_tuple[0]) - 1:
                    schema_str += schema_tuple[0][i] + " " + "varchar,"
                else:
                    schema_str += schema_tuple[0][i] + " " + "varchar"
        schema_str += """)"""

        return schema_str

    def __load_data(self, cur, file_path):
        """
        Load data from a file into an empty table.
        :param cur:
        :param file_path:
        :return:
        """
        try:
            print("Loading data from file.")
            cur.execute("COPY " + self.table_name + " FROM " + "'" + file_path + "'" + " DELIMITER ',' CSV HEADER")
            cur.close()
        except (Exception, psy.DatabaseError) as error:
            print("Failed to load data.")
            print(error)

    def check_by_latlng(self, lat, lon, search_radius=300000, geomcol_name='geom'):
        """
        Check if an entry with the given lat, lon exists. If so, return all rows that match in a tuple where the first
        value is True or False for whether an entry exist, and the second value is the the rows.
        :param lat:
        :param lon:
        :return:
        """
        found = False
        rows = []
        try:
            print("Attempting to find entry.")
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.table_name + " WHERE ST_DWITHIN(ST_TRANSFORM(ST_GEOMFROMTEXT('POINT(" + str(lon) + " " + str(lat) + ")', 4326),4326)::geography, ST_TRANSFORM(" + geomcol_name + ", 4326)::geography, " + str(search_radius) + ", true);"
                cur.execute(command)
                rows = cur.fetchall()

                cur.close()

                if len(rows) > 0:
                    print("Found")
                    found = True
                else:
                    print("No matching entries found.")
            else:
                print(
                    "No connection open. Did you open a connection using getConnectFromKeywords() or getConnectFromConfig()?")
        except (Exception, psy.DatabaseError) as error:
            print("Failed to get entry.")
            print(error)

        return found, rows

    def check_by_countryloc(self, country_name, location_name, countrycol_name='country', locationcol_name='location'):
        """
        Check if an entry exists with the given country and location. If so, return all rows that match in a
        tuple where the first value is True or False for whether an entry exist, and the second value is the the rows.
        :param country_name:
        :param location_name:
        :return:
        """
        try:
            print("Attempting to find entry.")
            if not self.connector.connection is None:
                cur = self.connector.connection.cursor()
                command = "SELECT * FROM " + self.table_name + " WHERE " + countrycol_name + " = '" + country_name + "' AND " + locationcol_name + " = '" + location_name + "';"
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

    def change_table(self, new_table):
        """
        Switch to a different table without creating a new
        DatabaseConnector
        :param new_table:
        :return:
        """
        print("Active table is now " + new_table)
        self.table_name = new_table

    def update_entries(self, lngcol_name='longitude', latcol_name='latitude', countrycol_name='country', locationcol_name='location', file_path=False):
        """
        Insert or update entries from a .csv file.
        :param file_path:
        :return:
        """
        if file_path is False or file_path == '':
            Tk().withdraw()
            file_path = filedialog.askopenfilename(title='Please select a file')

        if file_path.endswith('xlsx'):
            tableFile = self.xlsx_to_csv(file_path)
        elif file_path.endswith('csv'):
            tableFile = pd.read_csv(file_path)
        else:
            print('This tool currently only supports .csv and .xlsx files.')
            return
        try:
            for (index, row) in tableFile.iterrows():
                lat = row[latcol_name]
                long = row[lngcol_name]
                country_name = row[countrycol_name]
                loc_name = row[locationcol_name]
                if not self.check_by_countryloc(country_name, loc_name)[0]:
                    # Entry does not exist
                    print("Entry does not exist.")
                    print("Inserting new entry")
                    cmnd_arr = []
                    for item in row.values:
                        cmnd_arr.append(item)
                    cmnd = "INSERT INTO " + self.table_name + " VALUES (" + self.__build_insertion_string(cmnd_arr) + " );"
                    cur = self.connector.connection.cursor()
                    cur.execute(cmnd)
                    cur.close()
                else:
                    print("Entry exists.")
                    print("Updating existing entry")
                    cmmnd = "UPDATE " + self.table_name + " SET " + latcol_name + " = '" + str(lat) + "', " + lngcol_name + " = '" + str(long) + """' WHERE 
                    """ + countrycol_name + " = '" + country_name + "' AND " + locationcol_name + " = '" + loc_name + "';"
                    cur = self.connector.connection.cursor()
                    cur.execute(cmmnd)
                    cmmnd2 = "UPDATE " + self.table_name + " SET geom = ST_SETSRID(ST_MakePoint(" + lngcol_name + ", " + latcol_name + """), 4326) 
                    WHERE """ + countrycol_name + " = '" + country_name + "' AND " + locationcol_name + " = '" + loc_name + "';"
                    cur.execute(cmmnd2)
                    cur.close()
            self.connector.connection.commit()
            self.__check_geom_nulls()
        except (Exception, psy.DatabaseError) as error:
            print("Updating failed.")
            print(error)

    def __build_insertion_string(self, vals_arr):
        vals_str = ''
        for i in range(len(vals_arr) - 2):
            if isinstance(vals_arr[i], str):
                vals_str += "'" + str(vals_arr[i]) + "', "
            else:
                if vals_arr[i] is None or pd.isnull(vals_arr[i]) or vals_arr[i] == np.nan:
                    vals_str += "NULL,"
                else:
                    vals_str += str(vals_arr[i]) + ", "
        if isinstance(vals_arr[len(vals_arr) - 1], str):
            vals_str += "'" + str(vals_arr[len(vals_arr) - 1]) + "' "
        else:
            if vals_arr[len(vals_arr) - 1] is None or pd.isnull(vals_arr[len(vals_arr) - 1]) or vals_arr[len(vals_arr) - 1] == np.nan:
                vals_str += "NULL"
            else:
                vals_str += str(vals_arr[len(vals_str) - 1]) + " "
        return vals_str

    def __check_geom_nulls(self, lngcol_name='Longitude', latcol_name='Latitude', geomcol_name='geom'):
        """
        Check for null values in a spatial table and, if they exist, check the lat and lng
        values to generate geometry.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            if self.is_spatial():
                update_table = "UPDATE " + self.table_name + """ SET """ + geomcol_name + """= ST_SETSRID(ST_MakePoint(""" + lngcol_name + """, 
                            """ + latcol_name + """), 4326) WHERE """ + geomcol_name + """ IS NULL;"""
                cur.execute(update_table)
            cur.close()
            self.connector.connection.commit()
        except (Exception, psy.DatabaseError) as error:
            print("Failed to check for nulls.")
            print(error)

    def is_spatial(self, geomcol_name='geom'):
        """
        Check if the given table is spatial.
        :return:
        """
        try:
            cur = self.connector.connection.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.table_name + "' AND column_name = '" + geomcol_name + "';")
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

    def entries_by_input(self, vals, column_names):
        """
        Return all entries that match ALL search terms. Returns False
        if an error occurs
        :param vals:
        :return:
        """
        try:
            if not (isinstance(vals, list) and isinstance(column_names, list)):
                print("Keywords must be passed in as a list of strings")
                return False
            if not len(vals) == len(column_names):
                print("Keywords and columnNames lists must have the same length.")
                return False
            if not self.__validate_columns(column_names):
                print("Input column names are invalid.")
                return False
            else:
                request_vals = "(SELECT * FROM " + self.table_name + " WHERE "
                for i in range(len(vals)):
                    if not i == len(vals) - 1:
                        request_vals += column_names[i] + "=" + "'" + vals[i] + "' AND "
                    else:
                        request_vals += column_names[i] + "=" + "'" + vals[i] + "');"
                print("Request cmmnd is: " + request_vals)
                cur = self.connector.connection.cursor()
                cur.execute(request_vals)
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

    def __validate_columns(self, column_names):
        """
        Validates whether all string in a list correlate to a valid
        column name in the table.
        :param column_names:
        :return: True if all names exist in table, False if not
        """
        if not isinstance(column_names, list):
            print("Names must be passed in as a list of strings.")
        else:
            cmmnd = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.table_name + "';"
            cur = self.connector.connection.cursor()
            cur.execute(cmmnd)
            nameList = list(cur.fetchall())
            print(nameList)
            cur.close()
            for name in column_names:
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
                cmmnd = "SELECT * FROM " + self.table_name + ";"
            else:
                cmmnd = "SELECT * FROM " + self.table_name + " LIMIT " + str(limit) + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            return rows
        except (Exception, psy.DatabaseError) as error:
            print("Fetching table failed.")
            print(error)

    def check_validity(self, world_table_name, new_typecol_name='dtype', new_foundcountrycol_name='dbCountry', points_geomcol_name='geom', world_geomcol_name='geom', wolrd_countrycodecol_name='gid_0', points_countrycodecol_name='country_code', world_countrynamecol_name='name_0'):
        """
        Validate using data in the database whether the entries in the table
        have the correct country.
        :param world_table_name:
        :return:
        """
        cur = self.connector.connection.cursor()
        cmmnd1 = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.table_name + "' AND column_name = '" + new_typecol_name + "';"
        cur.execute(cmmnd1)
        name = cur.fetchall()
        cur.close()

        if len(name) > 0:
            print("Already validated once. Revalidating.")
            cur = self.connector.connection.cursor()
            cmmnd = "UPDATE " + self.table_name + " SET " + new_typecol_name + "='Invalid' FROM " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.table_name + " SET " + new_foundcountrycol_name + "=" + world_table_name + "." + world_countrynamecol_name + " FROM " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.table_name + ", " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()
        else:
            print("Not validated yet. Generating dtype column.")
            cur = self.connector.connection.cursor()
            cmmnd = "ALTER TABLE " + self.table_name + " ADD " + new_typecol_name + " varchar;"
            cur.execute(cmmnd)
            cmmnd = "ALTER TABLE " + self.table_name + " ADD " + new_foundcountrycol_name + " varchar;"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.table_name + " SET " + new_typecol_name + "='Valid'"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.table_name + " SET " + new_typecol_name + "='Invalid' FROM " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            cmmnd = "UPDATE " + self.table_name + " SET " + new_foundcountrycol_name + "=" + world_table_name + "." + world_countrynamecol_name + " FROM " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            cmmnd = "SELECT * FROM " + self.table_name + ", " + world_table_name + " WHERE ST_WITHIN(" + self.table_name + "." + points_geomcol_name + ", " + world_table_name + "." + world_geomcol_name + ") AND " + world_table_name + "." + wolrd_countrycodecol_name + "  != " + self.table_name + "." + points_countrycodecol_name + ";"
            cur.execute(cmmnd)
            rows = cur.fetchall()
            cur.close()

        self.connector.connection.commit()

        return rows

    def table_to_csv(self, file_name):
        names_list = []
        vals_list = []
        cmmnd1 = "SELECT column_name FROM information_schema.columns WHERE table_name = '" + self.table_name + "';"
        cmmnd2 = "SELECT * FROM " + self.table_name + ";"

        cur = self.connector.connection.cursor()
        cur.execute(cmmnd1)
        names = cur.fetchall()
        cur.close()

        cur = self.connector.connection.cursor()
        cur.execute(cmmnd2)
        rows = cur.fetchall()
        cur.close()

        for tTuple in names:
            names_list.append(tTuple[0])

        i = 0
        for row in rows:
            print(row)
            vals_list.append(row)
            i += 1
        df = pd.DataFrame(data=vals_list, columns=names_list)
        file_path = str(path.abspath(path.join(path.dirname(__file__), '..', 'resources', 'csv', file_name)))

        df.to_csv(file_path, sep=',', encoding='utf-8', index=False)

