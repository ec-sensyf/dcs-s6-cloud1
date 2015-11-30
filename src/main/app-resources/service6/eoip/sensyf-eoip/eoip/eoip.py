#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,shutil,datetime

import simplejson as json 
from osgeo import gdal
from create_ndvi.create_ndvi import NDVI
from create_lai.create_lai import LAI
from kd_lai.kd_lai import KD_Lai
from convert_geotiff_asc.geotiff_asc import TIFF_ASC


# This is the main class of SenSyF-S6: Earth Observation Ingestion and Processing
class EOIP():
    
    conf = ""
    basePath = ""
    
    # Create NDVI image from joint band satellite reflectances product (band 3 (red) and 4 (infrared))
    def createNDVI(self, filePath, basePath):
        print "copy inputfile and creating NDVI file..."
        
        #inputDir = self.conf["create_ndvi"]["input_folder"]
        #os.system("cp "+filePath+" "+inputDir)
        
        ndvi = NDVI();
        ndvi.run(self.conf["create_ndvi"], filePath, basePath)
        
    # Create LAI image from NDVI and using kd_lai generated datamining model
    def createLAI(self):
        print "Creating LAI..."
        kd_lai = KD_Lai();
        
        if self.conf["create_lai"]["create_arff"] == "True":
            kd_lai.build_model(False); # False, will not re-process shape files
        
        lai = LAI();
        lai.create(self.conf["create_lai"], kd_lai, self.basePath)
        
    # Tile LAI image
    def tileLAI(self):
        print "Tiling LAI image"
        input_dir = self.conf["create_tiles"]["input_folder"]
        output_dir = self.conf["create_tiles"]["output_folder"]
        pixels = self.conf["create_tiles"]["pixels"]
        os.system("./sensyf-tile -r "+str(pixels)+" "+input_dir+' '+output_dir)
              
        
    # Create the ASC formated file to be compatible in the MOHID module. Also replace -1 with -99
    def convertTif2Asc(self, basePath):
        print "Converting TIF to ESRCI ASC file"
        conv = TIFF_ASC()
        conv.run(basePath+"/"+self.conf["convert_geotiff_asc"]["input_folder"],basePath+"/"+self.conf["convert_geotiff_asc"]["output_folder"] )
        
        
    def cropProduct(self, shapePath, filePath, dirPath):
        print "cropping the product for the parcel"
        
        # crop all the products present in the dir
        # init the crop file
        parcelId = os.path.basename(os.path.splitext(shapePath)[0])
        
        croppedFile = os.path.splitext(filePath)[0]+"_"+parcelId+"_crop.tif"
        
        filename = os.path.basename(filePath)
        

        croppedFile = dirPath+"/"+parcelId+"_20140923"+".tif"
        print croppedFile
        
        # crop the file 
        os.system('gdalwarp -t_srs EPSG:4326 -dstnodata -1 -q -cutline ' + shapePath + ' -crop_to_cutline -dstalpha -of GTiff -overwrite ' + filePath + ' ' + croppedFile)
            
        return croppedFile    
        
    # main    
    def run(self, eoip_conf, basePath, filePath, shapePath):
        with open(eoip_conf) as data_file:    
            self.conf = json.load(data_file)

        self.basePath = basePath
        
        # load the parcel shapefile
        croppedFile = self.cropProduct(shapePath, filePath, basePath)
        
        # create NDVI files
        self.createNDVI(croppedFile, basePath)
        
        # create LAI files
        self.createLAI()
        
        # tile LAI
        #self.tileLAI()
        
        # convert gtiff in asc for MOHID
        self.convertTif2Asc(basePath)
        
        # create input.urls for the MOHID job
        #self.createInputs(self.conf["convert_geotiff_asc"]["output_folder"])
        
