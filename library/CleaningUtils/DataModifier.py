import os
import pandas as pd

class Modifier:
    """
    Class acts as a command line tool for accepting/rejecting proposed data modifications and
    stores the validated data and any data already marked as correct as a new file.
    """
    def __init__(self, incorrect_locs=None, correct_locs=None, geocoded_locs=None):
        self.to_check = None
        cwd = os.getcwd()
        try:
            print('Reading in incorrect locations.')
            if incorrect_locs:
                self.to_check = pd.read_csv(incorrect_locs)
            else:   # Point to file w/ suggested changes.
                self.to_check = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'logged_locations.csv'))))
            print('Reading in correct locations.')
            if correct_locs:
                self.corrects = pd.read_csv(correct_locs)
            else:
                self.corrects = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'correct_locations.csv'))))
            print('Reading in geocoded locations.')
            if geocoded_locs:
                self.to_check_geocoded = pd.read_csv(geocoded_locs)
            else:
                self.to_check_geocoded = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'geocoded_locations.csv'))))
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
        toss_desc = 'Use this command to toss the suggested values and keep the existing.'
        exit_command = 'EXIT'
        exit_desc = '''Use this command to close the program. Changes up to this point will be saved into an 
                updated, separate version of the correct values files.'''
        help_command = 'HELP'
        help_desc = 'Use this command to see the list of commands and their descriptions.'

        command_list = []
        desc_list = []
        command_list.append(save_command)
        command_list.append(toss_command)
        command_list.append(exit_command)
        command_list.append(help_command)
        desc_list.append(save_desc)
        desc_list.append(toss_desc)
        desc_list.append(exit_desc)
        desc_list.append(help_desc)
        return command_list, desc_list, help_command

    def run(self, lat_col = 'Latitude', lng_col='Longitude', rec_lat_col='Recorded_Lat',
            rec_lng_col='Recorded_Lng', cc_col='ISO3', country_col='Country', loc_col='Location',
            reg_col='Region'):
        """
        Iterate over cleaned data file and prompt user to confirm changes. Changes are then stored
        in a new file and the original data is left untouched.

        :params: Optional params to define column names
        """

        maker = self.make_commands()

        command_list = maker[0]
        desc_list = maker[1]

        columns = [lat_col, lng_col, country_col, loc_col, cc_col, rec_lat_col, rec_lng_col,
                   reg_col, 'Address']

        confirmed_data = pd.DataFrame(columns=columns)

        print('Running')
        print('Commands')
        print('===========')
        for i in range(len(command_list)):
            print(command_list[i] + ': ' + desc_list[i])
        self.run_loop(self.to_check, confirmed_data, maker, command_list, desc_list)
        self.run_loop(self.to_check_geocoded, confirmed_data, maker, command_list, desc_list)

        print('All rows checked. Saving.')
        self.save_file(confirmed_data)

    def run_loop(self, this_check, confirmed_data, maker, command_list, desc_list):
        """
        Loop over entries that require validation.
        """
        for (index, row) in this_check.iterrows():
            print(row['Location'] + ', ' + row['Country'])
            print('Input Lat: ' + str(row['Latitude']) + '  Input Lng: ' + str(row['Longitude']))
            print('Recorded Lat: ' + str(row['Recorded_Lat']) + '  Recorded Lng: ' + str(row['Recorded_Lng']))
            user_input = input('Input command. Type "HELP" for options: ')

            # If user chooses help or inputs valid input, loop until we get different.
            while user_input not in command_list or user_input == maker[2]:
                if user_input == maker[2]:
                    for i in range(len(command_list)):
                        print(command_list[i] + ': ' + desc_list[i])
                else:
                    print('Invalid command. Type "HELP" to see available commands.')

            # At this point, a valid command has been input
            if user_input == maker[0][0]:    # SAVE: Save the suggested value
                print('Saving')
                row['Latitude'] = row['Recorded_Lat']
                row['Longitude'] = row['Recorded_Lat']
                row['Type'] = 'correct location data'
                confirmed_data.append(row)
            elif user_input == maker[0][1]:     # TOSS: Don't use suggested value.
                print('Tossing')
                row['Type'] = 'correct location data'
                confirmed_data.append(row)
            elif user_input == maker[0][2]:    # EXIT: Stop editing and save new file now.
                print('Stopping')
                break

    def save_file(self, confirmed_data, file_path=None):
        """
        Save the passed dataframe as a new .csv file.

        :param confirmed_data: A pandas DataFrame representing all data validated as correct
        :param file_path: File path including file name with .csv extension. Dictates where output is placed.
        """
        self.corrects.append(confirmed_data)    # Append our validated data to the correct data
        if not file_path:   # If filepath for output is not passed, create one
            file_path = ''
            unique = False
            cwd = os.getcwd()
            i = 0
            while not unique:  # Ensure we write to a new file and don't overwrite an existing one.
                file_path = os.path.normpath(os.path.join(cwd, 'correctlocation_' + str(i) + '.csv'))
                if not os.path.exists(file_path):
                    unique = True
                    file_path = str(file_path)
                i += 1
        print('Creating file at ' + file_path)
        self.corrects.to_csv(path_or_buf=file_path, sep=',', index=False)

        print('Complete. Closing program.')
