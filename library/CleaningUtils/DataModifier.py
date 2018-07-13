import os
import geopandas as gpd
import pandas as pd

class Modifier:
    def __init__(self, incorrect_locs=None, correct_locs=None):
        self.to_check = None
        self.flipframes = []
        cwd = os.getcwd()
        try:
            for i in range(8):
                tfile = str(os.path.normpath(os.path.join(cwd, 'flip_' + str(i) + '.csv')))
                self.flipframes.append(pd.read_csv(tfile))
            print(self.flipframes)
            if incorrect_locs:
                self.to_check = pd.read_csv(incorrect_locs)
            else:   # Point to file w/ suggested changes.
                self.to_check = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'invalid_locations.csv'))))
            if correct_locs:
                self.corrects = pd.read_csv(correct_locs)
            else:
                self.to_check = pd.read_csv(str(os.path.normpath(os.path.join(cwd, 'logged_locations.csv'))))
        except OSError:
            print('Unable to find flipped coordinates files. Have you cleaned the data yet with a Geocode Validator?')

    def make_commands(self):
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
        return command_list, desc_list

    def run(self):
        """
        Iterate over cleaned data file and prompt user to confirm changes
        """
        maker = self.make_commands()

        command_list = maker[0]
        desc_list = maker[1]

        for i in range(len(command_list)):
            print(command_list[i] + ': ' + desc_list[i])

        # columns = list(self.to_check.columns.values)
        columns = ['Type', 'Latitude', 'Longitude', 'Country', 'Location', 'ISO3', 'Recorded_Lat', 'Recorded_Lng',
                   'Region', 'Index', 'Address']

        confirmed_data = pd.DataFrame(columns=columns)

        for (index, row) in self.to_check.iterrows():

            print(row['Location'] + ', ' + row['Country'])
            print('Input Lat: ' + row['Latitude'] + '  Input Lng: ' + row['Longitude'])
            print('Recorded Lat: ' + row['Recorded_Lat'] + '  Recorded Lng: ' + row['Recorded_Lng'])
            user_input = input('Input command. Type "HELP" for options: ')

            while user_input not in command_list or user_input == help_command:
                if user_input == help_command:
                    for i in range(len(command_list)):
                        print(command_list[i] + ': ' + desc_list[i])
                else:
                    print('Invalid command. Type "HELP" to see available commands.')

            if row['Type'] != 'correct location data':
                if user_input == 'SAVE':    # Save the suggested value
                    row['Latitude'] = row['Recorded_Lat']
                    row['Longitude'] = row['Recorded_Lat']
                    confirmed_data.append(row)
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
        self.corrects.to_csv(path_or_buf=path, sep=',', index=False)

modifier = Modifier()