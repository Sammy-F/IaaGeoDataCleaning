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
        """
        Take in a shapefile directory and parse the filepath to each file in the directory.

        :param shapefile: filepath to shapefile directory.
        :type shapefile: str
        :return: dictionary with the file extension as keys and the complete filepath as values.
        :rtype: dict of {str: str}

        >>> validator = GeocodeValidator()
        >>> validator.process_shapefile('/home/example_user/example_shapefile_directory')
        {'dbf': '/home/example_user/example_shapefile_directory/example_shapefile.dbf',
         'prj': '/home/example_user/example_shapefile_directory/example_shapefile.prj',
         'shp': '/home/example_user/example_shapefile_directory/example_shapefile.shp',
         'shx': '/home/example_user/example_shapefile_directory/example_shapefile.shx'}
        """
        file_dict = dict()
        for directory, _, files in os.walk(shapefile):
            for file in files:
                file_path = os.path.abspath(os.path.join(directory, file))
                file_dict[file_path[-3:]] = file_path
        return file_dict

    def get_shape(self, shp_file):
        """
        Generate a GeoDataFrame from .shp file.

        :param shp_file: filepath to the .shp file.
        :type shp_file: str
        :return:
        :rtype: geopandas.GeoDataFrame
        """
        return gpd.read_file(shp_file)

    def get_projection(self, prj_file):
        """
        Determine the EPSG code from .prj file.

        :param prj_file: filepath to the .prj file.
        :type prj_file: str
        :return:
        :rtype: int

        >>> validator = GeocodeValidator()
        >>> validator.get_projection('/home/example_user/example_shapefile_directory/example_shapefile.prj')
        4326
        """
        srider = Sridentify()
        srider.from_file(prj_file)
        return srider.get_epsg()

    def read_file(self, file_path):
        """
        Generate a dataframe from .xlsx or .csv file.

        :param file_path:
        :type file_path: str
        :return:
        :rtype: DataFrame
        :raise TypeError: if the file extension is not .csv or .xlsx.
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
        Check to see whether the column names are present in the dataframe.

        :param df:
        :type df: DataFrame or geopandas.GeoDataFrame
        :param cols:
        :type cols: list of str or set of str
        :return:
        :rtype: bool
        :raise KeyError: if any of the column names cannot be found in the dataframe.

        >>> import pandas as pd
        >>> validator = GeocodeValidator()
        >>> d = {'Location': ['Beijing', 'Sao Paulo', 'Amsterdam'],
        ...      'Country': ['China', 'Brazil', 'Netherlands']}
        >>> df = pd.DataFrame(d)
        >>> df
            Location      Country
        0    Beijing        China
        1  Sao Paulo       Brazil
        2  Amsterdam  Netherlands
        >>> validator.check_columns(df=df, cols=['Country', 'Location'])
        True

        .. note::
            Function will always return True or raise an error.
        """
        if not isinstance(cols, set):
            cols = set(cols)
        if cols.issubset(df.columns):
            return True
        else:
            raise KeyError('Column names not found in data frame.')

    def read_data(self, data, cols):
        """
        Generate a dataframe and verify that the specified columns are in the dataframe.

        :param data: filepath (.csv or .xlsx extension) or dataframe.
        :type data: str, DataFrame, geopandas.GeoDataFrame
        :param cols:
        :type cols: list of str or set of str
        :return:
        :rtype: DataFrame if the type of `data` is DataFrame or str, or geopandas.GeoDataFrame if it is geopandas.GeoDataFrame
        :raises TypeError: if a different type is passed for `data` or the file extension is not .csv or .xlsx.
        :raises KeyError: if any of the column names cannot be found in `data`.

        >>> import pandas as pd
        >>> validator = GeocodeValidator()
        >>> d = {'City': ['Delhi', 'Giza'], 'Country': ['India', 'Egypt'],
        ...      'Latitude': [28.68, 30.01], 'Longitude': [77.22, 31.13]}
        >>> df = pd.DataFrame(d)
        >>> validator.read_data(data=df, cols={'Country', 'Latitude', 'Longitude'})
            City Country  Latitude  Longitude
        0  Delhi   India     28.68      77.22
        1   Giza   Egypt     30.01      31.13
        """
        if isinstance(data, str):
            df = self.read_file(data)
        elif isinstance(data, pd.DataFrame) or isinstance(data, gpd.GeoDataFrame):
            df = data
        else:
            raise TypeError('Cannot read data type.')
        if self.check_columns(df, cols):
            return df

    def filter_data_without_coords(self, data, lat_col, lng_col):
        """
        Generate two dataframes to filter out entries where no latitudinal and longitudinal data was entered.

        :param data: filepath (.csv or .xlsx extension) or dataframe.
        :type data: str, DataFrame, geopandas.GeoDataFrame
        :param lat_col: name of the latitude column.
        :type lat_col: str
        :param lng_col: name of the longitude column.
        :type lng_col: str
        :return: two dataframes, one with all of the entries with coordinates and one of those without.
        :rtype: tuple of (DataFrame, DataFrame) if the type of `data` is DataFrame or str,
                tuple of (geopandas.GeoDataFrame, geopandas.GeoDataFrame) if it is geopandas.GeoDataFrame
        :raises TypeError: if a different type is passed for `data` or the file extension is not .csv or .xlsx.
        :raises KeyError: if any of the column names cannot be found in `data`.

        .. note::
            Entries whose latitude and longitude are both 0 are considered as having no inputs.

        >>> import pandas as pd
        >>> validator = GeocodeValidator()
        >>> d = {'City': ['Addis Ababa', 'Manila', 'Dubai'], 'Country': ['Ethiopia', 'Philippines', 'United Arab Emirates'],
        ...      'Latitude': [8.98, 14.35, 0], 'Longitude': [38.76, 21.00, 0]}
        >>> df = pd.DataFrame(d)
        >>> validator.filter_data_without_coords(data=df, lat_col='Latitude', lng_col='Longitude')
        (         City      Country  Latitude  Longitude
        0  Addis Ababa     Ethiopia      8.98      38.76
        1       Manila  Philippines     14.35      21.00,
            City               Country  Latitude  Longitude
        2  Dubai  United Arab Emirates       0.0        0.0)
        """
        data = self.read_data(data, {lat_col, lng_col})

        with_coords = data.index[(data[lat_col] != 0) & (data[lng_col] != 0) &
                                 pd.notnull(data[lat_col]) & pd.notnull(data[lng_col])].tolist()
        with_coords_df = data.loc[with_coords]
        without_coords_df = data[~data.index.isin(with_coords)]

        return with_coords_df, without_coords_df

    def add_country_code(self, data, ctry_col):
        """
        Append two new columns to the data containing each entry's country's country codes.

        :param data: filepath (.csv or .xlsx extension) or dataframe.
        :type data: str, DataFrame, geopandas.GeoDataFrame
        :param ctry_col: name of the country column.
        :type ctry_col: str
        :return: the modified dataframe with the new columns 'ISO2' and 'ISO3' for two-letter and three-letter country
                 codes respectively.
        :rtype: DataFrame if the type of `data` is DataFrame or str, or geopandas.GeoDataFrame if it is geopandas.GeoDataFrame
        :raises TypeError: if a different type is passed for `data` or the file extension is not .csv or .xlsx.
        :raises KeyError: if the country column's name cannot be found in `data`.

        >>> import pandas as pd
        >>> validator = GeocodeValidator()
        >>> d = {'City': ['Rabat', 'Lyon', 'Cleveland'], 'Country': ['Morocco', 'France', 'United States of America']}
        >>> df = pd.DataFrame(d)
        >>> validator.add_country_code(df=data, ctry_col='Country')
                City                   Country ISO2 ISO3
        0      Rabat                   Morocco   MA  MAR
        1       Lyon                    France   FR  FRA
        2  Cleveland  United States of America   US  USA
        """
        df = self.read_data(data, {ctry_col})
        df['ISO2'] = None
        df['ISO3'] = None

        df['ISO2'] = coco.convert(names=list(df[ctry_col]), to='ISO2')
        df['ISO3'] = coco.convert(names=list(df[ctry_col]), to='ISO3')

        return df

    def flip_coords(self, data, lat_col, lng_col, prj):
        """
        Generate 8 geopandas.GeoDataFrames, each with two columns comprising one latitude-longitude combination among
        [(lat, lng), (lat, -lng), (-lat, lng), (-lat, -lng),
         (lng, lat), (lng, -lat), (-lng, lat), (-lng, -lat)].

        :param data: filepath (.csv or .xlsx extension) or dataframe.
        :type data: str, DataFrame, geopandas.GeoDataFrame
        :param lat_col: name of the latitude column.
        :type lat_col: str
        :param lng_col: name of the longitude column.
        :type lng_col: str
        :param prj: EPSG code for spatial projection.
        :type prj: int
        :return:
        :rtype: list of geopandas.GeoDataFrame
        :raises TypeError: if a different type is passed for `data` or the file extension is not .csv or .xlsx.
        :raises KeyError: if the country column's name cannot be found in `data`.

        >>> import pandas as pd
        >>> validator = GeocodeValidator()
        >>> d = {'City': ['Addis Ababa', 'Manila', 'Vienna', 'Mexico City', 'Puebla'],
        ...      'Country': ['Ethiopia', 'Philippines', 'Austria', 'Mexico', 'Mexico'],
        ...      'Latitude': [8.98, 14.35, 0, 19.25, None], 'Longitude': [38.76, 21.00, 0, -99.10, None]}
        >>> df = pd.DataFrame(d)
        >>> dfs = validator.flip_coords(data=df, lat_col='Latitude', lng_col='Latitude', prj=4326)
        >>> dfs[1]
                  City      Country  Latitude  Longitude  temp_lat  temp_lng             geometry
        0  Addis Ababa  Ethiopia     8.98      38.76      8.98     -38.76     POINT (-38.76 8.98)
        1  Manila       Philippines  14.35     21.00      14.35    -21.00     POINT (-21 14.35)
        2  Vienna       Austria      0.00      0.00       0.00     -0.00      POINT (-0 0)
        3  Mexico City  Mexico       19.25    -99.10      19.25     99.10     POINT (99.10 19.25)
        4  Puebla       Mexico      NaN       NaN         0.00      0.00      POINT (0 0)

        .. note::
            Point geometry is formatted as (lng, lat).

            Null latitude and longitude are converted to 0s.
        """
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
        """
        Generate a geopandas.GeoDataFrame.

        :param data: filepath (.csv or .xlsx extension) or dataframe.
        :type data: str or DataFrame
        :param lat_col: name of the latitude column.
        :type lat_col: str
        :param lng_col: name of the longitude column.
        :type lng_col: str
        :param prj: EPSG code for spatial projection.
        :type prj: int
        :return:
        :rtype: geopandas.GeoDataFrame
        """
        df = self.read_data(data, {lat_col, lng_col})
        df.fillna({lat_col: 0, lng_col: 0}, inplace=True)
        geometry = [Point(coords) for coords in zip(df[lng_col], df[lat_col])]
        crs = {'init': 'epsg:' + str(prj)}

        return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    def export_df(self, df, extension, filename, directory):
        """
        Export the dataframe to a file.

        :param df:
        :type df: DataFrame or geopandas.GeoDataFrame
        :param extension: outfile extension (.csv or .xlsx).
        :type extension: str
        :param filename: outfile name (without extension).
        :type filename: str
        :param directory: outfile directory.
        :type directory: str
        :return: absolute filepath to outfile.
        :rtype: str
        :raise TypeError: if file extension is not csv or  xlsx.
        """

        extension = extension.lower().replace('.', '')
        file_path = os.path.join(directory, '.'.join((filename, extension)))
        if extension.endswith('csv'):
            df.to_csv(file_path, index=False)
        elif extension.endswith('xlsx'):
            df.to_excel(file_path, index=False)
        else:
            raise TypeError('Unsupported file type.')
        return file_path

    def rtree(self, geodata, polygon):
        """
        Use geopandas's R-tree implementation to find all of the locations in `geodata` in the spatial polygon.

        :param geodata: dataframe of locations with spatial geometries.
        :type geodata: geopandas.GeoDataFrame
        :param polygon:
        :type polygon: shapely.geometry.Polygon
        :return: all of the entries with locations in the polygon.
        :rtype: geopandas.GeoDataFrame
        """
        sindex = geodata.sindex
        if isinstance(polygon, Polygon):
            polygon = MultiPolygon([polygon])

        possible_matches_index = list(sindex.intersection(polygon.bounds))
        possible_matches = geodata.iloc[possible_matches_index]     # geodataframe
        precise_matches = possible_matches[possible_matches.intersects(polygon)]    # dataframe

        return precise_matches

    def check_country_geom(self, geodata, shapedata):
        """

        :param geodata: dataframe of locations with spatial geometries.
        :type geodata: geopandas.GeoDataFrame
        :param shapedata: shapefile dataframe.
        :type shapedata: geopandas.GeoDataFrame
        :return: all of the entries that were verified as having their location in the respective indicated country.
        :rtype: geopandas.GeoDataFrame
        """
        outdata = pd.DataFrame(columns=list(geodata.columns))

        for index, row in shapedata.iterrows():
            stations_within = self.rtree(geodata, row['geometry'])
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
                df = df[~df[eval_col].isin(matched_dfs[0][eval_col])]
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
#
# print('geocoding')
# start = timeit.default_timer()
#
# without_coords = filtered[1]
# remaining_df = res[1]
# to_geocode = without_coords.append(remaining_df, sort=True)
#
# geocoded_res = gv.geocode_locations(to_geocode, 'Location', 'Country')
# stop = timeit.default_timer()
# print(stop - start)
