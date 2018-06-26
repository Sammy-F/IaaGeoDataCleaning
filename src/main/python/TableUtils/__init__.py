import math
import pandas as pd
import re
import os
from src.main.python.IaaGeoDataCleaning import verify, filenames


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


class TableTools:
    def __init__(self, file_path=str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                                                                  'resources', 'xlsx', 'verified_entries.xlsx'))),
                 loc_col='Location', ctry_col='Country', reg_col ='Region', lat_col='Latitude', lng_col='Longitude'):
        self.file_path = file_path
        self.df = self.read_file(self.file_path)
        self.validator = verify.GeocodeValidator()
        self.directory = os.path.splitext(os.path.basename(self.file_path))[0]
        # os.mkdir(self.directory)

        if {loc_col, ctry_col, reg_col, lat_col, lng_col}.issubset(self.df.columns):
            self.loc_col = loc_col
            self.ctry_col = ctry_col
            self.reg_col = reg_col
            self.lat_col = lat_col
            self.lng_col = lng_col

        else:
            raise KeyError('Column names not found in table.')

    def read_file(self, file_path):
        """
        Reads in csv or excel file.
        :param file_path:
        :return: a pandas data frame.
        """
        if file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            raise TypeError('Support is only available for .xlsx and .csv files.')
        return data

    def export_file(self, df, outfile, directory, file_type):
        outfile = outfile + file_type
        file_path = str(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', directory, outfile)))

        if outfile.endswith('.csv'):
            df.to_csv(file_path, index_label='Index', sep=',', encoding='utf-8')
        elif outfile.endswith('.xlsx'):
            df.to_excel(file_path, index_label='Index')
        else:
            raise TypeError('Support is only available for .xlsx and .csv files.')
        print('Finished exporting. File can be found at: %s' % file_path)

    def query_table(self, loc=None, ctry=None, lat=None, lng=None):
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
        else:
            raise TypeError('Not enough arguments provided.')
        return indices

    def cell_in_table(self, value, col_list):
        val_in = []
        if pd.notnull(value):
            if isinstance(value, float):
                val_in = [idx for idx, val in enumerate(col_list) if math.isclose(value, val, abs_tol=1e-1)]
            elif isinstance(value, str):
                val_in = [idx for idx, val in enumerate(col_list) if regex.sub('', value.lower()) == regex.sub('', str(val).lower())]
            else:
                raise TypeError('Type unsupported in the data frame.')
        return val_in

    def clean_table(self, outfile_type):
        # Variables for logging data
        verified_entries = {'Type': [], 'Location': [], 'Country': [], 'Region': [], 'Latitude': [], 'Longitude': [],
                            'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [], 'Country_Code': []}
        pending_entries = {'Type': [], 'Location': [], 'Country': [], 'Region': [], 'Latitude': [], 'Longitude': [],
                           'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [], 'Country_Code': []}
        repeated_entries = {'Type': [], 'Location': [], 'Country': [], 'Region': [], 'Latitude': [], 'Longitude': [],
                            'ver_Index': [], 'Recorded_Lat': [], 'Recorded_Lng': [], 'Address': [], 'Country_Code': []}
        flagged_indices = []

        # Iterating through the rows to clean data
        for (index, row) in self.df.iterrows():
            print('Verifying row at index: ' + str(index))
            location = row[self.loc_col]
            country = row[self.ctry_col]
            region = row[self.reg_col]
            latitude = row[self.lat_col]
            longitude = row[self.lng_col]

            row_info = self.clean_data(location, country, region, latitude, longitude, verified_entries)
            print(row_info)
            # Row already exists in the verified dictionary
            if isinstance(row_info, list):
                for ver_idx in row_info:
                    entry = {}
                    for key in verified_entries.keys():
                        entry[key] = verified_entries[key][ver_idx]
                    entry['ver_Index'] = ver_idx
                    del entry['Type']
                    self.log_to_dict(repeated_entries, entry)
            # Completely new entry
            else:
                if row_info[0] < 0:
                    flagged_indices.append(index)
                    self.log_to_dict(pending_entries, row_info[1])
                else:
                    self.log_to_dict(verified_entries, row_info[1])

        # Exporting the data
        for key in repeated_entries.keys():
            print(key, ' ', len(repeated_entries[key]))
        self.export_file(pd.DataFrame(verified_entries), filenames.VERIFIED_ENTRIES_FILENAME, self.directory, outfile_type)
        self.export_file(pd.DataFrame(pending_entries), filenames.PENDING_ENTRIES_FILENAME, self.directory, outfile_type)

        self.export_file(pd.DataFrame(repeated_entries), filenames.REPEATED_ENTRIES_FILENAME, self.directory, outfile_type)

        return len(flagged_indices) / (1e-10 + len(self.df))

    def clean_data(self, location, country, region, latitude, longitude, verified_log):
        loc_in_table = self.cell_in_table(value=str(location), col_list=list(verified_log['Location']))
        ctry_in_table = self.cell_in_table(value=str(country), col_list=list(verified_log['Country']))
        in_table = list(set(loc_in_table) & set(ctry_in_table))
        if in_table:
            return in_table
        else:
            return self.validator.verify_info(location, country, region, latitude, longitude)

    def log_to_dict(self, log, row_dict):
        for key in row_dict.keys():
            log[key].append(row_dict[key])

    def verify_row(self, index, outfile_type):
        loc = self.df.iloc[index, self.loc_col]
        ctry = self.df.iloc[index, self.ctry_col]
        reg = self.df.iloc[index, self.reg_col]
        lat = self.df.iloc[index, self.lat_col]
        lng = self.df.iloc[index, self.lng_col]

        in_table = self.query_table(loc=loc, ctry=ctry)
        if in_table:
            new_df = pd.DataFrame(columns=self.df.columns)
            for idx in in_table:
                new_df.loc[len(new_df)] = dict(self.df.iloc[idx])
        else:
            row_info = self.validator.verify_info(loc, ctry, reg, lat, lng)
            new_df = pd.DataFrame(row_info[1])

        self.export_file(new_df, filenames.VALIDATION_RESULT_FILENAME, self.directory, outfile_type)


tools = TableTools(file_path=str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                                                                  'resources', 'xlsx', 'tblLocation.xlsx'))))
tools.clean_table('.csv')
