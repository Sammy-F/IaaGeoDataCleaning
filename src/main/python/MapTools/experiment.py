from src.main.python.TableUtils import TableTools
import folium as foli
from folium.plugins import MarkerCluster
import os
from src.main.python.IaaGeoDataCleaning.verify import Point, gpd, np, pd

class MapTool:
    def __init__(self, file_path=str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                                                                  'tblLocation', 'verified_entries.csv'))),
                 outfile_type='.csv', loc_col='Location', ctry_col='Country', reg_col='Region',
                 lat_col='Recorded_Lat', lng_col='Recorded_Lng'):

        self.tableTools = TableTools(file_path=file_path, loc_col=loc_col, ctry_col=ctry_col,
                                     reg_col=reg_col, lat_col=lat_col, lng_col=lng_col)

    def plot_point(self, lat, lng, desc=None):
        m = foli.Map(location=[lat, lng], zoom_start=5)
        if desc:
            marker = foli.Marker([lat, lng], popup=desc, icon=foli.Icon(prefix='fa', icon='circle', icon_color='white'))
        else:
            marker = foli.Marker([lat, lng], icon=foli.Icon(prefix='fa', icon='circle', icon_color='white'))
        m.add_child(marker)
        return m

    def plot_all_stations(self):
        m = foli.Map(location=[0, 0], zoom_start=2)

        lat_list = list(self.tableTools.df[self.tableTools.lat_col])
        lng_list = list(self.tableTools.df[self.tableTools.lng_col])
        coord_list = [[lat_list[i], lng_list[i]] for i in range(len(lat_list))]
        loc_list = list(self.tableTools.df[self.tableTools.loc_col])
        ctry_list = list(self.tableTools.df[self.tableTools.ctry_col])
        popup_list = [foli.Popup(loc_list[i] + ', ' + ctry_list[i], parse_html=True) for i in range(len(loc_list))]

        cluster = MarkerCluster(name="Plant Breeding Station Cluster", locations=coord_list, popups=popup_list)
        m.add_child(cluster)

        return m

    def plot_no_country(self):
        m = foli.Map(location=[0, 0], zoom_start=2)

        locations = []
        popups = []
        icons = []

        for (index, row) in self.tableTools.df.iterrows():
            if not (np.isnan(row[self.tableTools.lat_col]) or np.isnan(row[self.tableTools.lng_col])):
                lat = row[self.tableTools.lat_col]
                lng = row[self.tableTools.lng_col]
                if pd.isnull(row[self.tableTools.loc_col]):
                    loc = ''
                else:
                    loc = row[self.tableTools.loc_col]

                if pd.isnull(row[self.tableTools.ctry_col]):
                    ctry = ''
                else:
                    ctry = row[self.tableTools.ctry_col]

                point = Point(np.array([lng, lat]))
                filter = self.tableTools.validator.map['geometry'].contains(point)
                mLoc = self.tableTools.validator.map.loc[filter, 'ISO3']

                if len(list(mLoc)) == 0:
                    locations.append((lat, lng))
                    popups.append(foli.Popup(loc + ', ' + ctry, parse_html=True))
                    icons.append(foli.Icon(prefix='fa', icon='circle', icon_color='white', color='red'))

        cluster = MarkerCluster(name="Out of Border Stations", locations=locations, icons=icons, popups=popups)
        m.add_child(cluster)

        return m, locations

    def plot_geocoded_locations(self):
        m = foli.Map(location=[0, 0], zoom_start=2)

        for (index, row) in self.tableTools.df.iterrows():
            if row['Type'] == 'no lat/lng entered / incorrect lat/lng - geocoded location':
                lat = row[self.tableTools.lat_col]
                lng = row[self.tableTools.lng_col]
                loc = row[self.tableTools.loc_col]
                ctry = row[self.tableTools.ctry_col]

                marker = foli.Marker(location=[lat, lng], popup=foli.Popup(loc + ', ' + ctry, parse_html=True))
                m.add_child(marker)

        return m

    def plot_pair(self, index, orig_lat_col, orig_lng_col, rec_lat_col, rec_lng_col):
        m = foli.Map(location=[0, 0], zoom_start=2)

        orig_lat = self.tableTools.df.loc[index, orig_lat_col]
        orig_lng = self.tableTools.df.loc[index, orig_lng_col]
        rec_lat = self.tableTools.df.loc[index, rec_lat_col]
        rec_lng = self.tableTools.df.loc[index, rec_lng_col]

        loc = self.tableTools.df.loc[index, self.tableTools.loc_col]
        ctry = self.tableTools.df.loc[index, self.tableTools.ctry_col]

        orig_loc = foli.Marker(location=[orig_lat, orig_lng],
                               popup=foli.Popup(loc + ', ' + ctry, parse_html=True),
                               icon=foli.Icon(prefix='fa', icon='circle', icon_color='white', color='red'))
        rec_loc = foli.Marker(location=[rec_lat, rec_lng],
                              popup=foli.Popup(loc + ', ' + ctry, parse_html=True),
                              icon=foli.Icon(prefix='fa', icon='circle', icon_color='white', color='green'))

        m.add_child(orig_loc)
        m.add_child(rec_loc)

        return m

    def compare_points(self, first_coord, second_coord):
        m = foli.Map(location=[0, 0], zoom_start=2)

        first_loc = foli.Marker(location=first_coord,
                                popup=foli.Popup('(%s, %s)' % (first_coord[0], first_coord[1]), parse_html=True),
                                icon=foli.Icon(prefix='fa', icon='circle', icon_color='white', color='green'))
        second_loc = foli.Marker(location=second_coord,
                                 popup=foli.Popup('(%s, %s)' % (second_coord[0], second_coord[1]), parse_html=True),
                                 icon=foli.Icon(prefix='fa', icon='circle', icon_color='white', color='blue'))
        m.add_child(first_loc)
        m.add_child(second_loc)

        return m











