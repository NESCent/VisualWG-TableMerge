Spreadsheet merging script for Evolution of the Vertebrate Visual System working group. 

The scripts here are "as is", mostly for preservation purposes. 
In this state, they are not intended as a product for use by others.    


Config
-----

Create file src/visualwg/settings.py with contents like these: 
----begin----
DB_CONN_STRING = "host=YOURHOST dbname=YOURDB user=YOURUSER password=YOURPASS"
WORK_DIR = "/PATH/TO/WORKDIR"
----end-----

Since settings.py contains passwords, it is under .gitignore

DB_CONN_STRING is assumed to point to a PostgreSQL database.  
Database YOURDB should exist, but can be empty (it will be wiped out anyway).  
WORK_DIR contains source data and will accept the results. 


Dev setup
---------

The scripts were developed under Eclipse PyDev, but .project and .pydevproject files are not in SCM. 


Running 
-------

In Eclipse, use 'Run as > Python Run'.  