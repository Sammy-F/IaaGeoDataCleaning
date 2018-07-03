# from folium import Map, Icon, Marker, CircleMarker
from src.main.python.TableUtils import TableTools
import os
from ipyleaflet import Map, Marker, Circle
class MapTool:
    def __init__(self, file_path=str(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                                                                  'tblLocation', 'verified_entries.csv'))),
                 outfile_type='.csv', loc_col='Location', ctry_col='Country', reg_col='Region',
                 lat_col='Recorded_Lat', lng_col='Recorded_Lng'):

        self.tableTools = TableTools(file_path=file_path, loc_col=loc_col, ctry_col=ctry_col,
                                     reg_col=reg_col, lat_col=lat_col, lng_col=lng_col)

    # def plot_point(self, lat, lng, desc=None):
    #     m = Map(location=[lat, lng], zoom_start=5)
    #     if desc:
    #         marker = Marker([lat, lng], popup=desc, icon=Icon(prefix='fa', icon='circle', icon_color='white'))
    #     else:
    #         marker = Marker([lat, lng], icon=Icon(prefix='fa', icon='circle', icon_color='white'))
    #     m.add_child(marker)
    #     return m

    def plot_all_stations(self):
        # m = Map(location=[0, 0], zoom_start=2)
        m = Map(center=(0, 0), zoom=2)

        lat_list = list(self.tableTools.df[self.tableTools.lat_col])
        lng_list = list(self.tableTools.df[self.tableTools.lng_col])
        loc_list = list(self.tableTools.df[self.tableTools.loc_col])
        ctry_list = list(self.tableTools.df[self.tableTools.ctry_col])

        for i in range(len(loc_list)):
            point = Circle(location=(lat_list[i], lng_list[i]), opacity=0.3, radius=5)
            m.add_layer(point)

        return m

