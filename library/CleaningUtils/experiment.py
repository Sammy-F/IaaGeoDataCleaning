import os
import geopandas as gpd
import geopy as gp
from sridentify import Sridentify
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
import timeit
import country_converter as coco
from itertools import product
from geopy.exc import GeocoderTimedOut


class GeocodeValidator:
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

    def read_data(self, data, cols):
        if isinstance(data, str):
            df = self.read_file(data)
        elif isinstance(data, pd.DataFrame) or isinstance(data, gpd.GeoDataFrame):
            df = data
        else:
            raise TypeError('Cannot read data type.')
        if self.check_columns(df, cols):
            return df

    def filter_data_without_coords(self, data, lat_col, lng_col):
        data = self.read_data(data, {lat_col, lng_col})

        with_coords = data.index[(data[lat_col] != 0) & (data[lng_col] != 0) &
                                 pd.notnull(data[lat_col]) & pd.notnull(data[lng_col])].tolist()
        with_coords_df = data.loc[with_coords]
        without_coords_df = data[~data.index.isin(with_coords)]

        return with_coords_df, without_coords_df

    def add_country_code(self, data, ctry_col):
        df = self.read_data(data, {ctry_col})
        df['ISO2'] = None
        df['ISO3'] = None

        df['ISO2'] = coco.convert(names=list(df[ctry_col]), to='ISO2')
        df['ISO3'] = coco.convert(names=list(df[ctry_col]), to='ISO3')

        return df

    def flip_coords(self, data, lat_col, lng_col, prj):
        def create_comb(nums):
            return list(product(*((x, -x) for x in nums)))

        df = self.read_data(data, {lat_col, lng_col})

        temp_lat_lng = list(df.apply(lambda row: create_comb([row[lat_col], row[lng_col]]), axis=1))
        temp_lng_lat = list(df.apply(lambda row: create_comb([row[lng_col], row[lat_col]]), axis=1))
        temp_coords = [temp_lat_lng[i] + temp_lng_lat[i] for i in range(len(temp_lat_lng))]

        all_gdfs = list()
        for i in range(8):
            ndf = pd.DataFrame.copy(df)
            ndf['temp_lat'] = [loc[i][0] for loc in temp_coords]
            ndf['temp_lng'] = [loc[i][1] for loc in temp_coords]
            gdf = self.to_gdf(ndf, 'temp_lat', 'temp_lng', prj)
            all_gdfs.append(gdf)

        return all_gdfs

    def to_gdf(self, data, lat_col, lng_col, prj):
        df = self.read_data(data, {lat_col, lng_col})
        df.fillna({lat_col: 0, lng_col: 0}, inplace=True)
        geometry = [Point(coords) for coords in zip(df[lng_col], df[lat_col])]
        crs = {'init': 'epsg:' + str(prj)}

        return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    def export_df(self, df, format, filename, directory):
        format = format.lower().replace('.', '')
        file_path = os.path.join(directory, '.'.join((filename, format)))
        if format.endswith('csv'):
            df.to_csv(file_path, index=False)
        elif format.endswith('xlsx'):
            df.to_excel(file_path, index=False)

    def rtree(self, sindex, geodata, polygon):
        if isinstance(polygon, Polygon):
            polygon = MultiPolygon([polygon])

        possible_matches_index = list(sindex.intersection(polygon.bounds))
        possible_matches = geodata.iloc[possible_matches_index]     # geodataframe
        precise_matches = possible_matches[possible_matches.intersects(polygon)]    # dataframe

        return precise_matches

    def check_country_geom(self, geodata, shapedata):
        spatial_indices = geodata.sindex

        outdata = pd.DataFrame(columns=list(geodata.columns))

        for index, row in shapedata.iterrows():
            stations_within = self.rtree(spatial_indices, geodata, row['geometry'])
            if len(stations_within) > 0:
                stations_within['PolyCountry'] = row['NAME']
                stations_within['PolyISO2'] = row['ISO_A2']
                stations_within['PolyISO3'] = row['ISO_A3']
                stations_within = self.cross_check_cc(stations_within)
                outdata = outdata.append(stations_within, sort=True, ignore_index=True)

        return outdata

    def geocode_locations(self, data, loc_col, ctry_col):
        df = self.read_data(data, {ctry_col})

        gdf = pd.DataFrame()

        pht = gp.Photon(timeout=3)

        for index, row in df.iterrows():
            if pd.isnull(row[loc_col]):
                lwr = ''
            else:
                lwr = row[loc_col]
            if pd.isnull(row[ctry_col]):
                hgr = ''
            else:
                hgr = row[ctry_col]
            iso2 = coco.convert(hgr, to='ISO2')

            try:
                matches = pht.geocode(lwr + ', ' + hgr, exactly_one=False)
                if matches:
                    for match in matches:
                        match_country = match.address.split(',')[-1]
                        match_iso2 = coco.convert(match_country, to='ISO2')

                        if match_iso2 == iso2:
                            row['Geocoded_Lat'] = match.latitude
                            row['Geocoded_Lng'] = match.longitude
                            row['Geocoded_Adr'] = match.address
                            gdf = gdf.append(row, ignore_index=True)

                            break
            except GeocoderTimedOut:
                continue

        gdf.to_csv('geocoded_locations.csv')

        idf = df[~df[loc_col].isin(gdf[loc_col])]

        idf.to_csv('pending_locations.csv')

        return gdf, idf

    def cross_check_cc(self, data):
        indices = [index for index, row in data.iterrows() if row['ISO2'] == row['PolyISO2']]
        matched_df = data.loc[indices]
        return matched_df

    def check_multiple(self, eval_col, all_geodata, shapedata):
        matched_dfs = []
        orig_input_df = all_geodata[0]
        for i in range(len(all_geodata)):
            start = timeit.default_timer()
            df = self.check_country_geom(all_geodata[i], shapedata)

            if i > 0:
                df = df[~df[eval_col].isin(orig_input_df[eval_col])]
            matched_dfs.append(df)
            df.to_csv('flip_' + str(i) + '.csv', index=False)

            stop = timeit.default_timer()
            print(stop-start)

        matched_data = pd.DataFrame(columns=list(orig_input_df.columns))

        for data in matched_dfs:
            matched_data = matched_data.append(data, sort=True, ignore_index=True)

        remaining_data = orig_input_df[~orig_input_df[eval_col].isin(matched_data[eval_col])]
        remaining_data.to_csv('invalid_locations.csv', index=False)
        matched_data.to_csv('logged_locations.csv', index=False)

        return matched_data, remaining_data


start = timeit.default_timer()
gv = GeocodeValidator()
mapfile = gv.process_shapefile('/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/ne_50m_admin_0_countries')
shp = gv.get_shape(mapfile['shp'])
prj = gv.get_projection(mapfile['prj'])
print('removing coords')
filtered = gv.filter_data_without_coords('/Users/thytnguyen/Desktop/geodata-2018/IaaGeoDataCleaning/resources/xlsx/tblLocation.xlsx',
                                         'Latitude', 'Longitude')
with_coords = filtered[0]
print('adding cc')
with_cc = gv.add_country_code(with_coords, 'Country')

print('flipping')
data_dict = gv.flip_coords(with_cc, 'Latitude', 'Longitude', prj)

print('checking')
res = gv.check_multiple('Location', data_dict, shp)

stop = timeit.default_timer()
print(stop - start)

print('geocoding')
start = timeit.default_timer()

without_coords = filtered[1]
remaining_df = res[1]
to_geocode = without_coords.append(remaining_df, sort=True)

geocoded_res = gv.geocode_locations(to_geocode, 'Location', 'Country')
stop = timeit.default_timer()
print(stop - start)
