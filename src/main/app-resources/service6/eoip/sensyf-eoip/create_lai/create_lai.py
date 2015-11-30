#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,shutil,struct
from osgeo import gdal
#from kd_lai.kd_lai import KD_Lai


class LAI:
    
    def __init__(self):
        self.control=0
        self.model = ""
        
    
    # A function to create the output image
    def createOutputImage(self, outFilename, inDataset):
        # Define the image driver to be used 
        # This defines the output file format (e.g., GeoTiff)
        driver = gdal.GetDriverByName( "GTiff" )
        # Check that this driver can create a new file.
        metadata = driver.GetMetadata()
        if metadata.has_key(gdal.DCAP_CREATE) and metadata[gdal.DCAP_CREATE] == 'YES':
            print 'Driver GTiff supports Create() method.'
        else:
            print 'Driver GTIFF does not support Create()'
            sys.exit(-1)
        # Get the spatial information from the input file
        geoTransform = inDataset.GetGeoTransform()
        geoProjection = inDataset.GetProjection()
        # Create an output file of the same size as the inputted 
        # image, but with only 1 output image band.
        newDataset = driver.Create(outFilename, inDataset.RasterXSize, \
        inDataset.RasterYSize, 1, gdal.GDT_Float32)
        # Define the spatial information for the new image.
        newDataset.SetGeoTransform(geoTransform)
        newDataset.SetProjection(geoProjection)
        return newDataset
    
    
    def getLaiTuple(self, ndvi_tuple, sowing_days, kdObj, basePath):
        #  create the arff query file
        query_file = open(basePath+'/query.arff', 'w')
        query_file.write('@relation query \n')
        query_file.write('@attribute ndvi numeric\n')
        query_file.write('@attribute sowing_days numeric\n')
        query_file.write('@attribute lai numeric\n')
        query_file.write('@data\n')
        
        for i in range(len(ndvi_tuple)):
            ndvi_value = ndvi_tuple[i]
            query_file.write(str(ndvi_value)+','+str(sowing_days)+',0.0\n')
        
        query_file.close()
        
        kdObj.predict('query.arff', 'weka.classifiers.trees.M5P', self.model, 'out.stats', basePath)
        
        stats_file = open(basePath+'/out.stats', 'r')
        lai_tuple = ()
        
        for line in stats_file:
            #print line
            line_s = line.split()
            if len(line_s) == 4 and "#" not in line:
                lai_value = line_s[2]
                lai_tuple = lai_tuple + (float(lai_value),)
        
        return lai_tuple
        
        
    
    def calcLAI(self,dir, out, kdObj, basePath):
        
        for root, _, files in os.walk(dir):
          for f in files: # loop all tif's found 
            if '.tif' == os.path.splitext(f)[1]: # only tif files
                # Open the inputted dataset
                dataset = gdal.Open( dir+"/"+f, gdal.GA_ReadOnly )
                # Check the dataset was successfully opened
                if dataset is None:
                    print "The dataset could not opened"
                    sys.exit(-1)
            
                # create the lai output file
                laiFile = os.path.splitext(f)[0]+".tif"
            
                # Create the output dataset
                outDataset = self.createOutputImage(out+'/'+laiFile, dataset)
                # Check the datasets was successfully created.
                if outDataset is None:
                    print 'Could not create output image'
                    sys.exit(-1)
            
                # Get the NDVI band
                ndvi_band = dataset.GetRasterBand(1) # RED BAND. THIS IS TBD ACCORDING WITH DATASETS! To finetune in the future
                # Retrieve the number of lines within the image
                numLines = ndvi_band.YSize
                # Loop through each line in turn.
                num_lines = len(range(numLines))
                counter_lines = 1
                for line in range(numLines):
                    print "processing line "+str(counter_lines)
                    # Define variable for output line.
                    outputLine = ''
                    # Read in data for the current line from the 
                    # image band representing the red wavelength
                    ndvi_scanline = ndvi_band.ReadRaster( 0, line, ndvi_band.XSize, 1, \
                        ndvi_band.XSize, 1, gdal.GDT_Float32 )
                    # Unpack the line of data to be read as floating point data
                    ndvi_tuple = struct.unpack('f' * ndvi_band.XSize, ndvi_scanline)
            
                    # Calculate the sowing days
            
                    lai_tuple = self.getLaiTuple(ndvi_tuple, 100, kdObj, basePath)
                    
                    #print ndvi_tuple
                    #print lai_tuple

                    #outputLine = outputLine + struct.pack('f', lai_tuple)
                    # Write the completed line to the output image
                    #outDataset.GetRasterBand(1).WriteRaster(0, line, ndvi_band.XSize, 1,outputLine, buf_xsize=ndvi_band.XSize,buf_ysize=1, buf_type=gdal.GDT_Float32)
                    
            
                    # Loop through the columns within the image
                    for i in range(len(lai_tuple)):
                        #Calculate the NDVI for the current pixel.
                        lai_value = lai_tuple[i]
                        
                        #lai_value = 2 # TEMP !!
                        # create the query arff
                        #lai_value = self.getLaiTuple(ndvi_tuple, 72, kdObj)
                        
                        
                        # Add the current pixel to the output line
                        outputLine = outputLine + struct.pack('f', lai_value)
                        # Write the completed line to the output image
                        outDataset.GetRasterBand(1).WriteRaster(0, line, ndvi_band.XSize, 1,outputLine, buf_xsize=ndvi_band.XSize,buf_ysize=1, buf_type=gdal.GDT_Float32)
                    # Delete the output line following write
                    del outputLine
                    counter_lines += 1
                print 'LAI done'

    def create(self,conf, kdObj, basePath):
        dir = basePath+"/"+conf["input_folder"]
        out = basePath+"/"+conf["output_folder"]
        pdir = basePath+"/"+conf["processed_folder"]
        self.model = conf["lai_model"]
        self.calcLAI(dir, out, kdObj, basePath)   
        self.cleanUp(dir, pdir)
   
        #self.getLai(0.7, 150, kdObj)
   
    def cleanUp(self, dir, pdir):
        # move processed files to processed archive directory
        for root, _, files in os.walk(dir):
          for f in files:
              os.rename(dir+'/'+f, pdir+'/'+f)
   
   
"""   

else:
   print "Create LAI v1.0"
   print "Usage: create_lai <input_dir> <output_dir> <lai_model>"
   print "<input_dir>: NDVI files"
   print "<output_dir>: LAI output files"
   print "<lai_model>: path to LAI model (JAR file)"
   
"""
