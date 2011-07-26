'''
Created on Apr 14, 2011

@author: vgapeyev
'''

import os.path, shutil, logging, sys


class Conf(object):
    # These are config defaults, they are likely to be overwritten     
    work_dir = "UNDEFINED-WORK-DIR"
    db_conn_string = "UNDEFINED-DB-CONN-STRING"

    directives_dir = "UNDEFINED-directives-dir"
    subm_csv_dir = "UNDEFINED-subm-csv-dir"
    subm_reports_dir = "UNDEFINED-subm-reports-dir"
    results_dir = "UNDEFINED-results-dir"
    
    taxa_resolver_file = "UNDEFINED-taxa-resolver-file"
    columns_file = "UNDEFINED-columns-file"
    
    subm_basenames = ["UNDEFINED-subm-basenames"]
    
    
def reset_dir(dir):
    '''Make sure dir is present and is empty.'''
    shutil.rmtree(dir, True)  # 'True' ignores errors, e.g. when the dir is not there
    os.makedirs(dir)
    
    
def set_up_reporting(conf):
    ''' Set up reporting and logging.
        Creates one logger per submission, named as the submission's base name. 
        Also creates "applog" for application-level messages.
    '''
    # Reset the report and result directories
    reset_dir(conf.subm_reports_dir)
    reset_dir(conf.results_dir)
    
    
    
    # The root logger:
    logging.basicConfig(
                        #filename = os.path.os.path.join(reportdir, "visualwg.log"), 
                        level = logging.INFO,
                        stream = sys.stderr
                        )
    applog = logging.getLogger("applog")
    applog.setLevel(logging.INFO)
    for bname in conf.subm_basenames:
        subm_report = os.path.join(conf.subm_reports_dir, bname) 
        os.mkdir(subm_report)         
        subm_log = logging.getLogger(bname)
        subm_log.setLevel(logging.INFO)
        subm_log.addHandler(logging.FileHandler(os.path.join(subm_report, "issues.log")))
    
    

def obtain_conf():
    '''
    Eventually, this will read a textual config file and/or command line. 
    For now, we hard-wire the config values in settings.py 
    '''
    conf = Conf()
    
    from visualwg import settings  #TODO: read config values from a config file instead
                                   #TODO: also, find a way to keep the config file outside the source tree, to reduce dange of committing passwords to source control 
   
    conf.work_dir = settings.WORK_DIR
    conf.db_conn_string = settings.DB_CONN_STRING
    
    #TODO: rename Python vars to better match directory names in the file system
    conf.directives_dir = os.path.join(conf.work_dir, "directives-used")
    conf.subm_csv_dir = os.path.join(conf.work_dir, "data-used")
    conf.subm_reports_dir = os.path.join(conf.work_dir, "reports")
    conf.results_dir = os.path.join(conf.work_dir, "results")
    
    conf.taxa_resolver_file = os.path.join(conf.directives_dir, "taxa-resolver.tab")
    conf.taxacorr_dir = os.path.join(conf.work_dir, "taxa_corrections")
    
    conf.columns_file = os.path.join(conf.directives_dir, "columns.csv")
    #TODO: split columns_file into sys_columns and user_columns

    conf.subm_basenames = [f.split(".csv")[0]  for f in os.listdir(conf.subm_csv_dir) if f.endswith('.csv')]

    set_up_reporting(conf)
    
    return conf
