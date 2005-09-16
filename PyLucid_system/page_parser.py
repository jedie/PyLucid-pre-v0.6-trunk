#!/usr/bin/python
# -*- coding: UTF-8 -*-

# by jensdiemer.de (steht unter GPL-License)

"""
Der Parser füllt eine CMS Seite mit leben ;)
Parsed die lucid-Tags/Funktionen, führt diese aus und fügt das Ergebnis in die Seite ein.
"""

__version__="0.0.1"

__history__="""
v0.0.1
    - Erste Version: Komplett neugeschrieben. Nachfolge vom pagerender.py
"""

import sys, cgi, re, time

class parser:
    """
    Der Parser füllt alle bekannten lucid-Tags (lucidTag & lucidFunction) aus.
    """
    def __init__( self, PyLucid ):
        self.page_msg       = PyLucid["page_msg"]

        # self.module_manager --> Wird in der index.py setup_parser() hierhin "übertragen"

        self.tag_data = {} # "Statische" Tags-Daten

        # Tags die nicht bearbeitet werden:
        self.ignore_tag = ("page_msg","script_duration")

    def parse( self, content ):
        """
        Die Hauptfunktion.
        per re.sub() werden die Tags ersetzt
        """
        #~ start_time = time.time()
        content = re.sub( "<lucidTag:(.*?)/?>", self.handle_tag, content )
        #~ self.page_msg( "Zeit (re.sub-lucidTag) :", time.time()-start_time )

        #~ start_time = time.time()
        content = re.sub( "<lucidFunction:(.*?)>(.*?)</lucidFunction>", self.handle_function, content )
        #~ self.page_msg( "Zeit (re.sub-lucidFunction) :", time.time()-start_time )

        return content

    def handle_tag( self, matchobj ):
        """
        Abarbeiten eines <lucidTag:... />
        """
        tag = matchobj.group(1)
        if tag in self.ignore_tag:
            # Soll ignoriert werden. Bsp.: script_duration, welches wirklich am ende
            # erst "ausgefüllt" wird ;)
            return matchobj.group(0)

        if self.tag_data.has_key( tag ):
            # Als "Statische" Information vorhanden
            return self.tag_data[tag]

        try:
            return self.module_manager.run_tag( tag )
        except KeyError:
            # Kein Modul für das Tag vorhanden
            self.page_msg( "Unknown Tag: %s" % tag )
            pass

        return matchobj.group(0)

    def handle_function( self, matchobj ):
        function_name = matchobj.group(1)
        function_info = matchobj.group(2)

        return self.module_manager.run_function( function_name, function_info )



class render:
    """
    Parsed die Seite und wendes das Markup an.
    """
    def __init__( self, PyLucid ):
        self.PyLucid    = PyLucid
        self.page_msg   = PyLucid["page_msg"]
        self.CGIdata    = PyLucid["CGIdata"]
        self.config     = PyLucid["config"]
        self.session    = PyLucid["session"]
        self.parser     = PyLucid["parser"]
        self.tools      = PyLucid["tools"]
        self.db         = PyLucid["db"]

    def render( self, side_data ):
        try:
            CSS_content = "<style>%s</style>" % self.db.side_style_by_id( self.CGIdata["page_id"] )
        except IndexError:
            self.page_msg( "Style (ID:%s) not found!" )
            CSS_content = ""

        self.parser.tag_data["page_style_link"]     = CSS_content
        self.parser.tag_data["page_name"]           = cgi.escape( side_data["name"] )
        self.parser.tag_data["page_title"]          = cgi.escape( side_data["title"] )
        self.parser.tag_data["page_last_modified"]  = self.tools.convert_date_from_sql(
            side_data["lastupdatetime"], format = "preferences"
        )
        self.parser.tag_data["page_datetime"]       = self.tools.convert_date_from_sql(
            side_data["lastupdatetime"], format = "DCTERMS.W3CDTF"
        )
        self.parser.tag_data["page_keywords"]       = side_data["keywords"]
        self.parser.tag_data["page_description"]    = side_data["description"]

        if self.CGIdata.has_key("command"):
            # Ein Kommando soll ausgeführt werden -> Interne Seite
            self.parser.tag_data["robots"] = self.config.system.robots_tag["internal_pages"]
        else:
            self.parser.tag_data["robots"] = self.config.system.robots_tag["content_pages"]

        side_content = self.parser.parse( side_data["content"] )

        markup = side_data["markup"]

        from PyLucid_system import tools
        if markup == "textile":
            try:
                "textile Markup anwenden"
                from PyLucid_system import tinyTextile
                out = tools.out_buffer()
                #~ tinyTextile.parser( sys.stdout ).parse( txt )
                tinyTextile.parser( out ).parse( side_content )
                side_content = out.get()
            except Exception, e:
                self.page_msg( "Can't use textile-Markup (%s)" % e )
        elif markup == "none":
            pass
        else:
            self.page_msg( "Markup '%s' not supported yet :(" % markup )

        return side_content

    def apply_template( self, side_content, template ):
        """
        Alle Taps im Template ausfüllen und dabei die Seite in Template einbauen
        """
        self.parser.tag_data["page_body"]    = side_content

        side_content = self.parser.parse( template )

        return side_content