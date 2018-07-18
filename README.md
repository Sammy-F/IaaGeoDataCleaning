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

Using pip:
```
pip install IaaGeoDataCleaning
```

From source:
```
python setup.py install
```
### Usage
To perform data cleaning on a .csv or .xlsx file, ```from IaaGeoDataCleaning.library.CleaningUtils.experiment import GeocodeValidator```.
Data cleaning on a file can be performed by instantiating a GeocodeValidator Object and running the following series of methods. 

```
gv = GeocodeValidator()
mf = gv.process_shapefile('path/to/shapefile/directory')
shp = gv.get_shape(mf['shp'])
prj = gv.get_projection(mf['prj'])

filtered = gv.filter_data_without_coords('path/to/data.xlsx',
                                         'Latitude', 'Longitude')
with_coords = filtered[0]
with_cc = gv.add_country_code(with_coords, 'Country')

data_dict = gv.flip_coords(with_cc, 'Latitude', 'Longitude', prj)

res = gv.check_multiple('Location', data_dict, shp, shape_geom_col='geometry', shape_ctry_col='NAME', shape_iso2_col='ISO2', shape_iso3_col='ISO3')
pending = res[1].append(filtered[1])

gv.geocode_locations(pending, 'Location', 'Country')
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

