'''
Created on Mar 16, 2011

@author: vgapeyev
'''

from visualwg.config import conf


def test_config():
    print "Database: '%s'" % conf.db_conn_string  
    print "Working directory: '%s'" % conf.work_dir
    print "Directives: '%s'" % conf.directives_dir


if __name__ == '__main__':
    test_config()