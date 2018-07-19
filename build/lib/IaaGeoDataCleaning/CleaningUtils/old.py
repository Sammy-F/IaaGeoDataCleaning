import geopy as gp
import geopandas as gpd
from os import path
import pandas as pd
import numpy as np
from shapely.geometry import Point
import re
import string
import country_converter as coco


class GeoDataCorrector:
    """
    Handles cleaning of data whose lat/lng values due not match its input country.

    Cases tested for: Non-standard country name, flipped lat/lng values,
    no lat/lng entered

    See the documentation for usage examples.
    """
    def __init__(self, map_file=None, map=None):
        # Offer opportunity to input an already existing shapefile GeoDataFrame
        if not map:
            if not map_file:
                map_file = str(path.abspath(path.join(path.dirname(__file__), '..', '..', 'resources',
                                                      'mapinfo', 'TM_WORLD_BORDERS-0.3.shp')))
            self.map = gpd.read_file(map_file)
        else:
            self.map = map

        self.pht = gp.Photon(timeout=3)

        self.entry_type = {0: 'correct location data', 1: 'entered (lat, -lng)',
                           2: 'entered (-lat, lng)', 3: 'entered (-lat, -lng)',
                           4: 'entered (lng, lat)', 5: 'entered (lng, -lat)',
                           6: 'entered (-lng, lat', 7: 'entered (-lng, -lat)',
                           8: 'no lat/lng entered / incorrect lat/lng - geocoded location',
                           -1: 'incorrect location data/cannot find coordinates',
                           -2: 'no latitude and longitude entered',
                           -3: 'no location/country entered / wrong country format'}

        self.name_handler = NameHandler()

    def verify_info(self, location=None, country=None, region=None, input_lat=None, inp_lng=None):
        """
        Reads in data for a single location and verifies its information/checks for missing data.
        Returns a dictionary with the completed entry.

        :param location: string
        :param country: string
        :param input_lat: float
        :param inp_lng: float
        :return: the type of entry and the entry's information as a dictionary
        """
        if location and country:
            print("Beginning verification of " + str(location) + ", " + str(country))
        else:
            print("Beginning verification of unknown.")
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
        """
        Formats the passed parameters as a dictionary representation for
        further processing in other methods.

        :param location: string
        :param country: string
        :param region: string
        :param latitude: float
        :param longitude: float
        :return: The dictionary representation of the data.
        """
        if pd.notnull(location):
            location = string.capwords(location)
        if pd.notnull(country):
            country = string.capwords(country)
        return {'Location': location, 'Country': country, 'Region': region, 'Latitude': latitude, 'Longitude': longitude,
                'Recorded_Lat': None, 'Recorded_Lng': None, 'Address': None, 'ISO3': None}

    def check_input(self, entry):
        """
        Checks to see if all the necessary fields are entered.

        :param entry: A dictionary (or functionally similar) representation of a given row/entry
        :return: a tuple containing 2 values:
        the type of entry as an integer and the (altered) location dictionary.
        """
        if pd.isnull(entry['Location']) or pd.isnull(entry['Country']):
            return -3, entry

        # Looking up with coco
        try:
            entry['Country'] = self.name_handler.find_name(entry['Country'])
            entry['ISO3'] = self.name_handler.find_iso(entry['Country'], True)

        except LookupError:
            alt_ctry = self.name_handler.find_name(entry['Country'])
            if not alt_ctry:
                return -3, entry
            else:
                print('check 2 start')
                entry['Country'] = alt_ctry
                entry['ISO3'] = self.name_handler.find_iso(alt_ctry, True)
                print('check 2 end')

        # Checking if lat/lng were entered
        if (pd.isnull(entry['Latitude']) or pd.isnull(entry['Longitude'])) or (
                entry['Latitude'] == 0 and entry['Longitude'] == 0):
            return -2, entry

        return 0, entry

    def verify_coords(self, loc_dict, use_iso3=True):
        """
        Uses a dictionary to determine whether the entered coordinates fall within the borders of the country entered.

        :param loc_dict: A dictionary representation of a given row/entry
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """

        print("Check validity of coordinates")
        lat = loc_dict['Latitude']
        lng = loc_dict['Longitude']

        if use_iso3:
            if 'ISO3' in loc_dict:
                iso = loc_dict['ISO3']
            else:
                iso_find = self.name_handler.find_iso(loc_dict['Country'], use_iso3)
                iso = iso_find
        else:
            if 'ISO2' in loc_dict:
                iso = loc_dict['ISO2']
            else:
                iso_find = self.name_handler.find_iso(loc_dict['Country'], use_iso3)
                iso = iso_find

        loc_dict['Address'] = loc_dict['Location'] + ', ' + loc_dict['Country']

        possible_coords = [(lat, lng), (lat, -lng), (-lat, lng), (-lat, -lng),
                          (lng, lat), (lng, -lat), (-lng, lat), (-lng, -lat)]

        for i in range(len(possible_coords)):
            try:
                shape_point = np.array([possible_coords[i][1], possible_coords[i][0]])
                point = Point(shape_point)
                filter = self.map['geometry'].contains(point)

                if use_iso3:
                    mLoc = self.map.loc[filter, 'ISO3']
                else:
                    mLoc = self.map.loc[filter, 'ISO2']
                found_country = mLoc.iloc[0]
                if iso == found_country:
                    loc_dict['Recorded_Lat'] = possible_coords[i][0]
                    loc_dict['Recorded_Lng'] = possible_coords[i][1]
                    if i != 0:
                        print('Found flipped lat/lng. Flipping and marking.')
                    else:
                        print('Correct coordinates. Returning.')
                    return i, loc_dict

            except IndexError:
                continue

        print('Unable to validate coordinates. Marking as incorrect.')
        return -1, loc_dict

    def geocode_coords(self, loc_dict):
        """
        Finds the coordinates of a location based on the entered location and country. Directly
        modifies the passed dictionary.

        :param loc_dict: A dictionary representation of a given row/entry
        :return: a tuple containing 2 values:
        the type of entry and the (altered) location dictionary.
        """
        location = loc_dict['Location']
        country = loc_dict['Country']

        print("Attempting to geocode coordinates for " + str(location) + ", " + country)

        try:
            matches = self.pht.geocode(location + " " + country, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matched_country = match.address.split(',')[-1]
                    if re.search(country, matched_country, re.IGNORECASE):
                        loc_dict['Recorded_Lat'] = match.latitude
                        loc_dict['Recorded_Lng'] = match.longitude
                        loc_dict['Address'] = match.address
                        print('Successfully geocoded.')
                        return 8, loc_dict

            matches = self.pht.geocode(location, exactly_one=False)
            if matches is not None:
                for match in matches:
                    matched_country = match.address.split()[-1]
                    if re.search(country, matched_country, re.IGNORECASE):
                        loc_dict['Recorded_Lat'] = match.latitude
                        loc_dict['Recorded_Lng'] = match.longitude
                        loc_dict['Address'] = match.address
                        print('Successfully geocoded.')
                        return 8, loc_dict

            print("Unable to find coordinates for location.")
            return -1, loc_dict

        except Exception as e:
            print("An error occurred. Unable to geocode coordinates. Error message:")
            print(str(e))
            return -1, loc_dict

class NameHandler:
    """
    Handles standardization of country names
    """
    def __init__(self):
        self.convertor = coco.CountryConverter()

    def find_name(self, check_country):
        """
        Standardizes a country's name.

        :param check_country: The input country name
        :return: The standardized country name
        """
        return self.convertor.convert(names=[check_country], to='name_short')

    def find_iso(self, check_country, use_iso3=True):
        """
        Returns the ISO2 or ISO3 country code for the country

        :param check_country: The input country name
        :param use_iso3: Determines whether to return ISO2 or ISO3
        :return: ISO2 or ISO3 country code as string
        """
        if use_iso3:
            return self.convertor.convert(names=[check_country], to='ISO3').upper()
        else:
            return self.convertor.convert(names=[check_country], to='ISO2').upper()
