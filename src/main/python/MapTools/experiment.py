from src.main.python.TableUtils import TableTools
import folium as foli
from folium.plugins import MarkerCluster
import os

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
        marker.render(icon=foli.Icon(prefix='fa', icon='circle', icon_color='orange'))
        return m

    def plot_all_stations(self):
        m = foli.Map(location=[0, 0], zoom_start=2)

        lat_list = list(self.tableTools.df[self.tableTools.lat_col])
        lng_list = list(self.tableTools.df[self.tableTools.lng_col])
        coord_list = [[lat_list[i], lng_list[i]] for i in range(len(lat_list))]

        cluster = MarkerCluster(name="Plant Breeding Station Cluster", locations=coord_list)
        m.add_child(cluster)

        return m
