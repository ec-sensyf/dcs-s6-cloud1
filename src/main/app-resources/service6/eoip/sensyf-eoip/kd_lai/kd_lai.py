#!/usr/bin/python

import sys, os, glob, logging
from osgeo import gdal, gdalnumeric, ogr, osr
import Image, ImageDraw
import numpy as np
from lai.lai import Lai
from models.weka import Weka

# Class to create/update LAI model
class KD_Lai:
    
    def __init__(self):
        self.control = 0
        self.weka = Weka()
    
    def build_model(self, process_parcels_flag):
        lai = Lai()
                
        # Re-process the parcels. Using the parcels in 'sowing_dates'. For each shape, cut images and store arff data
        if process_parcels_flag:
            lai.processParcels() 
    
        # Creating ARFF file from generated data present in database
        lai.createARFF('ndvi_lai.arff')
        lai.disconnectDB()
        
        # Build the model for the generated data
        #model_type = 'weka.classifiers.meta.Bagging'
        #input_arff = 'ndvi_lai.arff'
        #model_output = './kd_lai/ndvi_lai.model'
        #cross_val_folders = '10'
        
        #self.weka.build_model(model_type, input_arff, model_output, cross_val_folders)
        

    def predict(self, query_arff, model_name, model_file, output_file, basePath):
        self.weka.predict(query_arff, model_name, model_file, output_file, basePath)
        

"""

if len(sys.argv) == 1:
    
    
    
    
else:
    print "Usage: run.py"
    
    """
