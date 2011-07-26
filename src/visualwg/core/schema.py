'''
Created on Jun 13, 2011

@author: vgapeyev
'''
import csv

class Schema(object):
    '''
    Schema for the structure of submission spreadsheets.  
    Describes what columns are expected and provides schema-driven methods 
    to verify and manipulate the submission spreadsheets. 
    '''

    def __init__(self, header_spec_file):
        '''
        Initializes from a CSV file where  each row describes a column of a submission spreadsheet. 
        '''
        specfile = open(header_spec_file, "U")
        csv_reader = csv.DictReader(specfile)   #["Column", "Category", "Type", "Summarizer"] are expected in the header row
        #TODO: check that the headers being read are the ones expected 
    
        #TODO: move category names into a list constant 
        headers_dict = {
                    "bookkeeping" : [],   # where list contains Column names; ditto for others
                    "pub-taxonomy" : [],
                    "taxonomy" : [], 
                    "info" : [], 
                    "trait" : [],  
                    "provenance" : [], 
                      }
        traits = [] # of tuples: (Column/Trait name, Type, Summarizer)
        for d in csv_reader:
            column = d["Column"].strip()
            category = d["Category"].strip()
            headers_dict[category].append(column)
            if  category == "trait":
                traits.append((column, d["Type"].strip(), d["Summarizer"].strip()))
        specfile.close()
    
        header_groups = [
                ("bookkeeping", headers_dict["bookkeeping"]), 
                ("taxonomy", headers_dict["taxonomy"]), 
                ("pub-taxonomy", headers_dict["pub-taxonomy"]), 
                ("info", headers_dict["info"]),
                ("trait", headers_dict["trait"]), 
                ("provenance", headers_dict["provenance"]), 
                      ]
        self.HEADER_GROUPS = header_groups
        self.TRAITS = traits
        
        self.new_init(header_spec_file)
        
        
    def new_init(self, header_spec_file):
        ''' This will gather new code, and may eventually replace __init__() itself
        '''
        specfile = open(header_spec_file, "U")
        csv_reader = csv.DictReader(specfile)   
        #TODO: check that headers in the spec file itself are expected ones: "Column", "Category", "Type", "Unit", "Summarizer", "In submission", "In merge", "In summary". 
        
        self.IN_SUBMISSION = {} 
        self.LOAD_HEADERS = []
#??        self.TRAIT_HEADERS = []
        for d in csv_reader:
            column = d["Column"].strip()
            #TODO: check that the just-read column name is not a duplicate of an earlier one
            category = d["Category"].strip()  #TODO: check that the value is among expected ones
            in_submission = d["In submission"]  #TODO: check that the value is expectable: no, required, or opt
            self.IN_SUBMISSION[column] = in_submission  
            if category != "taxonomy":  #TODO: control the construction of LOAD_HEADERS more robustly, directly from columns.csv 
                self.LOAD_HEADERS.append(column)
#??            if category == "trait":
#??                self.TRAIT_HEADERS.append(column)
        #--
        #--print "self.LOAD_HEADERS = %s" %  self.LOAD_HEADERS
        
        
    def check_headers(self, subm_headers, subm_logger = None):
        '''
        Accepts source_headers as the headers from the file to be sanitized and 
        checks them against the "In submission" directive in the column directives file. 
        Logs warning messages into the supplied subm_logger.  
        Returns True in the absence of errors that should stop further processing.  
        '''
        check_passed = True
        #Normalize the headers present in the submission
        #TODO: consider dropping punctuation
        present = set([h.strip().lower() for h in subm_headers])
        
        #Relevant sets of the schema headers: 
        everything = set([sh.lower() for (sh, _) in self.IN_SUBMISSION.items()])
        required =   set([sh.lower() for (sh, sv) in self.IN_SUBMISSION.items() if sv == "required"])
        prohibited = set([sh.lower() for (sh, sv) in self.IN_SUBMISSION.items() if sv == "no"])
        
        # Every required header must be present in the submission
        required_missing = required - present
        #-- 
        #--print  "required_missing = %s" % required_missing
        if len(required_missing) > 0:
            rm_list = "  " + "\n  ".join(required_missing)
            subm_logger.error("These headers are required, but were not found:\n%s\nLoading of this spreadsheet cannot succeed. Terminating.", 
                              rm_list)
            check_passed = False
        
        
        # Every prohibited header must be absent in the submission
        prohibited_present = prohibited & present
        #-- 
        #--print "prohibited_present = %s" % prohibited_present
        if len(prohibited_present) > 0:
            pp_list = "  " + "\n  ".join(prohibited_present)
            subm_logger.warning("These headers are reserved and should not be used:\n%s\nThe corresponding columns will be ignored.", 
                              pp_list)
        
        # Warning about submission headers that were not recognized
        present_unrecognized = present - everything 
        #--print "present_unrecognized = %s" % present_unrecognized 
        if len(present_unrecognized) > 0:
            pu_list = "  " + "\n  ".join(present_unrecognized)
            subm_logger.warning("These headers were not recognized:\n%s\nThe corresponding columns will be ignored.", 
                              pu_list)
        return check_passed

    def row_has_trait_data(self, dict):
        ''' Expects that dict has entries for all traits in TRAIT.
        '''
        count_data = 0
        for (trait, _, _) in self.TRAITS:
            if dict[trait]:
                count_data =+ 1
        return (count_data > 0)

        
    def  clean_for_loading(self, submission_name, submission, cleaned, logger):
        ''' Transforms a submission spreadsheet into the spreadsheet that will be directly loaded into DB.
            - Expects column headers have already been checked (with check_headers). 
            - Augments with columns holding submission title and original row number. 
            - Normalizes spelling of column names
            - Ignores rows with missing pub-genus, pub-species values. 
            - Ignores rows with no trait data. 
            - Normalizes case of values in taxa columns
        '''
        subm_file = open(submission, "U")
        subm_reader = csv.DictReader(subm_file)

        clean_file = open(cleaned, "w")
        clean_writer = csv.DictWriter(clean_file, self.LOAD_HEADERS)
        clean_header = dict([(h, h) for h in self.LOAD_HEADERS])
        clean_writer.writerow(clean_header) 
    
        nodata_rows = [] 
        #TODO: allow for extra punctuation in the incoming header names  
        #TODO: more generally, factor out a name normalization function to use in name comparisons
        for (si, sdict) in enumerate(subm_reader):
            s_linenum = si+2    #+1 for the header; +1 for 0- vs 1-indexing
            sdict = dict([ (key.strip().lower(), val) for (key, val) in sdict.items() ])
            cdict = dict.fromkeys(self.LOAD_HEADERS, "")
            #Transfer data from source to target:
            for ckey in cdict.keys():
                try:
                    sval = sdict[ckey.lower()]
                    cdict[ckey] = sval.strip()  #TODO: a place to check conformance to columns.csv!Type ?
                except KeyError:
                    pass
            #Only accept rows that have pub_genus and pub_species
            #TODO: eliminate hardwiring of "Pub. Genus" and "Pub. Species" -- use InSubmission=required from CSV schema
            if cdict["Pub. Genus"] == "" or cdict["Pub. Species"] =="":
                logger.warn("Row %i was skipped: no value in 'Pub. Genus' or " + \
                            "no 'Pub. Species'", s_linenum)
            #Only accept rows that contain at least one column with trait data
            elif not self.row_has_trait_data(cdict):
                nodata_rows.append(s_linenum)
            else:
                #Augment with bookkeeping fields:
                cdict["Submission"] = submission_name
                cdict["Linenum"] = s_linenum
                # Normalize the case of taxa names 
                for tx in ["Pub. Class", "Pub. Order", "Pub. Family", "Pub. Genus"]:
                    cdict[tx] = cdict[tx].capitalize()
                for tx in ["Pub. Species", "Pub. Subspecies"]:
                    cdict[tx] = cdict[tx].lower()
                #Emit the row 
                clean_writer.writerow(cdict)
        if len(nodata_rows) > 0:
            #TODO (pretty) condense nodata_rows into intervals before printing out
            logger.warn("These rows (%i total) had no data points and were ignored: %s", len(nodata_rows), nodata_rows)
        subm_file.close()
        clean_file.close()


        