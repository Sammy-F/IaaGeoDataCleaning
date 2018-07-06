from folium import Map, Marker, Icon, Popup
from folium.plugins import MarkerCluster
from os import path
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import math
# TODO: altair, side by side maps, plot stations in a country? continent?


class MapTool:
    def __init__(self):
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
        if not isinstance(cols, set):
            cols = set(cols)
        if cols.issubset(df.columns):
            return True
        else:
            raise KeyError('Column names not found in data frame.')

    def clean_dataframe(self, infile, cols):
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
        rlat0 = math.radians(lat0)
        rlat1 = math.radians(lat1)
        dlat = rlat1 - rlat0
        dlng = math.radians(lng1 - lng0)

        a = math.pow(math.sin(dlat/2), 2) + math.cos(rlat0) * math.cos(rlat1) * math.pow(math.sin(dlng/2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 6371 * c

    def plot_point(self, lat, lng, desc=None, clr='blue'):
        if desc:
            marker = Marker((lat, lng), popup=Popup(desc, parse_html=True),
                            icon=Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        else:
            marker = Marker((lat, lng), icon=Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        return marker

    def plot_all_stations(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=True):
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

    def plot_potential_errors(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='lightred', as_cluster=False):
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
                mLoc = self.map.loc[filtered, 'ISO3']

                if len(list(mLoc)) == 0:
                    marker = self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (location[0], location[1]), clr=clr)
                    if as_cluster:
                        marker.add_to(markers)
                    else:
                        markers.append(marker)

        return markers

    def plot_condition(self, infile, condition, cnd_col, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=False):
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
        df = self.clean_dataframe(infile, {lat0_col, lng0_col, lat1_col, lng1_col})

        if index < len(df):
            coords0 = (df.loc[index, lat0_col], df.loc[index, lng0_col])
            coords1 = (df.loc[index, lat1_col], df.loc[index, lng1_col])

            return self.plot_pair(coords0, coords1, clr0, clr1)
        else:
            raise KeyError('Index out of range.')

    def plot_pair(self, coords0, coords1, clr0='lightblue', clr1='darkblue'):
        marker0 = self.plot_point(lat=coords0[0], lng=coords0[1], desc=str(coords0), clr=clr0)
        marker1 = self.plot_point(lat=coords1[0], lng=coords1[1], desc=str(coords1), clr=clr1)

        return marker0, marker1

    def plot_within_range(self, infile, center, radius, loc_col, ctry_col, lat_col, lng_col, desc0=None, clr0='blue', clr1='lightblue'):
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
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})
        if index < len(df):
            coords = (df.loc[index, lat_col], df.loc[index, lng_col])
            location = '%s, %s' % (df.loc[index, loc_col], df.loc[index, ctry_col])
            return self.plot_within_range(infile, coords, radius, loc_col, ctry_col, lat_col, lng_col, location, clr0, clr1)
        else:
            raise KeyError('Index out of range.')
