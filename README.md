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

Easy install dependencies:
```
cd path/to/IaaGeoDataCleaning
pip install requirements.txt
```

Using pip:
```
pip install IaaGeoDataCleaning
```

From source:
```
python setup.py install
```
### Usage
To perform data cleaning on a .csv or .xlsx file, ```import IaaGeoDataCleaning.TableUtils.TableTool as TableTool```.
Data cleaning on a file can be performed by instantiating a TableTools Object and call its clean_table() method. \
The cleaned data will be saved in the same directory as the original data, and will include
the verified entries, pending entries, and repeated entries.

```
cleaner = TableTool(file_path=<path to data>)
cleaner.clean_table()
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

Continued development by [Samantha Fritsche ](https://github.com/Sammy-F) and [Thy Nguyen ](https://github.com/thytng).

Initial development by  [Jonathan Scott ](https://github.com/lionely/).

Many thanks to [Getiria Onsongo](https://github.com/getiria-onsongo/) for his mentorship in development of this package.

### Contributing

Feel free to submit a pull request if you have any features/improvements to add to the package. \
You can also open an issue if you ecountered a problem while using the current core functionalities of the package.

