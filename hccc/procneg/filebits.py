#!/usr/local/bin/python
#
# Some useful file/directory functions.
#
# Copyright (C) 2012 Nick Glazzard
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

import os, fnmatch, stat

def all_files( root, patterns='*', single_level=False, yield_folders=False ):
    patterns = patterns.split( ';' )
    for path, subdirs, files in os.walk( root ):
        if yield_folders:
            files.extend( subdirs )
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch( name, pattern ):
                    yield os.path.join( path, name )
                    break
        if single_level:
            break

def replace_text_in_string( s, substs ):
    for in_text, out_text in substs.iteritems():
        s = s.replace( in_text, out_text )
    return s

def replace_text_in_file( in_name, out_name, substs ):
    try:
        in_file = open( in_name )
        out_file = open( out_name, 'w' )

        for s in in_file:
            s = replace_text_in_string( s, substs )
            out_file.write( s )
            
        in_file.close()
        out_file.close()
        
    except:
        print 'Error in replace_text_in_file.'

def delete_file_if_exists( path ):
    if os.access( path, os.F_OK ):
        try:
            os.remove( path )
        except:
            print 'Cannot remove %s' % path
