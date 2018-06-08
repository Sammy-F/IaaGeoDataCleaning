#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thur May 31 00:11:58 2018

@author: NewType
"""

from setuptools import setup
long_description = 'Detects potentially corrupt lat/lng data.'
setup(name='IaaGeoDataCleaning',
      version='0.1.4',
      description='Detects potential corrupt entries in a dataframe.',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      url='https://github.com/getiria-onsongo/IaaGeoDataCleaning',
      author='Getiria Onsongo',
      author_email='gonsongo@macalester.edu',
      license='BSD',
      packages=['IaaGeoDataCleaning'],
      install_requires=['numpy', 'pandas', 'geocoder'],
      zip_safe=False)
