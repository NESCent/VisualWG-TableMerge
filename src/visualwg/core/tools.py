'''
Created on Mar 16, 2011

@author: vgapeyev
'''
import os, os.path, shutil
import csv, logging
import sys
import visualwg.core.dbal as dbal
from visualwg.config import conf
import schema, util




SCHEMA = schema.Schema(conf.columns_file)


    
    
def process_submissions():
    ''' Loads every CSV file under sourcedir into the DB, 
        while placing reports into individual directories under reportdir, one per each submission file.
    '''    

    applog = logging.getLogger("applog")

    applog.info("Setting up database (including the taxonomy table load)")
    db = dbal.DB(SCHEMA)  
        
    applog.info("Processing submissions from %s", conf.subm_csv_dir)
    applog.info("Submissions to process:\n  %s", "\n  ".join(conf.subm_basenames))
    
    for bname in conf.subm_basenames:
        applog.info("Processing submission %s", bname)

        logger = logging.getLogger(bname)
        submission = os.path.join(conf.subm_csv_dir, bname+".csv")
        loadable = os.path.join(conf.subm_reports_dir, bname, "loadable.csv")
        subm_header = util.get_csv_header(submission)
       
        if SCHEMA.check_headers(subm_header, logger):
            SCHEMA.clean_for_loading(bname, submission, loadable, logger)
            db.load_loadable(bname)
            applog.info("Accepted %s for merging into the database.", bname)
        else: 
            applog.info("Could not accept %s for further processing.", bname)
        applog.info("\n\n")
        
    #++    
    db.create_names_views()
    db.decide_actions()
    db.load_actions_table()
    for bname in conf.subm_basenames:
        db.report_taxa(bname)
    db.create_master_raw()
    db.download_master_raw()
    
    db.create_rowstatuscounts_views()
    db.create_data_density_views()
    
    db.populate_master_summarized()
    
    del db   #this only deletes the object and releases the connection
    applog.info("FINISHED ALL WORK")
    

##--
#def temp_create_loadable(bname):    
#    logger = logging.getLogger(bname)
#    submission = os.path.join(conf.subm_csv_dir, bname+".csv")
#    loadable = os.path.join(conf.subm_reports_dir, bname, "loadable.csv")
#    subm_header = util.get_csv_header(submission)
#   
#    #--
#    print "This is temporary: output from SCHEMA.check_headers"
#    SCHEMA.check_headers(subm_header, logger)
#    print "END output from SCHEMA.check_headers"
#    
#    #SCHEMA.check_headers(subm_header, logger)
#    #SCHEMA.clean_for_loading(submission, loadable, logger)
#
#
##-- This is a "prefix of process_submissions(), for debugging     
#def temp_process_submissions():
#    applog = logging.getLogger("applog")
#
#    applog.info("Setting up database, incl loading the taxonomy resolution table.")
#    #++
#    #db = dbal.DB(SCHEMA)  
#        
#    applog.info("Processing submissions from %s", conf.subm_csv_dir)
#    applog.info("Submissions to process:\n  %s", "\n  ".join(conf.subm_basenames))
#    
#    for bname in conf.subm_basenames:
#        applog.info("Processing submission %s", bname)
#        temp_create_loadable(bname)
#    #++
#    #    db.load_loadable(bname)
#    #    applog.info("Finished loading %s into the database", bname)
        

if __name__ == '__main__':
    #--
    #temp_process_submissions()
    #++
    process_submissions()