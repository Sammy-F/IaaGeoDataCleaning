import os
import geopandas as gpd
from sridentify import Sridentify
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
import pycountry as pc
import timeit
import country_converter as coco


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

    def add_country_code(self, data, ctry_col):
        df = self.clean_dataframe(data, {ctry_col})
        df['ISO2'] = None
        df['ISO3'] = None

        for (index, row) in df.iterrows():
            try:
                ctry_res = pc.countries.lookup(row[ctry_col])
                df.loc[index, 'alpha_2'] = ctry_res.alpha_2
                df.loc[index, 'alpha_3'] = ctry_res.alpha_3
            except LookupError:
                continue

        return df

    def to_gdf(self, data, lat_col, lng_col, prj):
        df = self.clean_dataframe(data, {lat_col, lng_col})
        df.fillna({lat_col: 0, lng_col: 0}, inplace=True)
        geometry = [Point(coords) for coords in zip(df[lng_col], df[lat_col])]
        crs = {'init': 'epsg:' + str(prj)}

        return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    def rtree(self, sindex, geodata, polygon):
        if isinstance(polygon, Polygon):
            polygon = MultiPolygon([polygon])

        possible_matches_index = list(sindex.intersection(polygon.bounds))
        possible_matches = geodata.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(polygon)]

        return precise_matches

    def check_country(self, geodata, shapedata):
        start = timeit.default_timer()
        spatial_indices = geodata.sindex

        outdata = pd.DataFrame(columns=list(geodata.columns) + ['PolyCountry'])
        with open('rtree_test.csv', mode='a') as output:
            outdata.to_csv(path_or_buf=output, index=False)
            for index, row in shapedata.iterrows():
                stations_within = self.rtree(spatial_indices, geodata, row['geometry'])
                stations_within['PolyCountry'] = row['NAME']
                stations_within.to_csv(path_or_buf=output, index=False, mode='a', header=False)
        stop = timeit.default_timer()
        print(stop-start)



gv = GeocodeValidator('/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/xlsx/tblLocation.xlsx',
                      'Latitude', 'Longitude', '/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/mapinfo')
gv.check_country(gv.gdf, gv.geo_map)
# res = gv.rtree(gv.gdf, gv.geo_map['geometry'].iloc[29])
# print(type(res))
# gv.gdf.to_csv('/Users/thytnguyen/Desktop/test.csv')

