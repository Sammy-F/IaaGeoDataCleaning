import pandas as pd
import datetime
import re
import reverse_geocode as rg
import string

"""
GeocodeValidator allows the user to perform reverse geocoding
on a .xlsx or .csv to ensure that input locations correspond to
the correct latitude and longitude. If not, then basic data cleaning
is performed to check for human error.

Created by Jonathan Scott

Modified by: Samantha Fritsche, Thy Nguyen 6/5/2018
"""

# TODO: handle exceptions when making API calls

parenNumRegex = re.compile('\(\d\)')
now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d ")


class GeocodeValidator:
    def __init__(self, fileName):
        self.fileName = fileName

        self.flaggedLocations = []  # flagged indexes in data frame
        self.log = {'index': [], 'location': [], 'type': []}

        if fileName.endswith('xlsx'):
            self.tobeValidatedLocation = pd.read_excel(fileName)
        else:
            self.tobeValidatedLocation = pd.read_csv(fileName)

    def run(self):
        """
        Iterates through every row of the data and validates the locational information of each entry
        :return:
        """
        for (index, row) in self.tobeValidatedLocation.iterrows():
            try:
                row['Location'] = parenNumRegex.sub("", row['Location'])
                country = string.capwords(str(row["Country"]).lower())
                location = string.capwords(str(row["Location"]).lower())

                inputCoordinates = (row.loc["Latitude"], row.loc["Longitude"])
                nearestCountry = rg.get(inputCoordinates)['country']

                if nearestCountry != country:
                    print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
                    self.flaggedLocations.append(index)
                    self.log['location'].append((location, country))
                    self.log['index'].append(index)
                    self.log['type'].append('mismatched country')


            except TypeError:
                print("Index: " + str(index) + " country does not match entered coordinates.(Index flagged.) \n")
                self.flaggedLocations.append(index)
                self.log['location'].append((location, country))
                self.log['index'].append(index)
                self.log['type'].append('mismatched country')

        self.logResults()

    def logResults(self):
        print("Flagged locations are at indicies: " + str(self.flaggedLocations))
        loggedDF = pd.DataFrame(data=self.log)
        loggedDF.to_csv('validation_log_' + str(now) + '.csv', sep=',', encoding='utf-8')
        return len(self.flaggedLocations) / (1e-10 + self.tobeValidatedLocation.shape[0])


validator1 = GeocodeValidator("NaNtblLocations.xlsx")
validator1.run()

