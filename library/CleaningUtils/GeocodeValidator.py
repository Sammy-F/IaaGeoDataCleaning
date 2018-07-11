import geopy as gp
import geopandas as gpd
from os import path
import pandas as pd
import pycountry as pc
import numpy as np
from shapely.geometry import Point
import re
import string


class GeocodeValidator:
    def __init__(self, map_file=None):
        if not map_file:
            map_file = str(path.abspath(path.join(path.dirname(__file__), '..', '..', 'resources',
                                                  'mapinfo', 'TM_WORLD_BORDERS-0.3.shp')))
        self.pht = gp.Photon(timeout=3)

        self.entry_type = {0: 'correct location data', 1: 'entered (lat, -lng)',
                           2: 'entered (-lat, lng)', 3: 'entered (-lat, -lng)',
                           4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
                           6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)',
                           8: 'no lat/lng entered / incorrect lat/lng - geocoded location',
                           -1: 'incorrect location data/cannot find coordinates',
                           -2: 'no latitude and longitude entered',
                           -3: 'no location/country entered / wrong country format'}

        self.map = gpd.read_file(map_file)

    def verify_info(self, location=None, country=None, region=None, input_lat=None, inp_lng=None):
        """
        Reads in data for a single location and verifies its information/checks for missing data.

        :param location:
        :param country:
        :param input_lat:
        :param inp_lng:
        :return: the type of entry and the entry's information as a dictionary
        """
        loc_info = self.format_info(location, country, region, input_lat, inp_lng)
        loc_checked = self.check_input(loc_info)
        # tuple (inp_type, dict)
        inp_typ = loc_checked[0]
        loc_info = loc_checked[1]

        # Location or country is not entered
        if inp_typ == -3:
            loc_info['Type'] = self.entry_type[inp_typ]
            return inp_typ, loc_info

        # Everything is entered
        elif inp_typ == 0:
            # Validate entered coordinates
            coords_checked = self.verify_coords(loc_info)

            coords_type = coords_checked[0]
            loc_info = coords_checked[1]

            # Attempt to find actual coordinates if the ones entered are not correct
            if coords_type == -1:
                coords_alt = self.geocode_coords(loc_info)
                coords_type = coords_alt[0]
                loc_info = coords_alt[1]

        # Attempt to find coordinates if not entered
        else:
            coords_alt = self.geocode_coords(loc_info)
            coords_type = coords_alt[0]
            loc_info = coords_alt[1]

        loc_info['Type'] = self.entry_type[coords_type]
        return coords_type, loc_info

    def format_info(self, location, country, region, latitude, longitude):
        if pd.notnull(location):
            location = string.capwords(location)
        if pd.notnull(country):
            country = string.capwords(country)
        return {'Location': location, 'Country': country, 'Region': region, 'Latitude': latitude, 'Longitude': longitude,
                'Recorded_Lat': None, 'Recorded_Lng': None, 'Address': None, 'Country_Code': None}

    def check_input(self, loc_dict):
        """
        Checks to see if all the necessary fields are entered.

        :param loc_dict:
        :return: a tuple containing 2 values:
        the type of entry as an integer and the (altered) location dictionary.
        """
        if pd.isnull(loc_dict['Location']) or pd.isnull(loc_dict['Country']):
            return -3, loc_dict

        # Looking up with pycountry
        try:
            loc_dict['Country_Code'] = pc.countries.lookup(loc_dict['Country']).alpha_3
            loc_dict['Country'] = pc.countries.lookup(loc_dict['Country']).name

        except LookupError:
            alt_ctry = self.find_alt_name(loc_dict['Country'])
            if not alt_ctry:
                return -3, loc_dict
            else:
                loc_dict['Country'] = alt_ctry
                loc_dict['Country_Code'] = pc.countries.lookup(alt_ctry).alpha_3

        # Checking if lat/lng were entered
        if (pd.isnull(loc_dict['Latitude']) or pd.isnull(loc_dict['Longitude'])) or (
                loc_dict['Latitude'] == 0 and loc_dict['Longitude'] == 0):
            return -2, loc_dict

        return 0, loc_dict

    def verify_coords(self, loc_dict):
        """
        Uses a shapefile to determine whether the entered coordinates fall within the borders of the country entered.

        :param loc_dict:
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """
        lat = loc_dict['Latitude']
        lng = loc_dict['Longitude']

        loc_dict['Address'] = loc_dict['Location'] + ', ' + loc_dict['Country']

        possible_coords = [(lat, lng), (lat, -lng), (-lat, lng), (-lat, -lng),
                          (lng, lat), (lng, -lat), (-lng, lat), (-lng, -lat)]

        for i in range(len(possible_coords)):
            try:
                shape_point = np.array([possible_coords[i][1], possible_coords[i][0]])
                point = Point(shape_point)
                filter = self.map['geometry'].contains(point)
                mLoc = self.map.loc[filter, 'ISO3']
                found_country = mLoc.iloc[0]

                if loc_dict['Country_Code'] == found_country:
                    loc_dict['Recorded_Lat'] = possible_coords[i][0]
                    loc_dict['Recorded_Lng'] = possible_coords[i][1]
                    return i, loc_dict

            except IndexError:
                continue

        return -1, loc_dict

    def geocode_coords(self, loc_dict):
        """
        Finds the coordinates of a location based on the entered location and country.

        :param loc_dict:
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """
        location = loc_dict['Location']
        country = loc_dict['Country']

        try:
            matches = self.pht.geocode(location + " " + country, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matched_country = match.address.split(',')[-1]
                    if re.search(country, matched_country, re.IGNORECASE):
                        loc_dict['Recorded_Lat'] = match.latitude
                        loc_dict['Recorded_Lng'] = match.longitude
                        loc_dict['Address'] = match.address
                        return 8, loc_dict

            matches = self.pht.geocode(location, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matched_country = match.address.split()[-1]
                    if re.search(country, matched_country, re.IGNORECASE):
                        loc_dict['Recorded_Lat'] = match.latitude
                        loc_dict['Recorded_Lng'] = match.longitude
                        loc_dict['Address'] = match.address
                        return 8, loc_dict

            return -1, loc_dict

        except:
            return -1, loc_dict

    def find_alt_name(self, country_name):
        """
        If a country name is invalid, assume it is an alternative name
        and attempt to find and return the official one.

        :param country_name:
        """
        finder = NameHandler()
        return finder.find_name(country_name)


class NameHandler:
    def __init__(self):
        self.names_dict = dict()
        self.names_dict['United States of America'] = ['United States', 'US', 'USA', 'America']
        self.names_dict['Congo'] = ['Republic of Congo']
        self.names_dict['Congo, The Democratic Republic of the'] = ['Zaire', 'DR Congo', 'DRC', 'East Congo',
                                                                   'Congo-Kinshasa', 'Democratic Republic Of Congo',
                                                                   'Democratic Republic of Congo']
        self.names_dict['Spain'] = ['España']
        self.names_dict["Côte d'Ivoire"] = ["Cote d’Ivoire", "Cote D'ivoire", "Cote D'Ivoire"]
        self.names_dict['South Africa'] = ['South Africa Rep.', 'Republic of South Africa']
        self.names_dict['Trinidad and Tobago'] = ['Trinidad Y Tobago']

    def find_name(self, check_country):
        for formattedName, alternativeNames in self.names_dict.items():
            for alternativeName in alternativeNames:
                if check_country.lower() == alternativeName.lower():
                    return formattedName
        return False
