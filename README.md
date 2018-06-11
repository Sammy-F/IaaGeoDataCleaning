# IaaGeoDataCleaning
Finding potential corrupt data entries using geocoding.

### Overview
This a python library for detecting potential corrupt entries in a dataframe.

By using this library, we can locate which entries in the dataframe might be corrupt. This library is capable of marking the index of the row of a potential corrupt data entry. After entries are found we can check the rows by hand and see how to clean the data. The main function ```run()```
of the main class ```GeocodeValidator(filePath)``` returns the percentage of potential corrupt entries. From this percentage we can infer if a huge number of entries are corrupt then the overall dataset needs to be cleaned.

### Dependencies

* Numpy
* Pandas
* Geopandas (requires GDAL and Fiona)
* Pycountry

### Installation
```
pip install IaaGeoDataCleaning

```
### Quick Start
This a quick start guide for using this library.

1. import the library

```python
import IaaGeoDataCleaning as ij
```

2. call the main function

```python
filePath = 'path to csv or xlsx'
validator = ij.GeocodeValidator(filePath)
ij.run()
```

### Example Output

``` python
Flagged locations are at indicies: [2, 3, 4, 7, 9, 10, 12, 13, 14, 15]
0.6249999999960938
```

### Acknowledgment:

Initial development by  [Jonathan Scott ](https://github.com/lionely/).

Continued development by [Samantha Fritsche ](https://github.com/Sammy-F) and [Thy Nguyen ](https://github.com/thytng).

### Contributing

Feel free to submit a pull request if you have any features/improvements to add to the package. \
You can also open an issue if you ecountered a problem while using the current core functionalities \
of the package.
