import math
import pandas as pd
import re
import os
import sys
from ..CleaningUtils.GeocodeValidator import GeocodeValidator

"""
GeocodeValidator allows the user to perform reverse geocoding
on a .xlsx or .csv to ensure that input locations correspond to
the correct latitude and longitude. If not, then basic data cleaning
is performed to check for human error.

Created by Jonathan Scott

Modified by: Samantha Fritsche, Thy Nguyen 6/7/2018

Some code by Martin Valgur @ StackOverflow was adapted to create this program.
See his original at: https://gis.stackexchange.com/questions/212796/get-lat-lon-extent-of-country-from-name-using-python

Note that some borders used are disputed
"""


regex = re.compile(' \(\d\)')


class TableTool:
    def __init__(self, file_path=None, map_file=None, outfile_type='.csv', loc_col='Location', ctry_col='Country',
                 reg_col='Region', lat_col='Latitude', lng_col='Longitude'):
        """
        Initializes a TableTools object to clean, query, or validate latitudinal and longitudinal inputs.

        :param file_path: the file path of the data being used.
        :param outfile_type: the extension of all output files to be produced.
        :param loc_col: the name of the location column.
        :param ctry_col: the name of the country column.
        :param reg_col: the name of the region column.
        :param lat_col: the name of the latitude column.
        :param lng_col: the name of the latitude column.
        """
        # TODO: should we include tblLocation.xlsx in the package?
        if not file_path:
            file_path = str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'xlsx',
                                                         'tblLocation.xlsx')))
        if not map_file:
            map_file = str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'mapinfo',
                                                        'TM_WORLD_BORDERS-0.3.shp')))
        self.file_path = file_path
        self.df = self.read_file(self.file_path)
        self.validator = GeocodeValidator(map_file)

        # Checking to see whether the columns actually exist in the data frame
        if {loc_col, ctry_col, reg_col, lat_col, lng_col}.issubset(self.df.columns):
            self.loc_col = loc_col
            self.ctry_col = ctry_col
            self.reg_col = reg_col
            self.lat_col = lat_col
            self.lng_col = lng_col

        else:
            raise KeyError('Column names not found in table.')

        # Checking to see the output file extension is supported or not
        if outfile_type != '.csv' and outfile_type != '.xlsx':
            raise TypeError('Support is only available for .xlsx and .csv files.')

        self.outfile_type = outfile_type

        # Creating a new directory if none has been created for output files.
        self.directory = str(os.path.abspath(os.path.join(os.path.dirname(__file__),'..',
                                                          os.path.splitext(os.path.basename(self.file_path))[0])))
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def read_file(self, file_path):
        """
        Reads in csv or excel file. Raises an error if a different file type was entered.

        :param file_path: .csv or .xlsx
        :return: a pandas data frame.
        """
        if file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            raise TypeError('Support is only available for .xlsx and .csv files.')
        return data

    def export_file(self, df, outfile, directory):
        """
        Exports the input data frame to the designated directory and outfile type.

        :param df: the data frame
        :param outfile: name of the output file
        :param directory: name of the directory
        :return:
        """
        outfile = outfile + self.outfile_type
        file_path = str(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', directory, outfile)))

        if outfile.endswith('.csv'):
            df.to_csv(file_path, index_label='Index', sep=',', encoding='utf-8')
        elif outfile.endswith('.xlsx'):
            df.to_excel(file_path, index_label='Index')
        else:
            raise TypeError('Support is only available for .xlsx and .csv files.')
        print('Finished exporting. File can be found at: %s' % file_path)

    def query_table(self, loc=None, ctry=None, lat=None, lng=None):
        """
        Queries the table for entries that match the conditions. Conditions must be:

        - Location, country, latitude, longitude

        - Location or country

        - Location and country

        - Latitude and longitude

        :param loc:
        :param ctry:
        :param lat:
        :param lng:
        :return: the indices of the entries matching the query.
        """
        loc_in = self.cell_in_table(loc, self.df[self.loc_col].tolist())
        ctry_in = self.cell_in_table(ctry, self.df[self.ctry_col].tolist())
        lat_in = self.cell_in_table(lat, self.df[self.lat_col].tolist())
        lng_in = self.cell_in_table(lng, self.df[self.lng_col].tolist())

        if loc and ctry and lat and lng:
            indices = list(set(loc_in) & set(ctry_in) & set(lat_in) & set(lng_in))
        elif loc and ctry:
            indices = list(set(loc_in) & set(ctry_in))
        elif lat and lng:
            indices = list(set(lat_in) & set(lng_in))
        elif loc:
            indices = loc_in
        elif ctry:
            indices = ctry_in
        else:
            raise TypeError('Not enough arguments provided.')
        return indices

    def cell_in_table(self, value, col_list):
        """
        Checks to see whether a cell with a certain value exists in the column.

        :param value: the condition being checked for.
        :param col_list: all of the entries in the column in a list.
        :return: a list of indices of rows with the value.
        """
        val_in = []
        if pd.notnull(value):
            if isinstance(value, float):
                val_in = [idx for idx, val in enumerate(col_list) if math.isclose(value, val, abs_tol=1e-1)]
            elif isinstance(value, str):
                val_in = [idx for idx, val in enumerate(col_list) if regex.sub('', value.lower()) == regex.sub('', str(val).lower())]
            else:
                raise TypeError('Type unsupported in the data frame.')
        return val_in

    def verify_by_indices(self, indices):
        """
        Verifies certain rows in the data frame given the indices and exports the results to a separate file.

        :param indices: all of the indices being checked for in a list.
        :return:
        """
        if not (isinstance(indices, list) or isinstance(indices, tuple)):
            indices = [indices]
        results = []
        for idx in indices:
            row = self.verify_row(idx)
            if row:
                results.append(row[1])

        if results:
            df = pd.DataFrame(results)
            df = df.set_index('Index')
            self.export_file(df, 'validation_result', self.directory)

    def verify_by_value(self, loc=None, ctry=None, lat=None, lng=None):
        """
        Verifies certain rows in the data frame using location, country, latitude, or longitude conditions,
        exports the results to a separate file.

        :param loc:
        :param ctry:
        :param lat:
        :param lng:
        :return:
        """
        indices = self.query_table(loc, ctry, lat, lng)
        self.verify_by_indices(indices)

    def verify_row(self, index):
        """
        Verifies a single row in the data frame.

        :param index: index of the row.
        :return: a tuple containing the type of entry and the information of the row represented in a dictionary.
        """
        try:
            loc = self.df.iloc[index][self.loc_col]
            ctry = self.df.iloc[index][self.ctry_col]
            reg = self.df.iloc[index][self.reg_col]
            lat = self.df.iloc[index][self.lat_col]
            lng = self.df.iloc[index][self.lng_col]

            row_info = self.validator.verify_info(loc, ctry, reg, lat, lng)
            row_info[1]['Index'] = index
            return row_info
        except IndexError:
            return None

    def clean_table(self):
        """
        Runs through the entire data frame and verifies all of the entries,
        exports 3 output files: verified entries, pending entries, and repeated entries.

        :return: the percentage of entries that could not be validated/geocoded.
        """
        # Variables for logging data
        logs = {'verified_entries': [], 'pending_entries': [], 'repeated_entries': []}
        flagged_indices = []

        # Iterating through the rows to clean data
        for (index, row) in self.df.iterrows():
            print('Verifying at index: ', index)
            location = str(row[self.loc_col])
            country = str(row[self.ctry_col])

            # Checking to see whether entry already exists
            all_loc = [dct['Location'] for dct in logs['verified_entries']]
            all_ctry = [dct['Country'] for dct in logs['verified_entries']]

            loc_in_table = self.cell_in_table(value=location, col_list=all_loc)
            ctry_in_table = self.cell_in_table(value=country, col_list=all_ctry)
            in_table = set(loc_in_table) & set(ctry_in_table)

            # Saving the entry in the repeated log if it has already been validated
            if in_table:
                for idx in in_table:
                    row = logs['verified_entries'][idx]
                    row['Index'] = index
                    row['ver_Index'] = idx
                    logs['repeated_entries'].append(row)
            # Verifying it using the geocode validator if not
            else:
                row = self.verify_row(index)
                row[1]['Index'] = index
                if row[0] >= 0:
                    logs['verified_entries'].append(row[1])
                else:
                    logs['pending_entries'].append(row[1])
                    flagged_indices.append(index)

        # Exporting the results
        for k, v in logs.items():
            df = pd.DataFrame(v)
            df = df.set_index('Index')
            self.export_file(df, k, self.directory)

        return len(flagged_indices) / (1e-10 + len(self.df))

    def add_entry(self, loc, ctry, reg, lat, lng):
        """
        Adds a new row to the data frame and overwrites the input file if successfully added.

        :param loc:
        :param ctry:
        :param reg:
        :param lat:
        :param lng:
        :return: a tuple containing the type of entry and the information of the row represented in a dictionary.
        """
        loc_in_table = self.cell_in_table(value=loc, col_list=list(self.df[self.loc_col]))
        ctry_in_table = self.cell_in_table(value=ctry, col_list=list(self.df[self.loc_col]))
        in_table = set(loc_in_table) & set(ctry_in_table)

        if in_table:
            results = []
            for idx in in_table:
                results.append(dict(self.df.iloc[idx]))
            return results
        else:
            row = self.validator.verify_info(loc, ctry, reg, lat, lng)
            if row[0] >= 0:
                index = len(self.df)
                for k, v in row[1].items():
                    self.df.loc[index, k] = v
                self.export_file(self.df, self.file_path, self.directory)
            return row