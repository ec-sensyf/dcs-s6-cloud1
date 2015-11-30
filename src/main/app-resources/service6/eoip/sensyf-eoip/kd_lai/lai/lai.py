#!/usr/bin/python

#general imports
import sys, os, glob, logging
from osgeo import gdal, gdalnumeric, ogr, osr
from datetime import datetime
import Image, ImageDraw
import numpy as np
import psycopg2
#!
# Class that reads data from LandSat datasets 
#!
class Lai:
    logging.basicConfig(filename='ndvi_lai.log', level=logging.DEBUG, format='%(asctime)s;%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    
    def getYearMonth(self, date):
        return 1,2
    
    # Get all pixel values from NDVI products that intersects with shapefile
    def processParcels(self):
        self.connectDB()
        
        logging.info('Processing input pixels...')
        
        
        # get all sowing date shapes
        self.cur.execute("SELECT parcel_id, sowing_date FROM sowing_dates");
        rows = self.cur.fetchall()                           
        
        for row in rows:
            # for each historical parcel, process data
            parcel_id = row[0] # the current parcel id
            sowing_date = str(row[1]) # the current sowing date
            print "Processing Parcel: "+parcel_id
            
            # get the polygon
            self.cur.execute("SELECT name, ST_astext(polygon) FROM glovi_polygon_geometry WHERE name = '"+parcel_id+"'");
            row_polygon = self.cur.fetchone()
            
            # for each polygon cut raster and store data
            if (row_polygon != None):
                ogr_polygon = ogr.CreateGeometryFromWkt(row_polygon[1] )
                
                # create temporary kml
                #kml = ogr_polygon.ExportToKML()
                
                # create the kml datasource
                driver = ogr.GetDriverByName('KML')
                dataSource = driver.CreateDataSource('tmp.kml')
                if dataSource is None:
                  print 'Could not create KML file'
                  sys.exit(1)
                layer = dataSource.CreateLayer('Parcel', geom_type=ogr.wkbPolygon)
                if layer is None:
                  print 'Could not create layer'
                  sys.exit(1)  
                
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetGeometry(ogr_polygon)
                
                layer.CreateFeature(feature)
                feature.Destroy()
                dataSource.Destroy()
                
                #file = open("tmp.kml", "w")
                #file.write(kml)
                #file.close()
                
                # read files and get the corresponding date file: e.g. LAI_20110705.tif. This is a fixed naming convention: TYPE_DATE
                
                for root, dirs, files in os.walk("./kd_lai/input/lai_ndvi"):
                    for file in files:
                        print "INFO:Processing file: "+file
                        file_type = file.split('_')[0];
                        file_date = file.split('_')[1];
                        
                        s_year, s_month, s_day = sowing_date.split('-')[0], sowing_date.split('-')[1], sowing_date.split('-')[2]
                        f_year, f_month, s_day = file_date.split('-')[0], file_date.split('-')[1], file_date.split('-')[2]
                        
                        # NDVI file
                        if s_year == f_year and 'NDVI' in file:
                            # if we have valid data for file year, store pixel values
                            
                            ndvi_filePath = os.path.join(root, file)
                            os.system("gdalwarp -overwrite -of GTiff -crop_to_cutline -cutline tmp.kml "+ndvi_filePath+" ./kd_lai/input/cut_ndvi/"+os.path.basename(ndvi_filePath).split('.')[0]+"_"+parcel_id+"_"+sowing_date+".tif")
                            
                        # LAI file    
                        elif s_year == f_year and 'LAI' in file:
                            # if we have valid data for file year, store pixel values
                            
                            lai_filePath = os.path.join(root, file)
                            os.system("gdalwarp -overwrite -of GTiff -crop_to_cutline -cutline tmp.kml "+lai_filePath+" ./kd_lai/input/cut_lai/"+os.path.basename(lai_filePath).split('.')[0]+"_"+parcel_id+"_"+sowing_date+".tif")
                            
                
        # read all cuted files and insert data in the database
        
        num_files = len(os.listdir("./kd_lai/input/cut_ndvi"))
        print "Processing "+str(num_files)+" cuted files:"
        
        for root, dirs, files in os.walk("./kd_lai/input/cut_ndvi"):
            
            for file in files:
                print "INFO: Processing cuted file: "+file
                file_type = file.split('_')[0];
                file_date = file.split('_')[1];
                file_parcel_id = file.split('_')[2];
                sowing_date = file.split('_')[3].split('.')[0];
                
                ndvi_filePath = os.path.join(root, file)
                lai_filePath = os.path.join(root.replace('cut_ndvi','cut_lai'), file.replace('NDVI','LAI'))
                
                # read pixels and save                        
                ds_ndvi = gdal.Open(ndvi_filePath, gdal.GA_ReadOnly)
                ds_lai = gdal.Open(lai_filePath, gdal.GA_ReadOnly)  
                
                # get general info from file
                (X, deltaX, rotation, Y, rotation, deltaY) = ds_ndvi.GetGeoTransform()
                srs_wkt = ds_ndvi.GetProjection()
                Nx = ds_ndvi.RasterXSize
                Ny = ds_ndvi.RasterYSize
                
                sourceSR = osr.SpatialReference(wkt=srs_wkt)
                targetSR = osr.SpatialReference()
                targetSR.ImportFromEPSG(4326)
                
                # reads pixels                    
                # get NDVI values
                imageArray_ndvi = ds_ndvi.GetRasterBand(1).ReadAsArray()
                imageArray_lai = ds_lai.GetRasterBand(1).ReadAsArray()
                             
                for y in xrange(0, len(imageArray_ndvi)):
                    for x in xrange(0,len(imageArray_ndvi[y])):
                        
                        # define pixel coordinate
                        newY = Y+(y*deltaY)
                        newX = X+(x*deltaX)
                        
                        #print "Processing point "+str(newX)+","+str(newY)
                        
                        point = self.convertMercatorTo4326(newX, newY, sourceSR, targetSR)
                        # transform mercator coordinates in WGS84:4326
                        
                        self.cur.execute("SELECT name, st_astext(polygon) FROM glovi_polygon_geometry WHERE ST_Intersects(polygon, ST_GeomFromText('"+point.ExportToWkt()+"',4326))");
                        
                        rows = self.cur.fetchall()                           
                        
                        for row in rows:
                            #print "Intersection found: "+point.ExportToWkt()
                            current_polygon_text = row[1]
                            value_ndvi = imageArray_ndvi[y][x] # ndvi value
                            value_lai = imageArray_lai[y][x] # lai value
                            
                            file_date_tmp = datetime.strptime(file_date, '%Y-%m-%d')
                            sowing_date_tmp = datetime.strptime(sowing_date, '%Y-%m-%d')
                            days = (file_date_tmp - sowing_date_tmp).days
                            
                            if value_ndvi != 0.0 and value_lai > value_ndvi: # valid NDVI values to store in DB
                                print "adding lai"
                                # insert in db
                                self.cur.execute("INSERT INTO arff_ndvi_lai (ndvi_value, lai_value, lat, lon, sowing_days) VALUES("+str(value_ndvi)+","+str(value_lai)+","+str(point.GetY())+","+str(point.GetX())+","+str(days)+")");
                            else:
                                print "No maize for the coordinate "+str(x)+','+str(y)
                                
                            
                            
                        self.conn.commit()
        
        
        # store filtered pixels in DB
        self.cur.execute("SELECT name, st_astext(polygon) from glovi_polygon_geometry")
        rows = self.cur.fetchall()
        for row in rows:
            current_polygon_text = row[1]
        
        self.disconnectDB()
 
    def connectDB(self):
        try:
            self.conn = psycopg2.connect("dbname='myfarm_kd' user='postgres' host='localhost' password='wwsknxek'")
            self.cur = conn.cursor()
            print "Database connection established"
        except:
            print "I am unable to connect to the database"    
        
    def disconnectDB(self):
        self.conn.commit()
        self.conn.close()
            
    def convertMercatorTo4326(self, x, y, src, trg):
        # create geometry point
        point = ogr.CreateGeometryFromWkt('POINT ('+str(x)+' '+str(y)+')')
        
        coordTrans = osr.CoordinateTransformation(src,trg)
        point.Transform(coordTrans)
        
        return point        
            
        
    def fillPixelsDates(self):
        logging.info('Processing filtered pixels...')
        # run all pixels in DB and update with sowing date and sowing delta
        
    def createARFF(self, arff_file):
        
        self.connectDB()
        
        logging.info('Building ARFF...')
        
        self.cur.execute("SELECT ndvi_value, lai_value, lat, lon, sowing_days FROM arff_ndvi_lai")
        
        rows = self.cur.fetchall()
        
        f = open(arff_file,'w') 
        f.write("")
        
        f.write("% 1. Title: Empirical LAI\n")
        f.write("% \n")
        f.write("% 2. Sources:\n")
        f.write("%      (a) Creator: Hugo Rosado\n")
        f.write("%      (c) Company: DME\n")
        f.write("%\n") 
        f.write("@RELATION lai-linha\n")
        f.write("@ATTRIBUTE ndvi  NUMERIC\n")
        f.write("@ATTRIBUTE sowing_days NUMERIC\n")
        #f.write("@ATTRIBUTE lat   NUMERIC\n")
        #f.write("@ATTRIBUTE lon   NUMERIC\n")
        f.write("@ATTRIBUTE lai  NUMERIC\n")
        f.write("\n")
        f.write("@DATA\n")
                               
                        
        for row in rows:

            i = 0
            for item in row:
                if i == 0:
                    ndvi_value = item
                elif i == 1:
                    lai_value = item
                elif i == 2:
                    lat = item
                elif i == 3:
                    lon = item
                elif i == 4:
                    sowing_days = item
                
                i+=1
            
            f.write(str(ndvi_value)+",")
            f.write(str(sowing_days)+",")
            #f.write(str(lat)+",")
            #f.write(str(lon)+",")
            f.write(str(lai_value))
            f.write("\n")
            
        f.close() # you can omit in most cases as the destructor will call if
            
        
        self.conn.commit()
        
        self.disconnectDB()

    def printInfo(self):
        print "This is the Sowing Date algorithm application"
        