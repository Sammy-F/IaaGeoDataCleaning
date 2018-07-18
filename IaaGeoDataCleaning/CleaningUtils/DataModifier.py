import os
import pandas as pd

"""
Created by Sammy Fritsche, Thy Nguyen 7/12/18.
Modified by Sammy Fritsche 7/16/18.

Facilitates modification of data after cleaning. Can be run as main or imported to instantiate
a Modifier class.
"""

class Modifier:
    """
    Class acts as a command line tool for accepting/rejecting proposed data modifications and
    stores the validated data and any data already marked as correct as a new file.

    :param incorrect_locs: String filepath to flipped locations.
    :param correct_locs: String filepath to locations that have been verified.
    :param geocoded_locs: String filepath to geocoded locations
    """
    def __init__(self, incorrect_locs, correct_locs, geocoded_locs):
        self.to_check = None
        cwd = os.getcwd()
        self.modded_path = cwd
        try:
            print('Reading in data files.')
            self.corrects = pd.read_csv(correct_locs)
            self.to_check = pd.read_csv(incorrect_locs)
            self.to_check_geocoded = pd.read_csv(geocoded_locs)
        except OSError:
            print('Unable to find flipped coordinates files. Have you cleaned the data yet with a Geocode Validator?')

    def make_commands(self):
        """
        Create lists of commands and their descriptions

        :return: Tuple containing commands, descriptions, and the help command
        """
        save_command = 'SAVE'
        save_desc = 'Use this command to save the suggested values to the data set.'
        toss_command = 'TOSS'
        toss_desc = 'Use this command to toss the suggested values and keep the existing, but does not mark as correct.'
        exit_command = 'EXIT'
        exit_desc = '''Use this command to close the program. Changes up to this point will be saved into an 
                updated, separate version of the correct values files.'''
        help_command = 'HELP'
        help_desc = 'Use this command to see the list of commands and their descriptions.'
        keep_command = 'KEEP'
        keep_desc = 'Use this command to toss the suggested values and mark the existing as correct.'

        command_list = []
        desc_list = []
        command_list.append(save_command)
        command_list.append(toss_command)
        command_list.append(exit_command)
        command_list.append(help_command)
        command_list.append(keep_command)
        desc_list.append(save_desc)
        desc_list.append(toss_desc)
        desc_list.append(exit_desc)
        desc_list.append(help_desc)
        desc_list.append(keep_desc)
        return command_list, desc_list, help_command

    def run(self, output_directory, lat_col='Latitude', lng_col='Longitude', rec_lat_col='Flipped_Lat',
            rec_lng_col='Flipped_Lng', country_col='Country', loc_col='Location',
            geoc_rec_lng_col='Geocoded_Lat', geoc_rec_lat_col='Geocoded_Lng'):
        """
        Iterate over cleaned data file and prompt user to confirm changes. Changes are then stored
        in a new file and the original data is left untouched.

        :params: Optional params to define column names
        """

        maker = self.make_commands()

        command_list = maker[0]
        desc_list = maker[1]

        # columns = [lat_col, lng_col, country_col, loc_col, cc_col, rec_lat_col, rec_lng_col,
        #            reg_col, 'Address']
        #
        # geoc_columns = [lat_col, lng_col, country_col, loc_col, cc_col, geoc_rec_lat_col, geoc_rec_lng_col,
        #            reg_col, 'Address']

        columns = list(self.to_check_geocoded.columns.values)
        geoc_columns = list(self.to_check.columns.values)

        print(columns)
        print(geoc_columns)
        # confirmed_data = pd.DataFrame(columns=columns)

        print('Running')
        print('Commands')
        print('===========')
        for i in range(len(command_list)):
            print(command_list[i] + ': ' + desc_list[i])
        flipped_data = self.__run_loop(self.to_check, maker, command_list, desc_list,
                                                               lat_col, lng_col, rec_lat_col, rec_lng_col, country_col,
                                                               loc_col)

        geocoded_data = self.__run_loop(self.to_check_geocoded, maker, command_list,
                                                               desc_list, lat_col, lng_col, geoc_rec_lat_col,
                                                               geoc_rec_lng_col, country_col, loc_col)
        if not output_directory:
            flipped_data[1].to_csv(path_or_buf=str(os.path.normpath(os.path.join(self.modded_path, 'flipped_updated.csv'))),
                                   sep=',', index=False)
            geocoded_data[1].to_csv(path_or_buf=str(os.path.normpath(os.path.join(self.modded_path, 'geocoded_updated.csv'))),
                                   sep=',', index=False)
        else:
            flipped_data[1].to_csv(str(os.path.join(output_directory, 'flipped_updated.csv')), sep=',', index=False)
            geocoded_data[1].to_csv(path_or_buf=str(os.path.join(output_directory, 'geocoded_updated.csv')), sep=',', index=False)
        flipped_data = pd.DataFrame(flipped_data[0], columns=columns)
        geocoded_data = pd.DataFrame(geocoded_data[0], columns=geoc_columns)
        confirmed_data = flipped_data.append(geocoded_data, sort=True)

        print('All rows checked. Saving.')
        self.__save_file(confirmed_data, output_directory)

    def __run_loop(self, this_check, maker, command_list, desc_list, lat_col, lng_col, rec_lat_col, rec_lng_col,
                   country_col, loc_col):
        """
        Private method to construct and run the loop over entries that require validation.

        :params: Uses column names defined in run()

        :return: The pandas DataFrame of confirmed locations up to this point as well as the modified
        DataFrame for the incorrects/geocoded entries.
        """
        temp_confirmed = []
        for (index, row) in this_check.iterrows():
            if row['Type'] == 'Flipped' or row['Type'] == 'Geocoded':    # Only run if data has been modified.
                print(row[loc_col] + ', ' + row[country_col])
                print('Input Lat: ' + str(row[lat_col]) + '  Input Lng: ' + str(row[lng_col]))
                print('Recorded Lat: ' + str(row[rec_lat_col]) + '  Recorded Lng: ' + str(row[rec_lng_col]))
                user_input = input('Input command: ')

                # If user chooses help or inputs valid input, loop until we get different.
                while user_input not in command_list or user_input == maker[2]:
                    if user_input == maker[2]:
                        for i in range(len(command_list)):
                            print(command_list[i] + ': ' + desc_list[i])
                    else:
                        print('Invalid command. Type "HELP" to see available commands.')
                    user_input = input("Input command: ")

                # At this point, a valid command has been input
                if user_input == maker[0][0]:    # SAVE: Save the suggested value
                    print('Saving')
                    row[lat_col] = row[rec_lat_col]
                    row[lng_col] = row[rec_lng_col]
                    row['Type'] = 'Verified'
                    temp_confirmed.append(row)
                    this_check.drop(index, inplace=True)
                elif user_input == maker[0][1]:     # TOSS: Don't use suggested value, but don't mark as correct. Keep it in the incorrects.
                    print('Tossing')
                    temp_confirmed.append(row)
                elif user_input == maker[0][3]:     # KEEP: Don't use the suggested value, mark it as correct. Remove from incorrects.
                    print('Keeping')
                    row['Type'] = 'Verified'
                    temp_confirmed.append(row)
                    this_check.drop(index, inplace=True)
                elif user_input == maker[0][2]:    # EXIT: Stop editing and save new file now.
                    print('Stopping')
                    break

        # temp_confirmed = pd.DataFrame(data=temp_confirmed, columns=cols)

        return temp_confirmed, this_check

    def __save_file(self, confirmed_data, file_path):
        """
        Save the passed dataframe as a new .csv file.

        :param confirmed_data: A pandas DataFrame representing all data validated as correct
        :param file_path: File path including file name with .csv extension. Dictates where output is placed.
        """
        self.corrects = self.corrects.append(confirmed_data, sort=True)    # Append our validated data to the data
        print(file_path)
        unique = False
        i = 0
        test_file_path=''
        while not unique:  # Ensure we write to a new file and don't overwrite an existing one.
            test_file_path = os.path.join(file_path, 'correctlocation_' + str(i) + '.csv')
            if not os.path.exists(file_path):
                unique = True
                test_file_path = str(test_file_path)
            i += 1
        print('Creating file at ' + test_file_path)
        self.corrects.to_csv(path_or_buf=test_file_path, sep=',', index=False)

        print('Complete. Closing program.')


if __name__ == "__main__":

    print('Define data filepaths')

    correct = input('Path to existing correct data: ')
    incorrect = input('Path to flipped data: ')
    geocoded = input('Path to geocoded data: ')

    mod = Modifier(incorrect_locs=incorrect, geocoded_locs=geocoded, correct_locs=correct)

    user_input = input('Define custom column names? (y/n) ')
    if user_input == 'y':
        lat_col = input('Latitude column: ')
        lng_col = input('Longitude column: ')
        rec_lat_col = input('Recommended latitude column: ')
        rec_lng_col = input('Recommended longitude column: ')
        cc_col = input('Country code column: ')
        country_col = input('Country name column: ')
        loc_col = input('Location column name: ')
        reg_col = input('Region column name: ')
        geoc_rec_lng_col = input('Geocoded longitudes column: ')
        geoc_rec_lat_col = input('Geocoded latitudes column: ')
        mod.run(lat_col=lat_col, lng_col=lng_col, rec_lat_col=rec_lat_col, rec_lng_col=rec_lng_col,
                country_col=country_col, loc_col=loc_col, geoc_rec_lng_col=geoc_rec_lng_col,
                geoc_rec_lat_col=geoc_rec_lat_col)
    else:
        mod.run('D:\PyCharm Projects\IaaGeoDataCleaning')
