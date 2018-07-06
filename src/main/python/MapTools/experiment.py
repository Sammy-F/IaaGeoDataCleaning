from folium import Map, Marker, Icon, Popup
from folium.plugins import MarkerCluster
from os import path
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import math
# TODO: plot all stations whose coordinates do not match the country.


class MapTool:
    def __init__(self):
        """
        Initializes a tool for mapping data points as markers using the folium package.
        """
        mapFile = str(path.abspath(path.join(path.dirname(__file__), '..', '..', '..', '..',
                                             'resources', 'mapinfo', 'TM_WORLD_BORDERS-0.3.shp')))
        self.map = gpd.read_file(mapFile)

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

    def check_columns(self, df, cols):
        """
        Checks to see whether the columns exist in the dataframe.
        :param df: pandas dataframe.
        :param cols: a tuple, list, or set of column names.
        :return:
        """
        if not isinstance(cols, set):
            cols = set(cols)
        if cols.issubset(df.columns):
            return True
        else:
            raise KeyError('Column names not found in data frame.')

    def clean_dataframe(self, infile, cols):
        """
        Confirms that a file can be used as a dataframe.
        :param infile: filepath to the data.
        :param cols: a tuple, list, or set of column names.
        :return: a pandas dataframe of the file.
        """
        df = self.read_file(infile)
        if self.check_columns(df, cols):
            return df

    def create_map(self, center=(0, 0), zoom=2):
        return Map(location=center, zoom_start=zoom)

    def format_popup(self, loc, ctry):
        if not loc:
            loc = ''
        if not ctry:
            ctry = ''
        return loc, ctry

    def haversine(self, lat0, lng0, lat1, lng1):
        """
        Calculates the distance between two coordinates using the haversine formula.
        :param lat0:
        :param lng0:
        :param lat1:
        :param lng1:
        :return: the distance in km.
        """
        rlat0 = math.radians(lat0)
        rlat1 = math.radians(lat1)
        dlat = rlat1 - rlat0
        dlng = math.radians(lng1 - lng0)

        a = math.pow(math.sin(dlat/2), 2) + math.cos(rlat0) * math.cos(rlat1) * math.pow(math.sin(dlng/2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 6371 * c

    def plot_point(self, lat, lng, desc=None, clr='blue'):
        """
        Creates a single marker.
        :param lat:
        :param lng:
        :param desc:
        :param clr:
        :return:
        """
        if desc:
            marker = Marker((lat, lng), popup=Popup(desc, parse_html=True),
                            icon=Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        else:
            marker = Marker((lat, lng), icon=Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        return marker

    def plot_all_stations(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=True):
        """
        Plots all data points in the file.
        :param infile: filepath to the data.
        :param loc_col: name of the location column.
        :param ctry_col: name of the country column.
        :param lat_col: name of the latitude column.
        :param lng_col: name of the longitude column.
        :param clr: color of the markers.
        :param as_cluster: boolean value - create the markers as a cluster or not.
        :return: a list of markers if as_cluster is False and a MarkerCluster otherwise.
        """
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})

        if as_cluster:
            markers = MarkerCluster()
        else:
            markers = []

        for (index, row) in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                lat = row[lat_col]
                lng = row[lng_col]
                location = self.format_popup(row[loc_col], row[ctry_col])

                marker = self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (location[0], location[1]), clr=clr)
                if as_cluster:
                    marker.add_to(markers)
                else:
                    markers.append(marker)

        return markers

    def plot_no_country(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='lightred', as_cluster=False):
        """
        Plots all data points whose coordinates do not fall within any country.
        :param infile:
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param clr:
        :param as_cluster: boolean value - create the markers as a cluster or not.
        :return: a list of markers if as_cluster is False and a MarkerCluster otherwise.
        """
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})

        if as_cluster:
            markers = MarkerCluster()
        else:
            markers = []

        for (index, row) in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                lat = row[lat_col]
                lng = row[lng_col]
                location = self.format_popup(row[loc_col], row[ctry_col])

                point = Point(np.array([lng, lat]))
                filtered = self.map['geometry'].contains(point)
                mLoc = list(self.map.loc[filtered, 'ISO3'])

                if len(mLoc) == 0:
                    marker = self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (location[0], location[1]), clr=clr)
                    if as_cluster:
                        marker.add_to(markers)
                    else:
                        markers.append(marker)

        return markers

    def plot_wrong_country(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='lightred'):
        """
        Plots all data points whose country does not match the country indicated by the coordinates and shapefile.
        Note: Given the differences in spelling, correct data points might still be plotted.
        :param infile:
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param clr:
        :return: the data points as Marker objects.
        """
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})
        markers = []

        for (index, row) in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                lat = row[lat_col]
                lng = row[lng_col]
                location = self.format_popup(row[loc_col], row[ctry_col])

                point = Point(np.array([lng, lat]))
                filtered = self.map['geometry'].contains(point)
                mLoc = list(self.map.loc[filtered, 'NAME'])

                if len(mLoc) > 0 and mLoc[0].lower() != location[1].lower():
                    markers.append(self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (location[0], location[1]), clr=clr))

        return markers

    def plot_potential_errors(self, infile, loc_col, ctry_col, lat_col, lng_col, clr0='lightred', clr1='orange'):
        """
        Plots all of the potentially incorrect location data points.
        :param infile:
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param clr0: color of the markers for entries that do not fall within any country border.
        :param clr1: color of the markers for entries whose country does not match
                     the country indicated by the shapefile and coordinates.
        :return: a list of Marker objects.
        """
        return self.plot_no_country(infile, loc_col, ctry_col, lat_col, lng_col, clr=clr0, as_cluster=False) + \
               self.plot_wrong_country(infile, loc_col, ctry_col, lat_col, lng_col, clr=clr1)

    def plot_condition(self, infile, condition, cnd_col, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=False):
        """
        Plots all of the data points that meet the specified condition.
        :param infile:
        :param condition: condition of the entries (currently works best with strings).
        :param cnd_col: name of the column to be evaluated.
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param clr: color of the markers.
        :param as_cluster: boolean value - create the markers as a cluster or not.
        :return: a list of markers if as_cluster is False and a MarkerCluster otherwise.
        """
        df = self.clean_dataframe(infile, {cnd_col, loc_col, ctry_col, lat_col, lng_col})

        if as_cluster:
            markers = MarkerCluster()
        else:
            markers = []

        for (index, row) in df.iterrows():
            if str(row[cnd_col]).lower() == str(condition).lower():
                if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                    lat = row[lat_col]
                    lng = row[lng_col]
                    location = self.format_popup(row[loc_col], row[ctry_col])

                    marker = self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (location[0], location[1]), clr=clr)
                    if as_cluster:
                        marker.add_to(markers)
                    else:
                        markers.append(marker)

        return markers

    def plot_pair_in_df(self, infile, index, lat0_col, lng0_col, lat1_col, lng1_col, clr0='lightblue', clr1='darkblue'):
        """
        Plots a data point if it contains two different coordinates for comparison.
        :param infile:
        :param index:
        :param lat0_col:
        :param lng0_col:
        :param lat1_col:
        :param lng1_col:
        :param clr0:
        :param clr1:
        :return: the data points as Marker objects.
        """
        df = self.clean_dataframe(infile, {lat0_col, lng0_col, lat1_col, lng1_col})

        if index < len(df):
            coords0 = (df.loc[index, lat0_col], df.loc[index, lng0_col])
            coords1 = (df.loc[index, lat1_col], df.loc[index, lng1_col])

            return self.plot_pair(coords0, coords1, clr0, clr1)
        else:
            raise KeyError('Index out of range.')

    def plot_pair(self, coords0, coords1, clr0='lightblue', clr1='darkblue'):
        """
        Plots two coordinates for comparison.
        :param coords0:
        :param coords1:
        :param clr0:
        :param clr1:
        :return: two Marker objects.
        """
        marker0 = self.plot_point(lat=coords0[0], lng=coords0[1], desc=str(coords0), clr=clr0)
        marker1 = self.plot_point(lat=coords1[0], lng=coords1[1], desc=str(coords1), clr=clr1)

        return marker0, marker1

    def plot_within_range(self, infile, center, radius, loc_col, ctry_col, lat_col, lng_col, desc0=None, clr0='blue', clr1='lightblue'):
        """
        Plots all data points within the range of the given center and radius.
        :param infile:
        :param center:
        :param radius: in km.
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param desc0:
        :param clr0:
        :param clr1:
        :return: all of the data points as Marker objects.
        """
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})
        if not desc0:
            desc0 = str(tuple(center))
        markers = []
        for (index, row) in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                lat = row[lat_col]
                lng = row[lng_col]
                d = self.haversine(center[0], center[1], lat, lng)

                if d < radius:
                    location = self.format_popup(row[loc_col], row[ctry_col])
                    markers.append(self.plot_point(lat=lat, lng=lng, clr=clr1,
                                                   desc='%s, %s, %s km' % (location[0], location[1], format(d, '.3f'))))

        markers.append(self.plot_point(lat=center[0], lng=center[1], desc=desc0, clr=clr0))
        return markers

    def plot_within_station(self, infile, index, radius, loc_col, ctry_col, lat_col, lng_col, clr0='blue', clr1='lightblue'):
        """
        Plots all of the data points within the radius of the specified data point.
        :param infile:
        :param index: index of the entry.
        :param radius:
        :param loc_col:
        :param ctry_col:
        :param lat_col:
        :param lng_col:
        :param clr0: color of the given data point.
        :param clr1: color of the other points.
        :return: all of the data points as Marker objects.
        """
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})
        if index < len(df):
            coords = (df.loc[index, lat_col], df.loc[index, lng_col])
            location = '%s, %s' % (df.loc[index, loc_col], df.loc[index, ctry_col])
            return self.plot_within_range(infile, coords, radius, loc_col, ctry_col, lat_col, lng_col, location, clr0, clr1)
        else:
            raise KeyError('Index out of range.')
