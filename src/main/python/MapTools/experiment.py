import folium as foli
from folium.plugins import MarkerCluster
import os
from src.main.python.IaaGeoDataCleaning.verify import Point, gpd, np, pd

class MapTool:
    def __init__(self):
        mapFile = str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                                             'resources', 'mapinfo', 'TM_WORLD_BORDERS-0.3.shp')))
        self.map = self.read_file(mapFile)

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
        return foli.Map(location=center, zoom_start=zoom)

    def plot_point(self, lat, lng, desc=None, clr='blue'):
        if desc:
            marker = foli.Marker((lat, lng), popup=foli.Popup(desc, parse_html=True),
                                 icon=foli.Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        else:
            marker = foli.Marker((lat, lng), icon=foli.Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
        return marker

    def plot_all_stations(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=True):
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})

        loc_list = list(df[loc_col])
        ctry_list = list(df[ctry_col])
        lat_list = list(df[lat_col])
        lng_list = list(df[lng_col])

        if as_cluster:
            popups = [foli.Popup('%s, %s' % (loc_list[i], ctry_list[i]), parse_html=True) for i in range(len(loc_list))]
            coords = [(lat_list[i], lng_list[i]) for i in range(len(lat_list))]
            icons = [foli.Icon(prefix='fa', color=clr, icon='circle', icon_color='white') for i in range(len(df))]

            cluster = MarkerCluster(locations=coords, icons=icons, popups=popups)
            return cluster
        else:
            markers = [self.plot_point(lat=lat_list[i], lng=lng_list[i], desc='%s, %s' % (loc_list[i], ctry_list[i]),
                                       clr=clr) for i in range(len(df))]
            return markers

    def plot_potential_errors(self, infile, loc_col, ctry_col, lat_col, lng_col, clr='lightred', as_cluster=False):
        df = self.clean_dataframe(infile, {loc_col, ctry_col, lat_col, lng_col})

        coords = []
        popups = []
        icons = []

        markers = []

        for (index, row) in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                lat = row[lat_col]
                lng = row[lng_col]
                if pd.isnull(row[loc_col]):
                    loc = ''
                else:
                    loc = row[loc_col]
                if pd.isnull(row[ctry_col]):
                    ctry = ''
                else:
                    ctry = row[ctry_col]

                point = Point(np.array([lng, lat]))
                filtered = self.map['geometry'].contains(point)
                mLoc = self.map.loc[filtered, 'ISO3']

                if len(list(mLoc)) == 0:
                    if as_cluster:
                        coords.append((lat, lng))
                        popups.append(foli.Popup('%s, %s' % (loc, ctry), parse_html=True))
                        icons.append(foli.Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
                    else:
                        markers.append(self.plot_point(lat=lat, lng=lng, desc='%s, %s' % (loc, ctry), clr=clr))

        if as_cluster:
            return MarkerCluster(locations=coords, popups=popups, icons=icons)
        else:
            return markers

    def plot_type(self, infile, type, type_col, loc_col, ctry_col, lat_col, lng_col, clr='blue', as_cluster=False):
        df = self.clean_dataframe(infile, {type_col, loc_col, ctry_col, lat_col, lng_col})

        coords = []
        popups = []
        icons = []

        markers = []

        for (index, row) in df.iterrows():
            if row[type_col] == type:
                if pd.notnull(row[lat_col]) and pd.notnull(row[lng_col]):
                    lat = row[lat_col]
                    lng = row[lng_col]
                    if pd.isnull(row[loc_col]):
                        loc = ''
                    else:
                        loc = row[loc_col]
                    if pd.isnull(row[ctry_col]):
                        ctry = ''
                    else:
                        ctry = row[ctry_col]

                    if as_cluster:
                        coords.append((lat, lng))
                        popups.append(foli.Popup('%s, %s' % (loc, ctry), parse_html=True))
                        icons.append(foli.Icon(prefix='fa', color=clr, icon='circle', icon_color='white'))
                    else:
                        markers.append(self.plot_point(lat, lng, '%s, %s' % (loc, ctry), clr))

        if as_cluster:
            return MarkerCluster(locations=coords, popups=popups, icons=icons)
        else:
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







