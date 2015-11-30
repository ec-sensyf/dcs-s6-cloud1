#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,shutil
from osgeo import gdal
import argparse
from subprocess import call
from eoip.eoip import EOIP

# parse the arguments
parser = argparse.ArgumentParser(description="SENSYF - EOIP - Process EO Products for MOHID ingestion")

# add possible arguments
parser.add_argument("config_path", type=str, help="the JSON configuration file")
parser.add_argument("dir_path", type=str, help="the base working dir")
parser.add_argument("shape_path", type=str, help="the shape to use in the process")
parser.add_argument("product_path", type=str, help="where the product is")
args = parser.parse_args()

eoip = EOIP()
confPath = args.config_path
dirPath = args.dir_path
filePath = args.product_path
shapePath = args.shape_path
eoip.run(confPath, dirPath, filePath, shapePath)
