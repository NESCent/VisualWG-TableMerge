'''
Created on Jun 13, 2011

@author: vgapeyev
'''
import csv
import codecs


def get_csv_header(fname):
    ''' Returns the 1st (presumed header) line of a CSV file, as a string list. 
    '''
    csv_file = open(fname, "U")
    csv_reader = csv.reader(csv_file)
    header = csv_reader.next()
    csv_file.close()
    return header


def csv2tabbed(csvfile, tabfile):
    csv_open = codecs.open(csvfile, "rU", 'ascii', 'ignore') #char encoding trouble...
    csv_reader = csv.reader(csv_open, "excel")
    tab_open = codecs.open(tabfile, "w", 'utf-8')
    tab_writer = csv.writer(tab_open, "excel-tab")
    for line in csv_reader:
        tab_writer.writerow(line)
    csv_open.close()
    tab_open.close()


def merge_dicts(dictlist):
    return dict(sum([d.items() for d in dictlist], []))

def colnames_to_sql_cols_ref(colnames):
    ''' From a list of strings (presumably column names of a table) creates a string 
        with the names quoted and comma-separated, 
        suitable as a list of column references in an SQL query.   
    '''
    col_refs = ['"%s"' % c for c in colnames]
    cols_ref = ", ".join(col_refs)
    return cols_ref 
