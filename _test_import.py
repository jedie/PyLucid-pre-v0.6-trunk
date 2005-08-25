#!/usr/bin/python
# -*- coding: UTF-8 -*-

import cgitb;cgitb.enable()
import os, sys, glob, imp

print "Content-type: text/html; charset=utf-8\r\n"
print "<pre>"


class modules:
    def __init__( self ):
        filelist = self.scan()
        modulelist = self.test( filelist )
        self.print_result( modulelist )

    def get_suffixes( self ):
        suffixes = ["*"+i[0] for i in imp.get_suffixes()]
        suffixes = "[%s]" % "|".join(suffixes)
        return suffixes

    def get_files( self, path ):
        files = []
        for suffix in self.get_suffixes():
            searchstring = os.path.join( path, suffix )
            files += glob.glob(searchstring)
        return files

    def scan( self ):
        filelist = []
        pathlist = sys.path
        for path_item in pathlist:
            if not os.path.isdir( path_item ):
                continue

            for file in self.get_files( path_item ):
                file = os.path.split( file )[1]
                if file == "__init__.py":
                    continue

                filename = os.path.splitext( file )[0]

                if filename in filelist:
                    continue
                else:
                    filelist.append( filename )

        return filelist

    def test( self, filelist ):
        modulelist = []
        for filename in filelist:
            try:
                imp.find_module( filename )
            except:
                continue
            modulelist.append( filename )
        return modulelist

    def print_result( self, modulelist ):
        modulelist.sort()
        print "="*80
        for modulename in modulelist:
            print modulename
        print "="*80
        print len( modulelist )

modules()

print "-"*80
print "fertig"
