#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,shutil,struct
from osgeo import gdal

class NDVI():


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
    
    def calcNDVI(self,f, out):
        
        """
        for root, _, files in os.walk(dir):
          if files != []:
              for f in files: # loop all tif's found
                if '.tif' == os.path.splitext(f)[1]: # only tif files
                    
        """            
        # Open the inputted dataset
        dataset = gdal.Open( f, gdal.GA_ReadOnly )
        # Check the dataset was successfully opened

        if dataset is None:
            print "The dataset could not opened"
            sys.exit(-1)
    
        # create the ndvi output file
        ndviFile = os.path.basename(os.path.splitext(f)[0]+".tif")
        
        # Create the output dataset
        outDataset = self.createOutputImage(out+'/'+ndviFile, dataset)
        # Check the datasets was successfully created.
        if outDataset is None:
            print 'Could not create output image'
            sys.exit(-1)
    
        # Get hold of the RED and NIR image bands from the image
        # Note that the image bands have been hard coded
        # in this case for the Landsat sensor. RED = 3
        # and NIR = 4 this might need to be changed if
        # data from another sensor was used.
        #red_band = dataset.GetRasterBand(3) # RED BAND. THIS IS TBD ACCORDING WITH DATASETS! To finetune in the future
        #nir_band = dataset.GetRasterBand(4) # NIR BAND. THIS IS TBD ACCORDING WITH DATASETS! To finetune in the future
        #this is for Deimos-1 bands
        red_band = dataset.GetRasterBand(2) # RED BAND. THIS IS TBD ACCORDING WITH DATASETS! To finetune in the future
        nir_band = dataset.GetRasterBand(1) # NIR BAND. THIS IS TBD ACCORDING WITH DATASETS! To finetune in the future
        # Retrieve the number of lines within the image
        numLines = red_band.YSize
        # Loop through each line in turn.
        for line in range(numLines):
            # Define variable for output line.
            outputLine = ''
            # Read in data for the current line from the 
            # image band representing the red wavelength
            red_scanline = red_band.ReadRaster( 0, line, red_band.XSize, 1, \
                red_band.XSize, 1, gdal.GDT_Float32 )
            # Unpack the line of data to be read as floating point data
            red_tuple = struct.unpack('f' * red_band.XSize, red_scanline)
    
            # Read in data for the current line from the 
            # image band representing the NIR wavelength
            nir_scanline = nir_band.ReadRaster( 0, line, nir_band.XSize, 1, \
                nir_band.XSize, 1, gdal.GDT_Float32 )
            # Unpack the line of data to be read as floating point data
            nir_tuple = struct.unpack('f' * nir_band.XSize, nir_scanline)
    
            # Loop through the columns within the image
            for i in range(len(red_tuple)):
                #Calculate the NDVI for the current pixel.
                ndvi_lower = (nir_tuple[i] + red_tuple[i])
                ndvi_upper = (nir_tuple[i] - red_tuple[i])
                ndvi = 0
                #Be careful of zero divide
                if ndvi_lower == 0:
                    ndvi = 0
                else:
                    ndvi = ndvi_upper/ndvi_lower
                # Add the current pixel to the output line
                outputLine = outputLine + struct.pack('f', ndvi)
                # Write the completed line to the output image
                outDataset.GetRasterBand(1).WriteRaster(0, line, red_band.XSize, 1,outputLine, buf_xsize=red_band.XSize,buf_ysize=1, buf_type=gdal.GDT_Float32)
            # Delete the output line following write
            del outputLine
        print 'NDVI done'
        """
          else:
            print "No new files to process"
            exit(0)
        """
    
    # function to convert digital numbers in reflectances. For this, use GRASS: http://grass.osgeo.org/grass65/manuals/i.landsat.toar.html
    def convertToReflectances(self, filePath):
        print "Converting to reflectances... (TBD)"
        
        
    def run(self,conf, filePath, basePath):
        dir = basePath+"/"+conf["input_folder"]
        out = basePath+"/"+conf["output_folder"]
        pdir = basePath+"/"+conf["processed_folder"]

        print dir, out, pdir 
        
        if "LANDSAT" in filePath:
            self.convertToReflectances(filePath)
        
        self.calcNDVI(filePath, out)
        #self.cleanUp(dir, pdir)
        
    def cleanUp(self, dir, pdir):
        # move processed files to processed archive directory
        for root, _, files in os.walk(dir):
          for f in files:
              print f
              os.rename(dir+'/'+f, pdir+'/'+f)
        
    def usage(self):
        print "Create NDVI v1.0"
        print "Usage: create_ndvi <input_dir> <output_dir>"
        print "<input_dir>: S2 compatible satellite products"
        print "<output_dir>: NDVI output files"
   
