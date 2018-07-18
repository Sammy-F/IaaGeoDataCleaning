# IaaGeoDataCleaning
Finds potential corrupt data entries using geocoding and includes tools for interacting with a PostgreSQL
database.

### Overview
Detects potential corrupt entries in a dataframe.

Marks indices of potentially corrupt entries and allows the user to determine whether recommended changes/geocoded locations are correct.
 In addition, includes tools for maintaining data in a PostgreSQL database. Visualization tools are included to simplify this process.

### Dependencies

* Numpy
* Pandas
* Geopandas (requires GDAL and Fiona)
* Pycountry
* psycopg2
* geopy
* shapely
* folium

### Installation
From source:
```
python setup.py install
```
### Usage
To perform data cleaning on a .csv or .xlsx file, ```from IaaGeoDataCleaning.CleaningUtils.coordinates_validator import *```.
Data cleaning on a file can be performed by instantiating a GeocodeValidator Object and running the following series of methods. 

```
shape_dir = '/path/to/map/dir'
shape_dict = process_shapefile(shape_dir)
shape_gdf = get_shape(shape_dict['shp'])
crs = get_projection(shape_dict['prj'])

df = read_file('/path/to/data.xlsx')
cc_df = add_country_code(data=df, ctry_col='Country')
filtered_df = filter_data_without_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude')

coords_gdf_list = flip_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude', prj=crs)

res = check_data_geom(eval_col='City', iso2_col='ISO2', all_geodata=orig_gdf, shapedata=shape_gdf, 
                      shape_geom_col='geometry', shape_iso2_col='ISO2')
corrects = res[0]

res = check_data_geom(eval_col='City', iso2_col='ISO2', all_geodata=coords_gdf_list, shapedata=shape_gdf,
                     shape_geom_col='geometry', shape_iso2_col='ISO2')]
flipped = res[0]

geocoded_res = geocode_coordinates(data=res[1], loc_col='City', ctry_col='Country')
geocoded = geocoded_res[0]

complete = res[0].append(geocoded_res[0], sort=False, ignore_index=True)

export_df(corrects, '.csv', 'corrects.csv', 'path/to/dir')
export_df(flipped, '.csv', 'fips.csv', 'path/to/dir')
export_df(geocoded, '.csv', 'geocodeds.csv', 'path/to/dir')
export_df(complete, '.csv', 'complete.csv', 'path/to/dir')
```

A courtesy class, Modifier, has been included to allow the user to update data based on file output suggestions from GeocodeValidator in the command line.
The run() method can take optional arguments to define custom column names if needed. The method outputs a file with
the updated corrects locations csv file, as well as updated geocoded and incorrect location files with the validated
locations removed. 

```
from IaaGeoDataCleaning.library.CleaningUtils.DataModifier import Modifier

modifier = Modifier(incorrect_locs='path/to/incorrects.csv', 
                    correct_locs='path/to/corrects.csv',
                    geocoded_locs='path/to/geocodeds.csv')
modifier.run()
```


To interact with the database, ```import IaaGeoDataCleaning.ConnectionUtils.DatabaseConnector.DatabaseConnector as DatabaseConnector``` and ```import IaaGeoDataCleaning.ConnectionUtils.Table.Table as Table```. Instantiate a DatabaseConnector and a Table. If loading data from an existing table, the Table's
name should be passed as the name of the existing table. Otherwise, choose an appropriate unique name. A Connection must also be instantiated using one of 
DatabaseConnector's getConnect methods.

```
connector = DatabaseConnector()
table = Table(tablename='helloworld', databaseConnector=connector)

connector.getConnectFromConfig()
```

Usage samples can be found in the documentation.

### Acknowledgments:

Continued development by [Samantha Fritsche](https://github.com/Sammy-F) and [Thy Nguyen](https://github.com/thytng).

Initial development by  [Jonathan Scott](https://github.com/lionely/).

Many thanks to [Getiria Onsongo](https://github.com/getiria-onsongo/) for his mentorship in development of this package.

### Contributing

Feel free to submit a pull request if you have any features/improvements to add to the package. \
You can also open an issue if you ecountered a problem while using the current core functionalities of the package.

