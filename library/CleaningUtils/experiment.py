import os
import geopandas as gpd
from sridentify import Sridentify
import pandas as pd
from shapely.geometry import Point


class GeocodeValidator:
    def __init__(self, data, lat_col, lng_col, shapefile):
        shapefile = self.process_shapefile(shapefile)
        self.geo_map = self.get_shape(shapefile['shp'])
        self.srid = self.get_projection(shapefile['prj'])
        self.gdf = self.to_gdf(data, lat_col, lng_col, self.srid)

    def process_shapefile(self, shapefile):
        file_dict = dict()
        for directory, _, files in os.walk(shapefile):
            for file in files:
                file_path = os.path.abspath(os.path.join(directory, file))
                file_dict[file_path[-3:]] = file_path
        return file_dict

    def get_shape(self, shp_file):
        return gpd.read_file(shp_file)

    def get_projection(self, prj_file):
        srider = Sridentify()
        srider.from_file(prj_file)
        return srider.get_epsg()

    def read_file(self, file_path):
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

    def clean_dataframe(self, data, cols):
        if isinstance(data, str):
            df = self.read_file(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise TypeError('Cannot read data type.')
        if self.check_columns(df, cols):
            return df

    def to_gdf(self, data, lat_col, lng_col, prj):
        df = self.clean_dataframe(data, {lat_col, lng_col})
        df.fillna({lat_col: 0, lng_col: 0}, inplace=True)
        geometry = [Point(coords) for coords in zip(df[lat_col], df[lng_col])]
        crs = {'init': 'espg:' + str(prj)}

        return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    def rtree(self, geodata, polydata):
        spatial_indices = geodata.sindex
        possible_matches_index = list(spatial_indices.intersection(polydata))


gv = GeocodeValidator('/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/xlsx/tblLocation.xlsx',
                      'Latitude', 'Longitude', '/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/mapinfo')

print(gv.gdf.sindex)




