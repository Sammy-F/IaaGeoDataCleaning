# IaaGeoDataCleaning
Finding potential corrupt data entries using geocoding.

### Overview
This a python library for detecting potential corrupt entries in a dataframe.

By using this library, we can locate which entries in the dataframe might be corrupt. This library is capable of marking the index of the row of a potential corrupt data entry. After entries are found we can check the rows by hand and see how to clean the data.
 In addition, the library includes tools for working with data in a PostgreSQL database, whether this involves uploading the cleaned data, updating the database, loading data, etc.

### Dependencies

* Numpy
* Pandas
* Geopandas (requires GDAL and Fiona)
* Pycountry
* psycopg2
* geopy
* shapely

### Installation
```
pip install IaaGeoDataCleaning
```
### Usage
To perform data cleaning on a .csv or .xlsx file, import ```IaaGeoDataCleaning.TableUtils```.

If interacting with a PostgreSQL database, import ```IaaGeoDataCleaning.ConnectionUtils.DatabaseConnector``` and
```IaaGeoDataCleaning.ConnectionUtils.Table```.

Data cleaning on a file can be performed by instantiating a TableTools Object and call its clean_table() method. \
The cleaned data will be saved in the same directory as the original data, and will include
the verified entries, pending entries, and repeated entries.

```
cleaner = TableTools(file_path=<path to data>)
cleaner.clean_table()
```

To interact with the database, instantiate a DatabaseConnector and a Table. If loading data from an existing table, the Table's
name should be passed as the name of the existing table. Otherwise, choose an appropriate unique name. A Connection must also be instantiated using one of 
DatabaseConnector's getConnect methods.

```
connector = DatabaseConnector()
Table = Table(tablename='helloworld', databaseConnector=connector)

connector.getConnectFromConfig()
```



### Acknowledgment:

Continued development by [Samantha Fritsche ](https://github.com/Sammy-F) and [Thy Nguyen ](https://github.com/thytng).

Initial development by  [Jonathan Scott ](https://github.com/lionely/).

Many thanks to [Getiria Onsongo](https://github.com/getiria-onsongo/) for his mentorship in development of this package.

### Contributing

Feel free to submit a pull request if you have any features/improvements to add to the package. \
You can also open an issue if you ecountered a problem while using the current core functionalities \
of the package.
