# IaaGeoDataCleaning
Finding potential corrupt data entries using geocoding.

### Overview
This a python library for detecting potential corrupt entries in a dataframe.

By using this library, we can locate which entries in the dataframe might be corrupt. This library is capable of marking the index of the row of a potential corrupt data entry. After entries are found we can check the rows by hand and see how to clean the data. The main function ```geocodeValidation()```
returns the percentage of potential corrupt entries. From this percentage we can infer if a huge number of entries are corrupt then the overall dataset needs to be cleaned.

### Dependencies

* Google Maps Services-python
* Numpy
* Pandas

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
fileName = '/iaa/test.xlsx'
api_key = 'X'
ij.geocodeValidation(fileName,api_key,flag_distance) #Default flag distance is 12. miles
```

### Example Output

``` python
distance matrix API Status: OK

distance matrix API Status: OK

distance matrix API Status: OK

Index: 2 distance between points is too large.(Index flagged.)

distance matrix API Status: OK

Index: 4 could not be geocoded.(Index flagged.)

distance matrix API Status: OK

distance matrix API Status: OK

distance matrix API Status: OK

Index: 7 distance between points is too large.(Index flagged.)

distance matrix API Status: OK

Index: 9 could not be geocoded.(Index flagged.)

Index: 10 could not be geocoded.(Index flagged.)

distance matrix API Status: OK

Index: 12 could not be geocoded.(Index flagged.)

Index: 13 could not be geocoded.(Index flagged.)

distance matrix API Status: OK

distance matrix API Status: OK

Flagged locations are at indicies: [2, 3, 4, 7, 9, 10, 12, 13, 14, 15]
0.6249999999960938

```
