'''
Created on Mar 18, 2011
@author: vgapeyev
Database Access Layer
'''

import psycopg2 
import os.path
import csv
import codecs

from visualwg.config import conf
from visualwg.core import util
import logging

#--
#def prepare_database(conn_string, upload_headers):
#    conn = psycopg2.connect(conn_string)
#    cur = conn.cursor()
#    cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
#    conn.commit()
#    cur.close()
#    conn.close()

TABLES = {
          "authority" : ["synonym", "genus", "species", "family", "order",  "class",  "sourceid"], 
          "upload" : [],    #to be filled up by the class constructor
          }
          

class DB(object):
    def __init__(self, schema):
        self.SCHEMA = schema
        self.authorityfile = conf.taxa_resolver_file
        self.table_specs = TABLES
        self.table_specs["upload"] = self.SCHEMA.LOAD_HEADERS

        self.submtaxa_columns =   \
            sum([headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "bookkeeping"], []) + \
            sum([headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "pub-taxonomy"], [])
        
        self.conn = psycopg2.connect(conf.db_conn_string)
        self.cleanup()
        self.create_tables()
        self.setup_taxoresolver()
        self.augment_with_taxacorr()
        self.create_master_summarized_table(self.SCHEMA.TRAITS)
        #--print "Initialized DB object"
        
    def __del__(self):
        self.conn.close()
        #--print "Deleted DB object"
        
    def exec_parameterless(self, query):
        cur = self.conn.cursor()
        try:
            cur.execute(query)
        finally:
            self.conn.commit()
            cur.close()

    def force_exec_parameterless(self, query):
        '''Careful!  This eats any ProgrammingError exceptions.'''
        cur = self.conn.cursor()
        try:
            cur.execute(query)
        except psycopg2.ProgrammingError:
            pass
        finally:
            self.conn.commit()
            cur.close()
        
        
    def cleanup(self):
        '''Remove tables that might already be there'''
        self.force_exec_parameterless("drop view rowstatuscounts_overall")
        self.force_exec_parameterless("drop view rowstatuscounts_bysubm")
        self.force_exec_parameterless("drop view taxamatch")
        self.force_exec_parameterless("drop view submnames;")
        for (table, _) in self.table_specs.items():
            q = 'drop table "%s";' % table
            #--print q
            self.force_exec_parameterless(q)
        self.force_exec_parameterless("drop table taxaaction")
        self.force_exec_parameterless("drop table master_raw")
        self.force_exec_parameterless("drop table master_summarized")
        
    def create_tables(self):
        '''Create empty tables'''
        for (table, fields) in self.table_specs.items():
            self.create_table(table, fields)

    def create_table(self, table, fields):
        '''Creates a table with auto-gen id and varchar fields'''
        fields_and_types = [(f, "varchar") for f in fields] 
        self.create_table_typed(table, fields_and_types)
        
    def create_table_typed(self, table, fields_and_types):
        '''Creates a table with auto-gen id and fields of specified types'''
        field_defs =  ['"%s" %s' % (f,t) for (f, t) in fields_and_types]
        fields_def = ",\n  ".join(field_defs)
        q = 'CREATE TABLE "%s" (\n  "%s_id" serial PRIMARY KEY,\n  %s\n);' % (table, table, fields_def)
        #!! print q
        #!! print "create table %s" % table
        self.exec_parameterless(q)
        
        
    def add_tabfile_to_authority(self, tabfile):
        tabfileo = open(tabfile, "U")
        tabfileo.readline()  #eat the header line  #TODO: check it has expected entries
        cur = self.conn.cursor()
        columns_quoted = ['"%s"' % c  for c in TABLES["authority"]]  # psycopg2 should do this!
        cur.copy_from(tabfileo, "authority", sep='\t', null='', columns=columns_quoted)
        self.conn.commit()
        cur.close()
        tabfileo.close()
        
        
    def setup_taxoresolver(self):
        #TODO: rewrite using add_tabfile_to_authority()
        '''Load the resolution table and perform any necessary transformations'''
        authority_filename = self.authorityfile

        authority_file = open(authority_filename, "U")
        authority_file.readline()  #eat the header line 
        cur = self.conn.cursor()
        #eat pk=1 in the table, so that  pk == spreadsheet linenum after load: 
        cur.execute("insert into authority(sourceid) values ('foo:666');") 
        cur.execute("delete from authority where sourceid = 'foo:666'") 

        columns_quoted = ['"%s"' % c  for c in TABLES["authority"]]  # psycopg2 should do this!
        cur.copy_from(authority_file, "authority", sep='\t', null='', columns=columns_quoted)
        self.conn.commit()
        cur.close()
        authority_file.close()
        
    def augment_with_taxacorr(self):
        ''' Augments the resolution table with corrective entries. 
        '''
        applog = logging.getLogger("applog")
        if not os.path.exists(conf.taxacorr_dir):
            applog.info("No taxa correction directory found at %s", conf.taxacorr_dir)
            return
        logging.info("Start loading taxa correction files from %s ... ", conf.taxacorr_dir)
        
        auth_columns = self.table_specs["authority"]  #use the same columns as in the authority table
        wg_columns = ['WG Genus', 'WG Species', 'WG Class', 'WG Order', 'WG Family']
        pub_columns = ['Pub. Genus', 'Pub. Species', 'Pub. Subspecies']
        
        #Open the master correction file and emit its header
        corrmaster_fname = os.path.join(conf.subm_reports_dir, "wg_taxa.tab")
        corrmaster_file = open(corrmaster_fname, "w")
        corrmaster_tab = csv.DictWriter(corrmaster_file, auth_columns, "###", 'raise', 'excel-tab')
        corrmaster_header = dict([(c,c) for c in auth_columns])
        corrmaster_tab.writerow(corrmaster_header)
        
        #From eligible input rows, construct rows for the taxa correction file
        taxacorr_files = [f for f in os.listdir(conf.taxacorr_dir) if f.endswith('.csv')]
        for f in taxacorr_files:
            fbase = f.split(".")[0]
            fname = os.path.join(conf.taxacorr_dir, f)
            file = open(fname, "U")
            file_csv = csv.DictReader(file)
            for (i, din) in enumerate(file_csv):
                linenum= i+2   # +1 for eaten header; +1 for 0-index
                # clean spurious spaces
                for c in pub_columns + wg_columns: 
                    if din[c]: 
                        din[c] = din[c].strip()
                #if the row appears to be a taxon correction row
                if any([din[c] for c in wg_columns]): 
                    # Check that the row is not invalid
                    if not (all([din[c] for c in wg_columns]) and 
                            din['Pub. Genus'] and din['Pub. Species']):
                        logging.warning("In %s, row %i (%s, %s) appears to be a correction row, but required entries are missing", 
                                        f, linenum, din['Pub. Genus'], din['Pub. Species'])
                    else:  #the row has all required data
                        #Construct and emit the output row
                        dout = {
                                "synonym" : din['Pub. Genus'].capitalize() + ' ' + din['Pub. Species'].lower() + 
                                            (' ' + din['Pub. Subspecies'].lower() if din['Pub. Subspecies'] else ''), 
                                "genus"   : din['WG Genus'].capitalize(),
                                "species" : din['WG Species'].lower(), 
                                "family"  : din['WG Family'].capitalize(), 
                                "order"   : din['WG Order'].capitalize(),  
                                "class"   : din['WG Class'].capitalize(),  
                                "sourceid": 'WG:%s/%i' % (fbase, linenum)
                            }
                        corrmaster_tab.writerow(dout)
            file.close() 

        corrmaster_file.close()
                
        #Load it in the same manner as is setup_taxoresolver()
        self.add_tabfile_to_authority(corrmaster_fname)
        logging.info("... Done loading taxa correction files")

        
        
    def load_loadable(self, bname):
        csv_fname = os.path.join(conf.subm_reports_dir, bname, "loadable.csv")
        tab_fname = os.path.join(conf.subm_reports_dir, bname, "loadable.tab")       
        util.csv2tabbed(csv_fname, tab_fname)
        
        file = codecs.open(tab_fname, "rU", 'utf-8')
        file.readline()   # eat the header line
        cur = self.conn.cursor()
        
        columns_quoted = ['"%s"' % c  for c in TABLES["upload"]] 
        cur.copy_from(file, "upload", sep='\t', null='', columns=columns_quoted)
        self.conn.commit()
        cur.close()
        file.close()
        os.remove(tab_fname)

    def create_names_views(self):   
        '''Creates views in the database: 
        - "submnames" - the vertical slice of uploads, with only the bookkeeping and 'pub' names columns
        - "taxamatch" - left join between the latter and the "authority" 
        '''     
        col_refs = ['"%s"' % c for c in self.submtaxa_columns]
        cols_ref = ',\n  '.join(col_refs)
        q = 'create view %s as \n' % ("submnames",) + \
            'select upload_id,\n%s\n from %s;' % (cols_ref, "upload")
        #--print q
        self.exec_parameterless(q)
        
        # taxamatches view: match submissions against authority table
        #TODO: eliminate hard-wiring for the column names
        q = '''\
create view taxamatch as 
select d.*, r.*  
from submnames d left join authority r
     on d."Pub. Genus" || ' ' || d."Pub. Species" || COALESCE(' ' || d."Pub. Subspecies", '') = r.synonym
order by d.upload_id;'''
        #--print q
        self.exec_parameterless(q)
        
        
    def decide_actions(self):
        ''' Determines actions for the taxa (take, rename, ignore) and the data rows (ignore vs accept), 
            to be used during the later merge. 
            The actions are based on the raw matches in "taxamatch", according to the rules in taxa-matching.txt 
            Results are written into a tab-delimited file. 
        '''
        #Set up the file to write the results into
        subm_columns = ['upload_id'] + self.submtaxa_columns
        match_columns = ['authority_id'] + TABLES["authority"]
        diagnosis_columns = ["binom_match", "fam_match", "pub_auth_agreement", "taxon_action", "data_action", "auth_used"]
        taxaaction_columns = subm_columns + diagnosis_columns + match_columns
        taxaaction_header = dict([(c,c) for c in taxaaction_columns])
        taxaaction_fname = os.path.join(conf.subm_reports_dir, "taxaaction.tab")
        taxaaction_file = open(taxaaction_fname, "w")
        taxaaction_tab = csv.DictWriter(taxaaction_file, taxaaction_columns, "###", 'raise', 'excel-tab')
        taxaaction_tab.writerow(taxaaction_header)
        
        #DB query for the join with matches 
        q = 'select * from taxamatch;'
        cur = self.conn.cursor()
        cur.execute(q)

        #Go over all the grouped matches
        for (upload_id, subm_taxon, match_taxa) in self.generate_grouped_matches(cur):
            #-- print "a match %i, %s ### %s" % (upload_id, subm_taxon, match_taxa)
            # Find WG taxon decision, if available
            wg_match = None
            for m in match_taxa:
                if m["sourceid"] and m["sourceid"].split(":")[0] == "WG":
                    wg_match = m 
            
            #Determine the diagnosis 
            diagnosis = None
            if len(match_taxa) == 1 and match_taxa[0]["authority_id"] == None:
                # subm_taxon was not matched in the authority table 
                diagnosis = {"binom_match":"notfound", "fam_match":"n/a", "pub_auth_agreement":"n/a", 
                             "taxon_action":"notfound", "data_action":"ignore", "auth_used":None}                
            elif len(match_taxa) == 1:
                # subm_taxon matches exactly one entry in the authority
                mtx = match_taxa[0]
                if subm_taxon["Pub. Class"] == None and subm_taxon["Pub. Order"] == None and subm_taxon["Pub. Family"] == None:
                    # No current C-O-F naming was submitted  => write-in from authority
                    diagnosis = {"binom_match":"exact", "fam_match":"n/a", "pub_auth_agreement":"nopub", 
                                 "taxon_action":"writein", "data_action":"accept", "auth_used":mtx['authority_id']}
                elif subm_taxon["Pub. Class"] == mtx["class"] and subm_taxon["Pub. Order"] == mtx["order"] and \
                     subm_taxon["Pub. Family"] == mtx["family"] and \
                     subm_taxon["Pub. Genus"] == mtx["genus"] and subm_taxon["Pub. Species"] == mtx["species"]:
                    # Submitted current naming agrees with that in the authority
                    diagnosis = {"binom_match":"exact", "fam_match":"n/a", "pub_auth_agreement":"agree", 
                                 "taxon_action":"ok", "data_action":"accept", "auth_used":mtx['authority_id']}
                else:
                    # Submitted current naming does not agree with that in the authority => override with authority
                    diagnosis = {"binom_match":"exact", "fam_match":"n/a", "pub_auth_agreement":"disagree", 
                                 "taxon_action":"override", "data_action":"accept", "auth_used":mtx['authority_id']}
            else:
                # There is more than one match for subm_taxon in the authority
                # Try to use current Family, if submitted, for further resolution
                if subm_taxon["Pub. Family"] == None:
                    # The Family was not submitted for subm_taxon
                    diagnosis = {"binom_match":"ambig", "fam_match":"nopub", "pub_auth_agreement":"n/a", 
                         "taxon_action":"foundmany", "data_action":"ignore", "auth_used":None}   
                else:
                    match_taxa_wfamily = [mtx  for mtx in match_taxa if mtx["family"] == subm_taxon["Pub. Family"]]
                    if len(match_taxa_wfamily) == 0:
                        # Submitted family is not among those in the authority
                        diagnosis = {"binom_match":"ambig", "fam_match":"notfound", "pub_auth_agreement":"n/a", 
                                     "taxon_action":"foundmany", "data_action":"ignore", "auth_used":None}     
                    elif len(match_taxa_wfamily) == 1:
                        # The Family helped to resolve ambiguity
                        mtx = match_taxa_wfamily[0]
                        if subm_taxon["Pub. Class"] == None and subm_taxon["Pub. Order"] == None:
                            # No current C-O naming was submitted  => write-in from authority
                            diagnosis = {"binom_match":"ambig", "fam_match":"exact", "pub_auth_agreement":"nopub", 
                                         "taxon_action":"writein", "data_action":"accept", "auth_used":mtx['authority_id']}                          
                        elif subm_taxon["Pub. Class"] == mtx["class"] and subm_taxon["Pub. Order"] == mtx["order"] and \
                             subm_taxon["Pub. Genus"] == mtx["genus"] and subm_taxon["Pub. Species"] == mtx["species"]:
                            # Submitted current naming agrees with that in the authority
                            diagnosis = {"binom_match":"ambig", "fam_match":"exact", "pub_auth_agreement":"agree", 
                                         "taxon_action":"ok", "data_action":"accept", "auth_used":mtx['authority_id']}                             
                        else:
                            # Submitted current C-O naming does not agree with that in the authority => override with authority
                            diagnosis = {"binom_match":"ambig", "fam_match":"exact", "pub_auth_agreement":"disagree", 
                                         "taxon_action":"override", "data_action":"accept", "auth_used":mtx['authority_id']}
                    else:
                        # Even with Family, there are still several possibilities in the authority
                        diagnosis = {"binom_match":"ambig", "fam_match":"ambig", "pub_auth_agreement":"n/a", 
                                     "taxon_action":"foundmany", "data_action":"ignore", "auth_used":None}                                         
            assert diagnosis != None
            
            #Now, if there is an overriding WG correction, apply it to the diagnosis
            # Find WG taxon decision, if available
            wg_match = None
            for m in match_taxa:
                if m["sourceid"] and m["sourceid"].split(":")[0] == "WG":
                    wg_match = m 
            if wg_match:
                diagnosis["taxon_action"] = "wg"
                diagnosis["auth_used"] = wg_match['authority_id']
                diagnosis["data_action"] = "accept"
            
            #Write results (subm_taxon, match_taxa and dignosis) to a file 
            dummy_diagnosis = {"binom_match":"", "fam_match":"", "pub_auth_agreement":"", 
                               "taxon_action":"", "data_action":"", "auth_used":None}
            dummy_auth_taxon = dict([(colname, None) for colname in ['authority_id'] + TABLES["authority"]])
            #emit an extra row (with empty authority data) when there were multiple authority matches, but none "worked"
            if diagnosis["auth_used"] == None and len(match_taxa) > 1:
                act_row = util.merge_dicts([subm_taxon, diagnosis, dummy_auth_taxon])   
                taxaaction_tab.writerow(act_row)      
            #in every case, emit a row for each authority match that was considered, 
            #  printing the diagnosis alongside the successful match   
            for auth_taxon in match_taxa:
                if auth_taxon['authority_id'] == diagnosis["auth_used"]:
                    act_row = util.merge_dicts([subm_taxon, diagnosis, auth_taxon])
                else:
                    act_row = util.merge_dicts([subm_taxon, dummy_diagnosis, auth_taxon])
                taxaaction_tab.writerow(act_row)
            
        taxaaction_file.close()
        cur.close()
        
        

    def generate_grouped_matches(self, cur):
        '''Takes a cursor ordered by upload_id and groups all authority matches of the upload_id into a list'''
        import itertools
        subm_columns = ['upload_id'] + self.submtaxa_columns
        match_columns = ['authority_id'] + TABLES["authority"]
        
        subm_grouped = itertools.groupby(cur, lambda rec : rec[0])
        for (upload_id, group) in subm_grouped:
            subm_taxon = None 
            match_taxa = []
            for rec in group: 
                subm_taxon = dict(zip(subm_columns, rec[0 : len(subm_columns)]))  #recomputed for each rec in group with the same result - oh, well...
                match_taxon = dict(zip(match_columns, rec[len(subm_columns) : ]))
                match_taxa.append(match_taxon)
            yield(upload_id, subm_taxon, match_taxa) 
                

    def load_actions_table(self):
        #REFACT: loading a tab-delimited file as a DB table is a fairly generic functionality; 
        # to make this code generic, however, need to supply SQL types to be used for columns. 
        ''' Loads the previously created table of taxa resolution actions
            from file into a DB table. 
        '''
        taxaaction_fname = os.path.join(conf.subm_reports_dir, "taxaaction.tab")

        #Read header row and create a table based on it, with a few INT cols as appropriate 
        taxaaction_file = open(taxaaction_fname, "rU")
        cols = csv.reader(taxaaction_file, "excel-tab").next()
        taxaaction_file.close()
        colsq = ['"%s"' % c for c in cols]
        int_columns = ['"upload_id"', '"auth_used"', '"authority_id"']
        col_specs = [('%s int' % c if c in int_columns else '%s varchar' % c)  
                     for c in colsq]
        cols_spec = ",\n  ".join(col_specs)
        q = "create table taxaaction (\n%s\n);" % cols_spec
        #--print q 
        self.exec_parameterless(q)
        
        #Load the rest of the file into the table
        taxaaction_file = open(taxaaction_fname, "rU")
        taxaaction_file.readline()  #eat the header
        cur = self.conn.cursor()
        cur.copy_from(taxaaction_file, "taxaaction", sep='\t', null='', columns=colsq)
        self.conn.commit()
        cur.close()
        taxaaction_file.close()


        
    def report_taxa(self, bname):
        ''' Generates submission-specific reports about taxa resolution: 
            one file for each of: successes, warnings, failures (with one line per submission line), 
            and a file with all details for all submission lines (with multiple lines depending on the number of matches).   
        '''
        qtemplate = '''
select "Linenum", "Pub. Genus" , "Pub. Species", "Pub. Subspecies", 
       "Pub. Class", "Pub. Order", "Pub. Family",  
       "taxon_action", "data_action", 
       (case when auth_used = authority_id then '*' end) as auth_used, 
       "authority_id", "synonym", "class", "order", "family", "genus", "species", "sourceid"
from taxaaction
where "Submission" = '%(subm)s'
  and   %(filter)s 
order by "upload_id"        
'''
        filt_successes = "\"taxon_action\" in ('writein', 'ok', 'wg')"
        filt_warnings  = "\"taxon_action\" in ('override')"
        filt_problems  = "\"taxon_action\" in ('foundmany', 'notfound')"
        filt_all = "true"
        self.report_taxa_one(bname, "taxareport_successes", qtemplate, filt_successes)
        self.report_taxa_one(bname, "taxareport_warnings", qtemplate, filt_warnings)
        self.report_taxa_one(bname, "taxareport_failures", qtemplate, filt_problems)
        self.report_taxa_one(bname, "taxareport_all_details", qtemplate, filt_all)

    def report_taxa_one(self, bname, repname, qtempl, filter):
        rep_fname = os.path.join(conf.subm_reports_dir, bname, repname+".csv")
        rep_file = open(rep_fname, "w")
        rep_csv = csv.writer(rep_file)
        
        q = qtempl % {"subm" : bname, "filter" : filter}
        cur = self.conn.cursor()
        cur.execute(q)
        colnames = [ d[0] for d in cur.description ] 
        rep_csv.writerow(colnames)
        for rec in cur:
            rep_csv.writerow(rec)
        
        cur.close()
        rep_file.close()


    def create_master_raw(self):
        ''' Pulls all submitted spreadsheets into one DB table, but limited to rows whose taxon resolved successfully.
        '''
        provenance_cols_ref = util.colnames_to_sql_cols_ref([headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "provenance"][0])
        traits_cols_ref     = util.colnames_to_sql_cols_ref([headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "trait"][0])
        info_cols_ref       = util.colnames_to_sql_cols_ref([headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "info"][0])
        q = '''
with resolved_taxa as (
  select "upload_id",
         "Submission", "Linenum", "Pub. Genus" , "Pub. Species", "Pub. Subspecies", 
         "Pub. Class", "Pub. Order", "Pub. Family", 
         "authority_id", "sourceid", "class", "order", "family", "genus", "species"
  from taxaaction
  where data_action = 'accept'
)
select resolved_taxa.*,
       %(info)s,
       %(traits)s,  
       %(provenance)s 
into master_raw
from resolved_taxa join upload
  on resolved_taxa.upload_id = upload.upload_id 
        ''' % {"info" : info_cols_ref, 
               "provenance" : provenance_cols_ref, 
               "traits" : traits_cols_ref}
        #--print q
        cur = self.conn.cursor()
        cur.execute(q)
        self.conn.commit()
        cur.close()
        

    def download_master_raw(self):
        fname = os.path.join(conf.results_dir, "master_raw.csv")
        file = open(fname, "w")
        csvwriter = csv.writer(file)
        q = '''
select * from master_raw 
order by "class", "order", "family", "genus", "species"
''' 
        cur = self.conn.cursor()
        cur.execute(q)
        colnames = [ d[0] for d in cur.description ] 
        csvwriter.writerow(colnames)
        for rec in cur:
            csvwriter.writerow(rec)
        cur.close()
        file.close()
        
        
    def create_rowstatuscounts_views(self):
        # Row status counts - overall 
        q = '''
create view rowstatuscounts_overall as 
select taxon_action, data_action, count(*) as "row count"
from taxaaction
where data_action is not null
group by taxon_action, data_action
order by data_action, taxon_action        
      
        '''
        #-- print q
        cur= self.conn.cursor()
        cur.execute(q)
        self.conn.commit
        cur.close()        
        q = '''
select * from  rowstatuscounts_overall       
        ''' 
        fname = os.path.join(conf.results_dir, "rowstatuscounts_overall.csv")
        self.query2file(q, fname)

        # Row status counts - by submission 
        q = '''
create view rowstatuscounts_bysubm as 
select "Submission", taxon_action, data_action, count(*) as "row count"
from taxaaction
where data_action is not null
group by "Submission", taxon_action, data_action
order by "Submission", data_action, taxon_action      
        '''
        #-- print q
        cur= self.conn.cursor()
        cur.execute(q)
        self.conn.commit
        cur.close()        
        q = '''
select * from  rowstatuscounts_bysubm       
        ''' 
        fname = os.path.join(conf.results_dir, "rowstatuscounts_bysubm.csv")
        self.query2file(q, fname)
       
        
    def query2file(self, qstr, fname):
        file = open(fname, "w")
        csvwriter = csv.writer(file)
        cur = self.conn.cursor()
        cur.execute(qstr)
        colnames = [ d[0] for d in cur.description ] 
        csvwriter.writerow(colnames)
        for rec in cur:
            csvwriter.writerow(rec)
        cur.close()
        file.close()
         
        
    def create_data_density_views(self):
        #TODO: actually create the views in DB
        traits = [headers for (gname, headers) in self.SCHEMA.HEADER_GROUPS if gname == "trait"][0]
        traitsq = ['"%s"' % t  for t in traits] 
        points =  ['count(%s) as %s' % (t, t)  for t in traitsq ]
        points_spec = ", ".join(points)
        presence = ["(case when %s > 0 then 1 else 0 end) as %s" % (t,t) for t in traitsq ]
        presence_spec = ", ".join(presence)
        sums = ["sum(%s) as %s" % (t,t) for t in traitsq ] 
        sums_spec = ", ".join(sums)
        
        q = '''
with data_point_counts as (
  select  "class", "order", "family", "genus", "species", 
          count(*) as "rowcount", 
          %s
  from master_raw
  group by "class", "order", "family", "genus", "species"
  order by count(*) desc 
),
data_point_presence as (
  select  "class", "order", "family", "genus", "species", 
          %s
  from data_point_counts
),
trait_counts_by_class as (
  select "class", count("order" || ' '|| "family" || ' ' || "genus" || ' '|| "species") as "species count", 
          %s
  from data_point_presence
  group by "class"
)
select * 
from trait_counts_by_class        
        ''' % (points_spec, presence_spec, sums_spec)
        #--print q

        fname = os.path.join(conf.results_dir, "trait_counts_by_class.csv")
        file = open(fname, "w")
        csvwriter = csv.writer(file)
        cur = self.conn.cursor()
        cur.execute(q)
        colnames = [ d[0] for d in cur.description ] 
        csvwriter.writerow(colnames)
        for rec in cur:
            csvwriter.writerow(rec)
        cur.close()
        file.close()

    @staticmethod
    def generate_cur2dicts(cur):
        import itertools
        fieldnames = [ d[0] for d in cur.description ]
        for row in cur:
            yield dict(itertools.izip(fieldnames, row))
        

    def create_master_summarized_table(self, traits):
        taxa_ranks = ["class", "order", "family", "genus", "species"]
        taxa_fields = [(f, "varchar") for f in taxa_ranks]
        trait_fields = [(trait, "real") if type == "real" else 
                        (trait, "varchar") if type == "code" else
                        (trait, "varchar") if type == "int" else     #TODO: proper SQL type; affects the summarizer as well
                        (trait, "varchar") 
                           for (trait, type, _) in traits]
        self.create_table_typed("master_summarized", taxa_fields + trait_fields)


    def populate_master_summarized(self):
        from itertools import groupby
        # Construct the insert query
        taxa_ranks = ["class", "order", "family", "genus", "species"]
        trait_names = [trait for (trait, _, _) in self.SCHEMA.TRAITS]
        field_names = taxa_ranks + trait_names
        field_refs = ['"%s"' % f for f in field_names] 
        fields_spec = ",   ".join(field_refs)
        # value_refs = ['%%(%s)s' % f for f in field_names ]
        value_refs = ["%s" for _ in field_names ]
        values_spec = ", ".join(value_refs)
        q_out = '''
insert into master_summarized ( %s )
                       values ( %s ) ;
        ''' % (fields_spec, values_spec)
        print q_out
        cur_out = self.conn.cursor()

        # Get input data stream         
        q_in = '''
select * 
from master_raw
order by "class", "order", "family", "genus", "species"         
        '''
        cur_in = self.conn.cursor()
        cur_in.execute(q_in)
        records_in = DB.generate_cur2dicts(cur_in)
        groups_in = groupby(records_in, 
                                      lambda r : {"class":r["class"], "order":r["order"], "family":r["family"], 
                                                  "genus":r["genus"], "species":r["species"]})

        from visualwg.core.aggregators import * 
        
        aggs = AggregatorArray(self.SCHEMA.TRAITS) 
        for (taxon, datagroup) in groups_in:
            #!! print (taxon, datagroup)
            # Compute data summary for each trait
            aggs.reset()  
            for datarow in datagroup:
                #-- aggs.start_row()
                for trait in trait_names: 
                    agg = aggs[trait]
                    agg.add(datarow[trait])
                if aggs.invalidity_in_row():
                    #TODO: (1) log the problem; (2) emit a row into the problem spreadsheet
                    print "Invalid points in submission %s, row %s: %s" % (datarow['Submission'], datarow['Linenum'], aggs.get_invalid_row_part())
            #TODO: Insert a new record into cur_out  
            #!! print "Aggregate data:"
            #!! print taxon,;  print aggs.get_aggregate_row()
            summarized = util.merge_dicts([taxon, aggs.get_aggregate_row()])
            summarized_list = [ summarized[f]  for f in field_names]    #cannot use the summarized dict for "DB dict insert", 
                                                                        # since some fields contain ")" !
            cur_out.execute(q_out, summarized_list)
        
        cur_out.close()
        cur_in.close()
        self.conn.commit()

        #Download to master_summarized spreadsheet
        q_download = '''
select %s 
from master_summarized
order by "class", "order", "family", "genus", "species" 
        ''' % fields_spec
        fname_download = os.path.join(conf.results_dir, "master_summarized.csv")
        self.query2file(q_download, fname_download) 
        