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

If you encounter gdal installation error on a Mac when using setup.py, a workaround is to set python path: 

``` 
PYTHONPATH=/usr/local/Cellar/gdal/2.3.0/lib/python3.6/site-packages
```
 
### Usage
To perform data cleaning on a .csv or .xlsx file, ```from IaaGeoDataCleaning.CleaningUtils.coordinates_validator import *```.
Data cleaning on a file can be performed by instantiating a GeocodeValidator Object and running the following series of methods.
For a full walkthrough of various methods, go to [examples.ipynb](IaaGeoDataCleaning/CleaningUtils/examples.ipynb). 

```
# First, we read in and process the shapefile. 
# In order to clean, we need to standardize the projection, so we project it to SRID4326.
shape_dir = '/path/to/map/dir'
shape_dict = process_shapefile(shape_dir)
shape_gdf = get_shape(shape_dict['shp'])
crs = get_projection(shape_dict['prj'])

# We read in the data file.
# We require a country code, so if there isn't a country code row in the original data,
# we pass it to add_country_code() to add the code, determined from the recorded country.
df = read_file('/path/to/data.xlsx')
cc_df = add_country_code(data=df, ctry_col='Country')

# We can filter out some data by removing all those entries that have no lat/lng
filtered_df = filter_data_without_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude')

# We want to check common errors caused by lat/lng being flipped, so we generate a
# list of possible coordinates.
coords_gdf_list = flip_coords(data=cc_df, lat_col='Latitude', lng_col='Longitude', prj=crs)

res = check_data_geom(eval_col='Location', iso2_col='ISO2', all_geodata=coords_gdf_list[0], 
                     shapedata=shape_gdf, shape_geom_col='geometry', shape_iso2_col='ISO2')
corrects = res[0]

export_df(corrects, '.csv', 'corrects', 'path/to/dir')
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

Usage samples can be found in the [documentation](https://sammy-f.github.io/IaaGeoDataCleaning/).

### Acknowledgments:

Continued development by [Samantha Fritsche](https://github.com/Sammy-F) and [Thy Nguyen](https://github.com/thytng).

Initial development by  [Jonathan Scott](https://github.com/lionely/).

Many thanks to [Getiria Onsongo](https://github.com/getiria-onsongo/) for his mentorship in development of this package.

This package comes with world border data from [thematicmapping.org](http://thematicmapping.org/downloads/world_borders.php).

### Contributing

Feel free to submit a pull request if you have any features/improvements to add to the package. \
You can also open an issue if you encountered a problem while using the current core functionalities of the package.

