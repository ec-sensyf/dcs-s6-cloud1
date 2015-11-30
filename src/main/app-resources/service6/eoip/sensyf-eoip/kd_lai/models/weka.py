#!/usr/bin/python

import os, sys
import types

class Weka:
    
    def __init__(self):
        self.control = 0
    
    def usage(self):
        print "-- WEKA EOIP tool v1.0 --"
        print "Options:"
        print "1.Make Prediction: weka -p <in:query_arff> <in:model_name> <in:model_input> <out:prediction_file>"
        print "2.Create model: weka -m <in:model_type> <in:input_arff> <in:cross_val_folders> <out:model_output>"
        
    def available_models(self):
        print "-- WEKA EOIP tool v1.0 --"
        print "Available models:"
        print "1. weka.classifiers.meta.Bagging"


    def build_model(self,model_type, input_arff, model_output, cross_val_folders):
        if model_type == "weka.classifiers.meta.Bagging":
            print "INFO: Building model..."
            os.popen('java '+model_type+' -t '+input_arff+' -d '+model_output+' -o -x '+cross_val_folders+' -P 100 -S 1 -I 10 -W weka.classifiers.trees.REPTree -- -M 2 -V 0.001 -N 3 -S 1 -L -1 > model.stats')
        else:
            print "WARN: Unrecognizable model"
            self.available_models()

    def predict(self,query_arff, model_name, model_file, output_file, basePath):
        # execute java command
        os.popen('java -classpath '+basePath+'/weka/weka.jar '+model_name+' -T '+basePath+"/"+query_arff+' -l '+basePath+"/"+model_file+' -p 0 > '+basePath+"/"+output_file);

"""
numVars = len(sys.argv)

if numVars >= 6:
    
    if(numVars == 6 and sys.argv[1] == '-p'):
        # Make Prediction (e.g. ./weka.py -p ndvi_lai_wout_latlon_test.arff weka.classifiers.meta.Bagging bagging_withoutLatLon/Bagging.model out)
        print "INFO: Predicting..."
        query_arff = sys.argv[2]
        model_name = sys.argv[3]
        model_file = sys.argv[4]
        output_file = sys.argv[5]
        
        # execute java command
        os.popen('java '+model_name+' -T '+query_arff+' -l '+model_file+' -p 0 > '+output_file);
        
    elif(numVars == 6 and sys.argv[1] == '-m'):
        # Create Model (e.g: java weka.classifiers.meta.Bagging -t ndvi_lai_wout_latlon.arff -d output.model -P 100 -S 1 -I 10 -W weka.classifiers.trees.REPTree -- -M 2 -V 0.001 -N 3 -S 1 -L -1)
        model_type = sys.argv[2]
        input_arff = sys.argv[3]
        cross_val_folders = sys.argv[4]
        model_output = sys.argv[5]
        
        if model_type == "weka.classifiers.meta.Bagging":
            print "INFO: Building model..."
            os.popen('java '+model_type+' -t '+input_arff+' -d '+model_output+' -o -x '+cross_val_folders+' -P 100 -S 1 -I 10 -W weka.classifiers.trees.REPTree -- -M 2 -V 0.001 -N 3 -S 1 -L -1 > model.stats')
        else:
            print "WARN: Unrecognizable model"
            available_models() 
    else:
        usage()
    
else:
    usage()
"""

