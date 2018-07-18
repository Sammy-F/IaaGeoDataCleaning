#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thur May 31 00:11:58 2018
Updated Wed July 18 2018

@author: NewType
"""

from setuptools import setup, find_packages
import os

cur_directory_path = os.path.abspath(os.path.dirname(__file__))
mapinfo = os.listdir(os.path.join(cur_directory_path, 'resources', 'mapinfo'))
data_dirs = []
for map in mapinfo:
      data_dirs.append(str(os.path.join(cur_directory_path, 'resources', 'mapinfo', map)))

long_description = 'Detects potentially corrupt lat/lng data.'
setup(name='IaaGeoDataCleaning',
      version='0.1.1',
      description='Detects potential corrupt entries in a dataframe.',
      long_description=long_description,
      url='https://github.com/getiria-onsongo/IaaGeoDataCleaning',
      author='Getiria Onsongo',
      author_email='gonsongo@macalester.edu',
      license='BSD',
      packages=find_packages(),
      package_data={'IaaGeoDataCleaning': data_dirs,
                    'IaaGeoDataCleaniing.CleaningUtils': data_dirs,
                    'IaaGeoDataCleaning.ConnectionUtils': data_dirs},
      install_requires=['numpy', 'pandas', 'geocoder', 'geopandas', 'fiona', 'gdal', 'psycopg2', 'geopy', 'xlrd',
                        'folium', 'country_converter', 'sridentify'],
      zip_safe=False)

