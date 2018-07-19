import os
import re
import pyproj
import geopandas as gpd
import pandas as pd
import geopy as gp
from geopy.exc import GeocoderTimedOut
from sridentify import Sridentify
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import transform
import country_converter as coco
from itertools import product
from functools import partial


def process_shapefile(shapefile=None):
    """
    Take in a shapefile directory and parse the filepath to each file in the directory.

    :param shapefile: filepath to shapefile directory.
    :type shapefile: str
    :return: dictionary with the file extension as keys and the complete filepath as values.
    :rtype: dict of {str: str}

    >>> process_shapefile('/home/example_user/example_shapefile_directory')
    {'dbf': '/home/example_user/example_shapefile_directory/example_shapefile.dbf',
     'prj': '/home/example_user/example_shapefile_directory/example_shapefile.prj',
     'shp': '/home/example_user/example_shapefile_directory/example_shapefile.shp',
     'shx': '/home/example_user/example_shapefile_directory/example_shapefile.shx'}
    """
    dirpath = os.path.abspath(os.path.dirname(__file__))
    if not shapefile:
        shapefile = str(os.path.abspath(os.path.join(dirpath, '..', '..', 'resources', 'mapinfo')))
    file_dict = dict()
    for directory, _, files in os.walk(shapefile):
        for file in files:
            file_path = os.path.abspath(os.path.join(directory, file))
            file_dict[file_path[-3:]] = file_path
    return file_dict


def get_shape(shp_file):
    """
    Generate a GeoDataFrame from .shp file.

    :param shp_file: filepath to the .shp file.
    :type shp_file: str.
    :return:
    :rtype: geopandas.GeoDataFrame
    """
    return gpd.read_file(shp_file)


def get_projection(prj_file):
    """
    Determine the EPSG code from .prj file.

    :param prj_file: filepath to the .prj file.
    :type prj_file: str.
    :return:
    :rtype: int.

    >>> get_projection('/home/example_user/example_shapefile_directory/example_shapefile.prj')
    4326
    """
    srider = Sridentify()
    srider.from_file(prj_file)
    return srider.get_epsg()


def read_file(file_path):
    """
    Generate a dataframe from .xlsx or .csv file.

    :param file_path:
    :type file_path: str.
    :return:
    :rtype: DataFrame.
    :raise TypeError: if the file extension is not .csv or .xlsx.
    """
    if file_path.endswith('.xlsx'):
        data = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        data = pd.read_csv(file_path)
    else:
        raise TypeError('Support is only available for .xlsx and .csv files.')
    return data


def check_columns(df, cols):
    """
    Check to see whether the column names are present in the dataframe.

    :param df:
    :type df: DataFrame or geopandas.GeoDataFrame.
    :param cols:
    :type cols: list of str or set of str.
    :return:
    :rtype: bool.
    :raise KeyError: if any of the column names cannot be found in the dataframe.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'Location': ['Beijing', 'Sao Paulo', 'Amsterdam'],
    ...                    'Country': ['China', 'Brazil', 'Netherlands']})
    >>> df
        Location      Country
    0    Beijing        China
    1  Sao Paulo       Brazil
    2  Amsterdam  Netherlands
    >>> check_columns(df=df, cols=['Country', 'Location'])
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


def read_data(data, cols):
    """
    Generate a dataframe and verify that the specified columns are in the dataframe.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str, DataFrame, geopandas.GeoDataFrame
    :param cols:
    :type cols: list of str or set of str.
    :rtype: DataFrame if the type of `data` is DataFrame or str, or geopandas.GeoDataFrame if it is geopandas.GeoDataFrame.
    :raises TypeError: if a different type is passed for `data` or the file extension is not .csv or .xlsx.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Delhi', 'Giza'], 'Country': ['India', 'Egypt'],
    ...                    'Latitude': [28.68, 30.01], 'Longitude': [77.22, 31.13]})
    >>> read_data(data=df, cols={'Country', 'Latitude', 'Longitude'})
        City Country  Latitude  Longitude
    0  Delhi   India     28.68      77.22
    1   Giza   Egypt     30.01      31.13
    """
    if isinstance(data, str):
        df = read_file(data)
    elif isinstance(data, pd.DataFrame) or isinstance(data, gpd.GeoDataFrame):
        df = data
    else:
        raise TypeError('Cannot read data type.')
    if check_columns(df, cols):
        return df


def filter_data_without_coords(data, lat_col, lng_col):
    """
    Generate two dataframes to filter out entries where no latitudinal and longitudinal data was entered.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str, DataFrame, geopandas.GeoDataFrame.
    :param lat_col: name of the latitude column.
    :type lat_col: str.
    :param lng_col: name of the longitude column.
    :type lng_col: str.
    :return: two dataframes, one with all of the entries with coordinates and one of those without.
    :rtype: tuple of (DataFrame, DataFrame) if the type of `data` is DataFrame or str,
            tuple of (geopandas.GeoDataFrame, geopandas.GeoDataFrame) if it is geopandas.GeoDataFrame.

    .. note::
        Entries whose latitude and longitude are both 0 are considered as having no inputs.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Addis Ababa', 'Manila', 'Dubai'],
    ...                    'Country': ['Ethiopia', 'Philippines', 'United Arab Emirates'],
    ...                    'Latitude': [8.98, 14.35, 0], 'Longitude': [38.76, 21.00, 0]})
    >>> filter_data_without_coords(data=df, lat_col='Latitude', lng_col='Longitude')
    (         City      Country  Latitude  Longitude
    0  Addis Ababa     Ethiopia      8.98      38.76
    1       Manila  Philippines     14.35      21.00,
        City               Country  Latitude  Longitude
    2  Dubai  United Arab Emirates       0.0        0.0)
    """
    data = read_data(data, {lat_col, lng_col})

    with_coords = data.index[(data[lat_col] != 0) & (data[lng_col] != 0) &
                             pd.notnull(data[lat_col]) & pd.notnull(data[lng_col])].tolist()
    with_coords_df = data.loc[with_coords]
    without_coords_df = data[~data.index.isin(with_coords)]

    return with_coords_df, without_coords_df


def add_country_code(data, ctry_col):
    """
    Append two new columns to the data containing each entry's country's country codes.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str, DataFrame, geopandas.GeoDataFrame.
    :param ctry_col: name of the country column.
    :type ctry_col: str.
    :return: the modified dataframe with the new columns 'ISO2' and 'ISO3' for two-letter and three-letter country
             codes respectively.
    :rtype: DataFrame if the type of `data` is DataFrame or str, or geopandas.GeoDataFrame if it is geopandas.GeoDataFrame.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Rabat', 'Lyon', 'Cleveland'],
    ...                    'Country': ['Morocco', 'France', 'United States of America']})
    >>> add_country_code(df=data, ctry_col='Country')
            City                   Country ISO2 ISO3
    0      Rabat                   Morocco   MA  MAR
    1       Lyon                    France   FR  FRA
    2  Cleveland  United States of America   US  USA
    """
    df = read_data(data, {ctry_col})
    df['ISO2'] = None
    df['ISO3'] = None

    df['ISO2'] = coco.convert(names=list(df[ctry_col]), to='ISO2')
    df['ISO3'] = coco.convert(names=list(df[ctry_col]), to='ISO3')

    return df


def flip_coords(data, lat_col, lng_col, prj=4326):
    """
    Generate 8 geopandas.GeoDataFrames, each with two columns comprising one latitude-longitude combination among
    [(lat, lng), (lat, -lng), (-lat, lng), (-lat, -lng),
     (lng, lat), (lng, -lat), (-lng, lat), (-lng, -lat)].

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str, DataFrame, geopandas.GeoDataFrame.
    :param lat_col: name of the latitude column.
    :type lat_col: str.
    :param lng_col: name of the longitude column.
    :type lng_col: str.
    :param prj: EPSG code for spatial projection.
    :type prj: int.
    :return:
    :rtype: list of geopandas.GeoDataFrame.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Addis Ababa', 'Manila', 'Vienna', 'Mexico City', 'Puebla'],
    ...                    'Country': ['Ethiopia', 'Philippines', 'Austria', 'Mexico', 'Mexico'],
    ...                    'Latitude': [8.98, 14.35, 0, 19.25, None], 'Longitude': [38.76, 21.00, 0, -99.10, None]})
    >>> dfs = flip_coords(data=df, lat_col='Latitude', lng_col='Latitude', prj=4326)
    >>> dfs[1]
              City      Country  Latitude  Longitude  Flipped_Lat  Flipped_Lng             geometry
    0  Addis Ababa  Ethiopia         8.98      38.76         8.98       -38.76  POINT (-38.76 8.98)
    1  Manila       Philippines     14.35      21.00        14.35       -21.00    POINT (-21 14.35)
    2  Vienna       Austria         0.00        0.00         0.00        -0.00         POINT (-0 0)
    3  Mexico City  Mexico          19.25     -99.10        19.25        99.10  POINT (99.10 19.25)
    4  Puebla       Mexico            NaN        NaN         0.00         0.00          POINT (0 0)

    .. note::
        Point geometry is formatted as (lng, lat).

        Null latitude and longitude are converted to 0s.
    """
    def create_comb(nums):
        return list(product(*((x, -x) for x in nums)))

    df = read_data(data, {lat_col, lng_col})

    temp_lat_lng = list(df.apply(lambda row: create_comb([row[lat_col], row[lng_col]]), axis=1))
    temp_lng_lat = list(df.apply(lambda row: create_comb([row[lng_col], row[lat_col]]), axis=1))
    temp_coords = [temp_lat_lng[i] + temp_lng_lat[i] for i in range(len(temp_lat_lng))]

    all_gdfs = list()
    for i in range(8):
        ndf = pd.DataFrame.copy(df)
        ndf['Flipped_Lat'] = [loc[i][0] for loc in temp_coords]
        ndf['Flipped_Lng'] = [loc[i][1] for loc in temp_coords]
        if i > 0:
            ndf['Type'] = 'Flipped'
        else:
            ndf['Type'] = 'Original'
        gdf = to_gdf(ndf, 'Flipped_Lat', 'Flipped_Lng', prj)
        all_gdfs.append(gdf)

    return all_gdfs


def cross_check(data, first_col, second_col):
    """
    Filter all of the entries in `data` whose values for ``first_col`` and ``second_col`` are equal.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str or DataFrame.
    :param first_col: column name.
    :type first_col: str.
    :param second_col: column name.
    :type second_col: str.
    :return: all qualified entries.
    :rtype: DataFrame

    >>> import pandas as pd
    >>> df = pd.DataFrame({'Country': ['Australia', 'Indonesia', 'Denmark'], 'Entered_ISO2': ['AUS', 'ID', 'DK'],
    ...                    'Matched_ISO2': ['AU', 'ID', 'DK']})
    >>> cross_check(data=df, first_col='Entered_ISO2', second_col='Matched_ISO2')
         Country Entered_ISO2 Matched_ISO2
    1  Indonesia           ID           ID
    2    Denmark           DK           DK
    """
    df = read_data(data, {first_col, second_col})
    indices = [index for index, row in df.iterrows() if row[first_col] == row[second_col]]
    matched_df = df.loc[indices]
    return matched_df


def to_gdf(data, lat_col, lng_col, prj=4326):
    """
    Generate a geopandas.GeoDataFrame.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str or DataFrame.
    :param lat_col: name of the latitude column.
    :type lat_col: str.
    :param lng_col: name of the longitude column.
    :type lng_col: str.
    :param prj: EPSG code for spatial projection.
    :type prj: int.
    :return:
    :rtype: geopandas.GeoDataFrame.
    """
    df = read_data(data, {lat_col, lng_col})
    df.fillna({lat_col: 0, lng_col: 0}, inplace=True)
    geometry = [Point(coords) for coords in zip(df[lng_col], df[lat_col])]
    crs = {'init': 'epsg:' + str(prj)}

    return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)


def export_df(df, extension, filename, directory):
    """
    Export the dataframe to a file.

    :param df:
    :type df: DataFrame or geopandas.GeoDataFrame.
    :param extension: outfile extension (.csv or .xlsx).
    :type extension: str.
    :param filename: outfile name (without extension).
    :type filename: str.
    :param directory: outfile directory.
    :type directory: str.
    :return: absolute filepath to outfile.
    :rtype: str.
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


def rtree(geodata, polygon):
    """
    Use geopandas's R-tree implementation to find all of the locations in `geodata` in the spatial polygon.

    :param geodata: dataframe of locations with spatial geometries.
    :type geodata: geopandas.GeoDataFrame.
    :param polygon:
    :type polygon: shapely.geometry.Polygon.
    :return: all of the entries with locations in the polygon.
    :rtype: geopandas.GeoDataFrame.
    """
    if not isinstance(geodata, gpd.GeoDataFrame):
        raise TypeError('Data must be a geopandas GeoDataFrame.')

    sindex = geodata.sindex
    if isinstance(polygon, Polygon):
        polygon = MultiPolygon([polygon])

    possible_matches_index = list(sindex.intersection(polygon.bounds))
    possible_matches = geodata.iloc[possible_matches_index]     # geodataframe
    precise_matches = possible_matches[possible_matches.intersects(polygon)]    # dataframe

    return precise_matches


def check_country_geom(geodata, geo_iso2_col, shapedata, shape_geom_col, shape_iso2_col):
    """
    Filter all of the entries in `geodata` whose coordinates are within their indicated country by
    iterating through a shapefile of country polygons and finding locations that are in each polygon.

    :param geodata: dataframe of locations with spatial geometries.
    :type geodata: geopandas.GeoDataFrame.
    :param geo_iso2_col: name of the two-letter country code column in dataframe.
    :type geo_iso2_col: str.
    :param shapedata: shapefile dataframe.
    :type shapedata: geopandas.GeoDataFrame.
    :param shape_geom_col: name of the geometry column in the shapefile dataframe.
    :type shape_geom_col: str.
    :param shape_iso2_col: name of the two-letter country code column in the shapefile dataframe.
    :type shape_iso2_col: str.
    :return: all of the entries that were verified as having their location in the respective indicated country.
    :rtype: geopandas.GeoDataFrame.
    """
    outdata = pd.DataFrame(columns=list(geodata.columns))
    shapedata = read_data(shapedata, {shape_geom_col, shape_iso2_col})
    geodata = read_data(geodata, {geo_iso2_col})

    for index, row in shapedata.iterrows():
        stations_within = rtree(geodata, row[shape_geom_col])
        if len(stations_within) > 0:
            stations_within['Poly_ISO2'] = row[shape_iso2_col]
            stations_within = cross_check(stations_within, geo_iso2_col, 'Poly_ISO2')
            stations_within = stations_within.drop(['Poly_ISO2'], axis=1)
            outdata = outdata.append(stations_within, sort=True, ignore_index=True)

    return outdata


def check_data_geom(eval_col, iso2_col, all_geodata, shapedata, shape_geom_col, shape_iso2_col):
    """
    Take in a collection of spatial dataframes that are variations of a single dataframe and check to see
    which geometry actually fall within the borders of its preset country. If an entry is verified as correct
    with its original inputs, the other variations will not be appended

    Generate two dataframes, one that combines all of the entries in the collection that are marked as verified,
    and one for entries whose respective geometry does not correspond to the preset country for any variation.

    :param eval_col: name of the column to distinguish between entries (should be a column in all of the dataframes).
    :type eval_col: str.
    :param iso2_col: name of the two-letter country code column.
    :type iso2_col: str.
    :param all_geodata: collection of spatial dataframes.
    :type all_geodata: geopandas.GeoDataFrame or list or set of geopandas.GeoDataFrame
    :param shapedata: shapefile dataframe.
    :type shapedata: geopandas.GeoDataFrame.
    :param shape_geom_col: name of the geometry column in the shapefile dataframe.
    :type shape_geom_col: str.
    :param shape_iso2_col: name of the two-letter country code column in the shapefile dataframe.
    :type shape_iso2_col: str.
    :return: two dataframes, one with verified entries, and one with invalid entries.
    :rtype: tuple of (geopandas.GeoDataFrame, geopandas.GeoDataFrame).

    ..note::
        The function assumes that the first dataframe in the collection is the original dataframe.

        The verified dataframe might contain multiple entries for the same initial entry if two or more of its
        variations match its preset country.

        :func:`~experiment.GeocodeValidator.flip_coords` should be called first to generate the dataframe collection
        to optimize this function.

    """

    if not isinstance(all_geodata, list):
        all_geodata = [all_geodata]

    orig_input_df = all_geodata[0]

    if len(all_geodata) > 1:
        alt_input_df = gpd.GeoDataFrame(columns=orig_input_df.columns)
        alt_input_df = alt_input_df.append(all_geodata[1:], sort=False, ignore_index=True)
        eval_dfs = [orig_input_df, alt_input_df]
    else:
        eval_dfs = [orig_input_df]

    matched_dfs = []

    for i in range(len(eval_dfs)):
        df = read_data(eval_dfs[i], {eval_col})

        if i > 0:
            df = df[~df[eval_col].isin(matched_dfs[0][eval_col])]

        df = check_country_geom(df, iso2_col, shapedata, shape_geom_col, shape_iso2_col)
        matched_dfs.append(df)

    matched_data = gpd.GeoDataFrame(columns=orig_input_df.columns)
    if len(matched_dfs) > 0:
        matched_data = matched_data.append(matched_dfs, sort=False, ignore_index=True)

    remaining_data = orig_input_df[~orig_input_df[eval_col].isin(matched_data[eval_col])]

    return matched_data, remaining_data


def geocode_coordinates(data, loc_col, ctry_col):
    """
    Use Photon API to geocode entries based on their location and country to find their coordinates.

    Perform a quick validation of the query result by comparing the returned country to the preset country.

    Three new fields representing the returned address, latitude, and longitude are appended to geocoded entries.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str or DataFrame.
    :param loc_col: name of the location (lower level) column.
    :type loc_col: str.
    :param ctry_col: name of the location (higher level) column.
    :type ctry_col: str.
    :return: two dataframes, one with all of the locations that Photon was able to find, and one with locations that
             could not be queried.
    :rtype: tuple of (DataFrame, DataFrame).

    .. note::
        Returned locations might not be 100% accurate.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Toronto', 'Dhaka', 'San Andres'], 'Country': ['Canada', 'Bangladesh', 'El Salvador']})
    >>> geocode_coordinates(data=df, loc_col='City', ctry_col='City')
    (     City        Country                            Geocoded_Adr  Geocoded_Lat  Geocoded_Lng
    0  Toronto     Canada       Toronto, Ontario, Canada                  43.653963    -79.387207
    1  Dhaka       Bangladesh   Dhaka, 12, Dhaka Division, Bangladesh     23.759357     90.378814,
             City      Country
    3  San Andres  El Salvador)
    """
    df = read_data(data, {ctry_col})

    gdf = pd.DataFrame(columns=df.columns)

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
                        row['Type'] = 'Geocoded'
                        gdf = gdf.append(row, ignore_index=True, sort=True)

                        break
        except GeocoderTimedOut:
            continue

    idf = df[~df[loc_col].isin(gdf[loc_col])]

    return gdf, idf


def cell_in_data(data, val, col, abs_tol=0.1):
    """
    Find the entries whose values in the passed column match the queried value.

    If querying a numeric value, the function will return all entries whose corresponding cells approximate
    the passed value with the specified absolute tolerance.

    If querying a string, the function will return all entries whose corresponding cells contain the passed value,
    case insensitive.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str or DataFrame.
    :param val: queried value.
    :type val: str, int, or float.
    :param col: name of queried column.
    :type col: str.
    :param abs_tol:
    :type abs_tol: float.
    :return: all entries meeting the condition.

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Birmingham', 'Brussels', 'Berlin'], 'Country': ['England', 'Belgium', 'Germany'],
    ...                    'Latitude': [52.48, 50.85, 52.52], 'Longitude': [-1.89, 4.35, 13.40]})
    >>> cell_in_data(data=df, val='brussels', col='City')
           City  Country  Latitude  Longitude
    1  Brussels  Belgium     50.85       4.35
    >>> cell_in_data(data=df, val=52.5, col='Latitude')
             City  Country  Latitude  Longitude
    0  Birmingham  England     52.48      -1.89
    2      Berlin  Germany     52.52      13.40
    """
    df = read_data(data, {col})

    res_df = pd.DataFrame()

    if pd.notnull(val):
        if isinstance(val, float) or isinstance(val, int):
            val = float(val)
            res_df = df[(df[col] - val).abs() < abs_tol]

        elif isinstance(val, str):
            res_df = df[df[col].str.contains(val, flags=re.IGNORECASE, regex=True)]

    return res_df


def query_data(data, query_dict, excl=False):
    """
    Find all entries that meet the conditions specified in the query dictionary.

    If ``excl=True``, the function only returns entries meeting every single criteria. Else, it returns any entry
    that meets at least one of the conditions.

    :param data: filepath (.csv or .xlsx extension) or dataframe.
    :type data: str or DataFrame.
    :param query_dict: dictionary whose keys are column names mapping to the queried value(s).
    :type query_dict: dict of {str: list, str: set, or str: str}.
    :param excl: exclusive or inclusive search.
    :type excl: bool.
    :return: all entries meeting the condition(s).

    >>> import pandas as pd
    >>> df = pd.DataFrame({'City': ['Birmingham', 'Brussels', 'Berlin'], 'Country': ['England', 'Belgium', 'Germany'],
    ...                    'Latitude': [52.48, 50.85, 52.52], 'Longitude': [-1.89, 4.35, 13.40]})
    >>> query_data(data=df, query_dict={'Latitude': [52.5, 40], 'City': 'Berlin'}, excl=False)
             City  Country  Latitude  Longitude
    0  Birmingham  England     52.48      -1.89
    2      Berlin  Germany     52.52      13.40
    >>> query_data(data=df, query_dict={'Latitude': 52.5, 'City': 'berlin'}, excl=True)
         City  Country  Latitude  Longitude
    2  Berlin  Germany     52.52       13.4
    """
    df = read_data(data, query_dict.keys())
    res_df = pd.DataFrame()

    for col, val in query_dict.items():
        if isinstance(val, list) or isinstance(val, set):
            for item in val:
                res_df = res_df.append(cell_in_data(df, item, col), sort=False)
        else:
            res_df = res_df.append(cell_in_data(df, val, col), sort=False)

    # TODO: fix handling of non-hashable types.
    if len(res_df) > 0:
        eval_cols = list(res_df.columns)
        if "geometry" in eval_cols:
            eval_cols.remove("geometry")
        if excl:
            return res_df[res_df.duplicated(subset=eval_cols)]
        else:
            return res_df.drop_duplicates(subset=eval_cols)
    return res_df


def convert_df_crs(df, out_crs=4326):
    """Change projection from input projection to provided crs (defaults to 4326)"""
    def get_formatted_crs(crs):
        """Determine correct crs string based on provided [out_crs] value"""
        try:
           new_crs = pyproj.Proj(crs)
           dcs = new_crs
           ncrs_str = crs
        except AttributeError:
           try:
               float(crs)
               new_crs = 'epsg:{}'.format(crs)
               dcs = pyproj.Proj(init=new_crs)
               ncrs_str = {'init': '{}'.format(new_crs)}
           except TypeError:
               new_crs = crs
               dcs = pyproj.Proj(init=new_crs)
               ncrs_str = {'init': new_crs}
        except RuntimeError:
           new_crs = out_crs
           dcs = pyproj.Proj(new_crs)
           ncrs_str = new_crs

        return dcs, new_crs, ncrs_str

    scs, _,_ = get_formatted_crs(df.crs)
    # get destination coordinate system, new coordinate system and new crs string
    dcs, new_crs, ncrs_str = get_formatted_crs(out_crs)
    project = partial(
       pyproj.transform,
       scs,  # source coordinate system
       dcs)  # destination coordinate system
    new_df = df[[x for x in df.columns if x != 'geometry']]
    new_geom = [transform(project, x) for x in df.geometry.values]
    new_df['geometry'] = new_geom
    new_spat_df = gpd.GeoDataFrame(new_df, crs=ncrs_str, geometry='geometry')
    # return dataframe with converted geometry
    return new_spat_df


shape_dict = process_shapefile()
shape_gdf = get_shape(shape_dict['shp'])
crs = get_projection(shape_dict['prj'])
df = read_file('D:\\PyCharm Projects\\IaaGeoDataCleaning\\resources\\xlsx\\tblLocation.xlsx')
cc_df = add_country_code(data=df, ctry_col='Country')
filtered_df = filter_data_without_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude')
coords_gdf_list = flip_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude', prj=crs)
corrects = check_data_geom(eval_col='Location', iso2_col='ISO2', all_geodata=coords_gdf_list[0], shapedata=shape_gdf, shape_geom_col='geometry', shape_iso2_col='ISO2')
flips = check_data_geom(eval_col='Location', iso2_col='ISO2', all_geodata=coords_gdf_list, shapedata=shape_gdf, shape_geom_col='geometry', shape_iso2_col='ISO2')
geocoded = geocode_coordinates(data=flips[1], loc_col='Location', ctry_col='Country')
flipped = flips[0]
export_df(corrects, '.csv', 'corrects', 'D:\\PyCharm Projects\\IaaGeoDataCleaning')
export_df(flipped, '.csv', 'flipped', 'D:\\PyCharm Projects\\IaaGeoDataCleaning')
export_df(geocoded[0], '.csv', 'geocoded', 'D:\\PyCharm Projects\\IaaGeoDataCleaning')