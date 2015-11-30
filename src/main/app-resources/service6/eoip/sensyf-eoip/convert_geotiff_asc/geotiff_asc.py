#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,shutil
from osgeo import gdal

class TIFF_ASC:
        
    def __init__(self):
        self.findreplace = [('-nan','-1')]
    
    # process each file for the replacement of nan's
    def replaceStringInFile(self,filePath):
       "replaces all findStr by repStr in file filePath"
       print filePath
       tempName=filePath+'~x~'
       backupName=filePath+'~~'
    
       inF = open(filePath,'rb')
       s=unicode(inF.read(),'utf-8')
       inF.close()
    
       for couple in self.findreplace:
           outtext=s.replace(couple[0],couple[1])
           s=outtext
       outF = open(tempName,'wb')
       outF.write(outtext.encode('utf-8'))
       outF.close()
    
       shutil.copy2(filePath,backupName)
       os.remove(filePath)
       os.rename(tempName,filePath)
    
    # replace nan values with -99 in all output asc files
    def processASCFiles(self,dir, out):
        for root, _, files in os.walk(dir):
          for f in files:
            if '.asc' == os.path.splitext(f)[1]:
              self.replaceStringInFile(root+'/'+f)
              # mv files to output folder
              os.system("mv "+root+'/'+os.path.splitext(f)[0]+".asc "+out)
              os.system("mv "+root+'/'+os.path.splitext(f)[0]+".prj "+out)
              os.system("mv "+root+'/'+os.path.splitext(f)[0]+".asc.aux.xml "+out)
            if '.tif' == os.path.splitext(f)[1]:
              # mv files to output folder
              os.system("mv "+root+'/'+os.path.splitext(f)[0]+".tif "+out)
              
    
    # transform tif files in asc
    def processTIFFiles(self,dir, out): 
        for root, _, files in os.walk(dir):
          for f in files: # loop all tif's found
            print "Processing file:" + f
            if '.tif' == os.path.splitext(f)[1]:
              print "INFO: Creating ESRI ASC file "+ os.path.splitext(f)[0] + ".asc"
            
              currentFilePath=os.path.join(root, f)
            
              # convert from 900913 to 4326 (temp files)
              #os.system("gdalwarp -s_srs EPSG:6326 -t_srs EPSG:4326 "+currentFilePath+" "+currentFilePath+"_4326")
              
              # convert from tif to asc
              os.system("gdal_translate -of AAIGrid " + currentFilePath + " " + os.path.splitext(currentFilePath)[0] + ".asc")
              
              # mv tif file 
              os.system("mv "+root+'/'+os.path.splitext(f)[0]+".tif "+out)
               
    # clean all the dirs and files in the input dir
    def cleanUp(self, dir):
        for root, _, files in os.walk(dir):
          # delete temp files
          os.system("rm -rf "+root+"/*")
              
     
    def run(self, dir, out):
        self.dir = dir
        self.out = out
        self.processTIFFiles(self.dir, self.out)
        self.processASCFiles(self.dir, self.out)
        self.cleanUp(dir)

    def usage(self):
        print "Conversion Tool: GeoTiff to ESRI ASC file v1.1"
        print "Usage: convert_geotiff_asc <input_dir> <output_dir>"
