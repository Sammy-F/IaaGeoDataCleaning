import os
import geopandas as gpd
import pandas as pd

# TODO: All of this is speculatory code atm. We need valid formatted data files to test for functionality.
class Modifier:
    """
    Class acts as a command line tool for accepting/rejecting proposed data modifications.
    """
    def __init__(self, incorrect_locs=None, correct_locs=None, geocoded_locs=None):
        self.to_check = None
        cwd = os.getcwd()
        try:
            if incorrect_locs:
                self.to_check = pd.read_csv(incorrect_locs)
            else:   # Point to file w/ suggested changes.
                self.to_check = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'incorrect_locations.csv'))))
            if correct_locs:
                self.corrects = pd.read_csv(correct_locs)
            else:
                self.to_check = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'correct_locations.csv'))))
            if geocoded_locs:
                self.to_check.append(pd.read_csv(geocoded_locs))    # TODO: Find more efficient way
            else:
                self.to_check.append(pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'geocoded_locations.csv')))))
        except OSError:
            print('Unable to find flipped coordinates files. Have you cleaned the data yet with a Geocode Validator?')

    def make_commands(self):
        """
        Create lists of commands and their descriptions
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

    def run(self, lat_col = 'Latitude', lng_col='Longitude', rec_lat_col = 'Recorded_Lat',
            rec_lng_col='Recorded_Lng', cc_col = 'ISO3', country_col='Country', loc_col='Location',
            reg_col='Region'):
        """
        Iterate over cleaned data file and prompt user to confirm changes
        """
        maker = self.make_commands()

        command_list = maker[0]
        desc_list = maker[1]

        for i in range(len(command_list)):
            print(command_list[i] + ': ' + desc_list[i])

        # columns = list(self.to_check.columns.values)
        columns = [lat_col, lng_col, country_col, loc_col, cc_col, rec_lat_col, rec_lng_col,
                   reg_col, 'Address']

        confirmed_data = pd.DataFrame(columns=columns)

        for (index, row) in self.to_check.iterrows():

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

            if row['Type'] != 'correct location data':
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

            else:   # Added in case a correct item slips in somehow.
                confirmed_data.append(row)

        print('All rows checked. Saving.')

        self.corrects.append(confirmed_data)
        path = ''
        unique = False
        cwd = os.getcwd()
        i = 0
        while not unique:   # Ensure we write to a new file and don't overwrite an existing one.
            path = os.path.normpath(os.path.join(cwd, 'correctlocation_' + str(i) + '.csv'))
            if not os.path.exists(path):
                unique = True
                path = str(path)
            i += 1
        print('Creating file at ' + path)
        self.corrects.to_csv(path_or_buf=path, sep=',', index=False)

modifier = Modifier()