#!/usr/bin/python
# -*- coding: UTF-8 -*-

# by jensdiemer.de (steht unter GPL-License)

"""
Ist f�r die Darstellung der Seiten zust�ndig
"""

__author__ = "Jens Diemer (www.jensdiemer.de)"

__version__="0.0.2"

__history__="""
v0.0.2
    - tinyTextile eingebaut
v0.0.1
    - erste Version
"""


import config


# Python-Basis Module einbinden
import os, sys, re





# Für Debug-print-Ausgaben
#~ print "Content-type: text/html\n"
#~ print "<pre>"


class pagerender:
    def __init__( self, session, CGIdata, db, auth, config ):
        self.session    = session
        self.CGIdata    = CGIdata
        self.db         = db
        self.auth       = auth
        self.config     = config

    def admin_menu( self ):
        menu  = '<p class="adminmenu">[ '
        menu += self.lucidTag_script_login()

        if self.session.has_key("page_history"):
            menu += " | "
            menu += '<a href="?command=edit_page">Edit this page</a>'

            menu += " | "
            menu += '<a href="?command=new_page">New page</a>'

        menu += " ]</p>"
        return menu


    ####################################################
    # lucid-Tags

    def replace_lucidTags( self, content, side_data ):
        #~ print "Content-type: text/html\n"
        #~ print "<pre>"
        #~ import cgi
        #~ for k,v in side_data.iteritems(): print k#,"-",cgi.escape(v)
        #~ print "</pre>"

        rules = [
            ( "<lucidTag:page_style_link/>",    self.lucidTag_page_style_link()     ),
            ( "<lucidTag:main_menu/>",          self.lucidTag_main_menu()           ),
            ( "<lucidTag:sub_menu/>",           self.lucidTag_sub_menu()            ),
            ( "<lucidTag:back_links/>",         self.lucidTag_back_links()          ),
            ( "<lucidTag:script_login/>",       self.lucidTag_script_login()        ),
            ( "<lucidTag:page_last_modified/>", side_data["lastupdatetime"]         ),
            ( "<lucidTag:page_title/>",         side_data["title"]                  ),
            ( "<lucidTag:page_keywords/>",      side_data["keywords"]               ),
            ( "<lucidTag:page_description/>",   side_data["description"]            ),
            ( "<lucidTag:powered_by/>",         __info__                            )
        ]
        for rule in rules:
            try:
                content = content.replace( rule[0], rule[1] )
            except:
                pass

        rules = [
            ( "<lucidFunction:IncludeRemote>(.*?)</lucidFunction>(?uism)", self.lucidFunction_IncludeRemote ),
        ]
        #~ print "-"*80
        #~ print content
        #~ print "-"*80
        for rule in rules:
            #~ try:
            #~ print re.findall( rule[0], content )
            content = re.sub( rule[0], rule[1], content )
            #~ except Exception, e:

                #~ pass

        return content

    def lucidTag_page_style_link( self ):
        CSS_content = self.db.side_style_by_id( self.CGIdata["page_id"] )
        return "<style>%s</style>" % CSS_content

    def lucidTag_main_menu( self ):
        "Baut das Menü auf"
        from PyLucid_modules import Menu
        MyMG = Menu.menugenerator( self.db, self.CGIdata, self.config )
        return MyMG.generate()

    def lucidTag_sub_menu( self ):
        "Baut das Untermenü zusammen"
        from PyLucid_modules.Menu import sub_menu
        MySM = sub_menu( self.db, self.CGIdata, self.config )
        return MySM.generate()

    def lucidTag_back_links( self ):
        from PyLucid_modules import BackLinks
        MyBL = BackLinks.backlinks( self.db, self.CGIdata["page_name"] )
        return MyBL.make()

    def lucidTag_ListOfNewSides( self ):
        from PyLucid_modules import ListOfNewSides
        return ListOfNewSides.start( self.db )

    def lucidTag_script_login( self ):
        if self.session.ID == False:
            return '<a href="?command=login">login</a>'
        else:
            return '<a href="?command=logout">logout [%s]</a>' % self.session["user"]


    ####################################################
    # lucid-Function

    def lucidFunction_IncludeRemote( self, matchobj ):
        """
        Unterscheidet zwischen Lokalen PyLucid-Skripten und echten URL-Abfragen
        """
        URL = matchobj.group(1)
        print URL

        def run_local_python_script( URL ):
            #~ return os.environ["SCRIPT_NAME"]
            try:
                scriptname = os.path.split( URL )[1]
                scriptname = os.path.splitext( scriptname )[0]
                return __import__( scriptname ).start( self.db )
            except Exception, e:
                return  "<p>IncludeRemote error '<pre>%s</pre><br />' \
                    error import local Python-skript '%s'<br /> \
                    error-msg.: '%s'</p>" % ( URL, scriptname , e )

        cleanURL = URL.split("?")[0] # Evtl. vorhandenen URL-Parameter abschneiden
        if cleanURL.endswith( "/BackLinks.py" ):
            return self.lucidTag_back_links()
        if cleanURL.endswith( "/Menu.py" ):
            return self.lucidTag_main_menu()
        if cleanURL.endswith( "/ListOfNewSides.py" ):
            return self.lucidTag_ListOfNewSides()

        #~ return "XXX%sXXX" % URL

        #~ if cleanURL.endswith( ".py" ):
            #~ # Ein Python-Skript ist angegeben

            #~ if URL.startswith( "http://" ):
                #~ # Ist das Skript auf dem lokalen Server?
                #~ for localdomain in config.preferences["LocalDomain"]:
                    #~ if URL.startswith( localdomain ):
                        #~ # Das Python-Skript ist lokal vorhanden
                        #~ return run_local_python_script( cleanURL )
            #~ elif URL.startswith( "/" ):
                #~ # Muß ein lokales Skript sein ;) Wird aber auch per urllib2
                #~ # "ausgeführt" weil es kein Python-Skript ist
                #~ URL = "http://" + os.environ["HTTP_HOST"] + URL
                #~ URL = "http://" + os.environ["SERVER_ADDR"] + URL

        # Kein lokales, Python-Skript -> wirklich per http hohlen
        import urllib2

        try:
            f = urllib2.urlopen( URL )
            sidecontent = f.read()
            f.close()
        except Exception, e:
            return "<p>IncludeRemote error! Can't get '%s'<br /> \
                error:'%s'</p>" % ( URL, e )

        try:
            return re.findall("<body.*?>(.*?)</body>(?uism)", sidecontent)[0]
        except:
            return sidecontent


    ####################################################
    # Render Page

    def lucidTag_page_body( self, side_data ):
        "Parsen des SeitenInhalt, der Aufgerufenen Seite"

        page_data = self.db.get_page_data_by_id( self.CGIdata["page_id"] )

        content = page_data["content"]

        content = self.parse_content( content, page_data["markup"] )

        content = self.replace_lucidTags( content, side_data )

        return content

    def parse_content( self, content, markup ):
        "Wendet das passende Markup an"

        if markup == "textile":
            try:
                return self.parse_textile_page( content )
            except Exception, e:
                return "[Can't use textile-Markup (%s)]\n%s" % ( e, content )
        elif markup == "none":
            return content
        else:
            return "[Markup '%s' not supported yet :(]\n%s" % ( markup, content )

    def parse_textile_page( self, content ):
        "textile Markup anwenden"
        import tinyTextile
        fileobj = fileobj_save()
        #~ tinyTextile.parser( sys.stdout ).parse( txt )
        tinyTextile.parser( fileobj ).parse( content )
        return fileobj.get()

        #~ from textile import textile
        #~ return textile.textile( content )



class fileobj_save:
    def __init__( self ):
        self.data = ""
    def write( self, txt ):
        self.data += txt
    def get( self ):
        return self.data












