"""
NameHandler takes an input country name that's not formatted in a manner we can process
and looks for its formatted version.

Inefficient!

Created by: Samantha Fritsche 6/7/18
"""

class NameHandler:
    def __init__(self):

        self.namesDict = {}
        self.namesDict['United States of America'] = ['United States', 'US', 'USA', 'America']
        self.namesDict['Congo'] = ['Republic of Congo']
        self.namesDict['Congo, The Democratic Republic of the'] = ['Zaire', 'DR Congo', 'DRC', 'East Congo', 'Congo-Kinshasa']
        self.namesDict['Spain'] = ['España']
        self.namesDict['Côte d’Ivoire'] = ["Cote d’Ivoire", "Cote D'ivoire", "Cote D'Ivoire"]
        self.namesDict['Republic of South Africa'] = ['South Africa Rep.']
        self.namesDict['Trinidad and Tobago'] = ['Trinidad Y Tobago']

        print("handler created")

    def findName(self, checkCountry):
        print(checkCountry)
        for formattedName, alternativeNames in self.namesDict.items():
            for alternativeName in alternativeNames:
                print(formattedName)
                print(alternativeName)
                if (checkCountry == alternativeName):
                    return formattedName
        return False

