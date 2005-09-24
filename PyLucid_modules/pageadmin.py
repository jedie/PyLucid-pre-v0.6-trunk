#!/usr/bin/python
# -*- coding: UTF-8 -*-

# by jensdiemer.de (steht unter GPL-License)

"""
Alles was mit dem ändern von Inhalten zu tun hat:
    -edit_page
"""

__author__ = "Jens Diemer (www.jensdiemer.de)"

__version__="0.2"

__history__="""
v0.2
    - NEU: "sequencing" - Ändern der Seiten-Reihenfolge
    - select_del_page benutzt nun CGI_dependent_actions (vereinheitlichung im Ablauf mit anderen Modulen)
v0.1.1
    - NEU: select_edit_page: Editieren einer Seite mit Select-Box in denen _alle_ Seiten angezeigt werden.
    - Bug 1275807 gefixed: "showlinks" und "permitViewPublic" werden nun richtig auf 0 gesetzt statt ""
v0.1.0
    - NEU: Das löschen von Seiten geht nun auch ;)
    - Anpassung an neuen Module-Manager
    - Beim erstellen einer neuen Seite, wird direkt zu dieser "hingesprungen"
v0.0.7
    - "must_admin" für Module-Manager definiert
    - Nutzt Zeitumwandlung aus PyLucid["tools"]
v0.0.6
    - vereinfachung in parent_tree.make_parent_option() durch MySQLdb.cursors.DictCursor
v0.0.5
    - NEU: Pseudo Klasse 'module_info' liefert Daten für den Module-Manager
v0.0.4
    - NEU: erstellen einer Seite
v0.0.3
    - NEU: encoding from DB (Daten werden in einem bestimmten Encoding aus der DB geholt)
v0.0.2
    - Fehler behoben: parend-ID wird nach einem Preview auf 'root' gesetzt
v0.0.1
    - erste Version
"""

__todo__ = """
lastupdatetime in der SQL Datenbank ändern: time-String keine gute Idee: in lucidCMS wird
das Archiv nicht mehr angezeigt :(
"""

# Python-Basis Module einbinden
import sys, cgi, time, pickle, urllib






class pageadmin:
    """
    Editieren einer CMS-Seite mit Preview und Archivierung
    """
    module_manager_data = {
        #~ "debug" : True,
        "debug" : False,

        "edit_page" : {
            "must_login"    : True,
            "must_admin"    : False,
            #~ "get_page_id"   : True,
        },
        "select_edit_page" : {
            "must_login"    : True,
            "must_admin"    : False,
        },
        "new_page" : {
            "must_login"    : True,
            "must_admin"    : True,
            #~ "get_page_id"   : True,
        },
        "select_del_page" : {
            "must_login"    : True,
            "must_admin"    : True,
            "CGI_dependent_actions" : {
                "delete_page"       : {
                    "CGI_laws"      : {"Submit":"delete_page"},
                    "CGI_must_have" : ("side_id_to_del",),
                },
            }
        },
        "preview" : {
            "must_login"    : True,
            "must_admin"    : False,
        },
        "save" : {
            "must_login"    : True,
            "must_admin"    : False,
        },
        "sequencing" : {
            "must_login"    : True,
            "must_admin"    : False,
        },
        "save_positions" : {
            "must_login"    : True,
            "must_admin"    : False,
        },
    }

    def __init__( self, PyLucid ):
        self.PyLucid    = PyLucid

        self.config         = PyLucid["config"]
        #~ self.config.debug()
        self.CGIdata        = PyLucid["CGIdata"]
        #~ self.CGIdata.debug()
        self.session        = PyLucid["session"]
        #~ self.session.debug()
        self.db             = PyLucid["db"]
        #~ self.auth       = PyLucid["auth"]
        self.page_msg       = PyLucid["page_msg"]
        self.preferences    = PyLucid["preferences"]
        self.tools          = PyLucid["tools"]
        self.parser         = PyLucid["parser"]
        self.render         = self.PyLucid["render"]

    def new_page( self ):
        "Neue Seite soll angelegt werden"

        core = self.preferences["core"]

        page_data = {
            "parent"            : int( self.CGIdata["page_id"] ),
            "name"              : "NewSide",
            "title"             : "NewSide",
            "template"          : core["defaultTemplate"],
            "style"             : core["defaultStyle"],
            "markup"            : core["defaultMarkup"],
            "showlinks"         : core["defaultShowLinks"],
            "permitViewPublic"  : core["defaultPermitPublic"],
            "ownerID"           : self.session["user_id"],
            "permitViewGroupID" : 1,
            "permitEditGroupID" : 1,
            "content"           : "",
            "keywords"          : "",
            "description"       : "",
        }

        # Damit man bei self.save() noch weiß, das es eine neue Seite ist ;)
        self.session["make_new_page"] = 1

        self.editor_page( page_data )

    def get_page_data( self, page_id ):
        """
        Liefert alle Daten die zum editieren einer Seite notwendig sind zurück
        wird auch von self.archive_page() verwendet
        """
        return self.db.page_items_by_id(
                item_list   = ["parent", "name", "title", "template", "style",
                                "markup", "content", "keywords", "description",
                                "showlinks", "permitViewPublic", "permitViewGroupID",
                                "ownerID", "permitEditGroupID"],
                page_id     = page_id
            )

    #_______________________________________________________________________
    # Edit a page

    def select_edit_page( self ):
        """
        Wenn eine Seite showlinks ausgeschaltet hat, kommt sie nicht mehr im Menü und
        im SiteMap vor. Um sie dennoch editieren zu können, kann man es hierrüber erledigen ;)
        """
        internal_page = self.db.get_internal_page("select_page_to_edit")

        # Wichtig, hier darf keine Modulemaneger Link genutzt werden, weil page_id= schon
        # enthalten ist. Dieser wird jedoch von der select-Box bestimmt!!!

        internal_page['content'] = internal_page['content'] % {
            "url"         : "%s?command=pageadmin&action=edit_page" % self.config.system.real_self_url,
            "side_option" : self.tools.forms().SideOptionList( with_id = True, select = self.CGIdata["page_id"] )
        }
        return internal_page

    def edit_page( self, encode_from_db=False ):
        page_data = self.get_page_data( self.CGIdata["page_id"] )

        status_msg = "" # Nachricht für encodieren

        if encode_from_db:
            # Daten aus der DB sollen convertiert werden
            encoding = self.CGIdata["encoding"]

            try:
                page_data["content"] = page_data["content"].decode( encoding ).encode( "utf8" )
                status_msg = "<h3>[Encoded from DB with '%s']</h3>" % encoding
            except Exception, e:
                status_msg = "<h3>%s</h3>" % e

        self.editor_page( page_data, status_msg )

    def editor_page( self, edit_page_data, status_msg="" ):
        #~ print "Content-type: text/html\n\n<pre>"
        #~ for k,v in edit_page_data.iteritems(): print k," - ",v," ",cgi.escape( str(type(v)) )
        #~ print "</pre>"
        #~ self.CGIdata.debug()

        internal_page = self.db.get_internal_page("edit_page")

        if str( edit_page_data["showlinks"] ) == "1":
            showlinks = " checked"
        else:
            showlinks = ""

        if str( edit_page_data["permitViewPublic"] ) == "1":
            permitViewPublic = " checked"
        else:
            permitViewPublic = ""

        if not edit_page_data.has_key( "summary" ):
            # Information kommt nicht von der Seite, ist aber beim Preview schon vorhanden!
            edit_page_data["summary"] = ""

        MyOptionMaker = self.tools.html_option_maker()

        encoding_option = MyOptionMaker.build_from_list( ["utf8","iso-8859-1"], "utf8" )
        markup_option   = MyOptionMaker.build_from_list( self.config.available_markups, edit_page_data["markup"] )

        parent_option = self.tools.forms().SideOptionList( select=int( edit_page_data["parent"] ) )


        def make_option( table_name, select_item ):
            """ Speziallfall: Select Items sind immer "id" und "name" """
            return MyOptionMaker.build_from_dict(
                data            = self.db.select( ("id","name"), table_name ),
                value_name      = "id",
                txt_name        = "name",
                select_item     = select_item
            )

        template_option             = make_option( "templates", edit_page_data["template"] )
        style_option                = make_option( "styles", edit_page_data["style"] )
        ownerID_option              = make_option( "users", edit_page_data["ownerID"] )
        permitEditGroupID_option    = make_option( "groups", edit_page_data["permitEditGroupID"] )
        permitViewGroupID_option    = make_option( "groups", edit_page_data["permitViewGroupID"] )

        if edit_page_data["content"] == None:
            # Wenn eine Seite mit lucidCMS frisch angelegt wurde und noch kein
            # Text eingegeben wurde, ist "content" == None -> Das Produziert
            # beim cgi.escape( edit_page_data["content"] ) einen traceback :(
            # und so nicht:
            edit_page_data["content"] = ""

        #~ edit_page_data["content"] += "\n\n" + str( edit_page_data )
        #~ form_url = "%s?command=pageadmin&page_id=%s" % ( self.config.system.real_self_url, self.CGIdata["page_id"] )

        try:
            print internal_page["content"] % {
                "status_msg"                : status_msg, # Nachricht beim encodieren
                # Textfelder
                "url"                       : self.command_url,
                "summary"                   : edit_page_data["summary"],
                "name"                      : cgi.escape( edit_page_data["name"] ),
                "title"                     : cgi.escape( edit_page_data["title"] ),
                "keywords"                  : edit_page_data["keywords"],
                "description"               : edit_page_data["description"],
                "content"                   : cgi.escape( edit_page_data["content"] ),
                # Checkboxen
                "showlinks"                 : showlinks,
                "permitViewPublic"          : permitViewPublic,
                # List-Optionen
                "encoding_option"           : encoding_option,
                "markup_option"             : markup_option,
                "parent_option"             : parent_option,
                "template_option"           : template_option,
                "style_option"              : style_option,
                "ownerID_option"            : ownerID_option,
                "permitEditGroupID_option"  : permitEditGroupID_option,
                "permitViewGroupID_option"  : permitViewGroupID_option,
            }
        except KeyError, e:
            print "<h1>generate internal Page fail:</h1><h4>KeyError:'%s'</h4>" % e

    def set_default( self, dictionary ):
        """
        Kompletiert evtl. nicht vorhandene Keys.
        Leere HTML-input-Felder bzw. nicht aktivierte checkboxen erscheinen nicht in den CGIdaten,
        diese müßen aber für die Weiterverarbeitung im Dict vorhanden sein.
        """
        default_dict = {
            "name":"", "title":"", "content":"", "keywords":"", "description":"",
            "showlinks":0, "permitViewPublic":0
        }
        for key, value in default_dict.iteritems():
            if not dictionary.has_key( key ):
                dictionary[key] = value
        return dictionary

    def preview( self ):
        "Preview einer editierten Seite"
        #~ self.CGIdata.debug()

        # CGI-Daten holen und leere Form-Felder "einfügen"
        edit_page_data = self.set_default( self.CGIdata )

        # CGI daten sind immer vom type str, die parent ID muß allerdings eine Zahl sein.
        # Ansonsten wird in MyOptionMaker.build_html_option() kein 'selected'-Eintrag gesetzt :(
        edit_page_data["parent"] = int( edit_page_data["parent"] )

        # Preview der Seite erstellen
        print "\n<h3>edit preview:</h3>\n"
        print '<div id="page_edit_preview">\n'

        # Möchte der rendere gern wissen ;)
        edit_page_data['lastupdatetime'] = "now"

        # Alle Tags ausfüllen und Markup anwenden
        print self.render.render( edit_page_data )

        print "\n</div>\n"

        # Formular der Seite zum ändern wieder dranhängen
        self.editor_page( edit_page_data )

    def save( self ):
        "Abspeichern einer editierten Seite"

        # CGI-Daten holen und leere Form-Felder "einfügen"
        new_page_data = self.set_default( self.CGIdata )

        if not self.session.has_key("make_new_page"):
            # Nur beim editieren, wird evtl. die vorherige Seite Archiviert.
            # Das wird allerdings nicht beim erstellen einer neuen Seite gemacht ;)
            if self.CGIdata.has_key( "trivial" ):
                self.page_msg( "trivial modifications selected. Old side is not archived." )
            else:
                # Nur bei einer nicht trivialen Änderung, wird das Datum aktualisiert
                new_page_data["lastupdatetime"] = self.tools.convert_time_to_sql( time.time() )

                old_page_data = self.get_page_data( self.CGIdata["page_id"] )

                #~ for k,v in old_page_data.iteritems():
                    #~ content += "%s - %s<br>" % (k,v)
                #~ content += "<hr>"

                archiv_data = {
                    "userID"    : self.session["user_id"],
                    "type"      : "PyLucid,page",
                    "date"      : new_page_data["lastupdatetime"],
                    "content"   : pickle.dumps( old_page_data )
                }
                if self.CGIdata.has_key( "summary" ):
                    archiv_data["comment"] = self.CGIdata["summary"]

                self.db.insert( "archive", archiv_data )

                end_time = time.time()

                self.page_msg( "Archived old sidedata." )

        #~ for k,v in self.CGIdata.iteritems():
            #~ content += "%s - %s<br>" % (k,v)
        #~ content += "<hr>"
        #~ for k,v in self.session.iteritems():
            #~ content += "%s - %s<br>" % (k,v)
        #~ content += "<hr>"
        #~ content += str( self.id_of_edit_page )

        item_list   = ["parent", "name", "title", "parent", "template", "style",
                "markup", "content", "keywords", "description",
                "showlinks", "permitViewPublic", "permitViewGroupID",
                "ownerID", "permitEditGroupID"
            ]

        # CGI-Daten holen, die SeitenInformationen enthalten
        new_page_data = {}
        for item in item_list:
            if self.CGIdata.has_key( item ):
                new_page_data[item] = self.CGIdata[item]

        # Daten ergänzen
        new_page_data["lastupdateby"]   = self.session["user_id"]
        new_page_data["lastupdatetime"] = self.tools.convert_time_to_sql( time.time() ) # Letzte Änderungszeit

        if self.session.has_key("make_new_page"):
            # Eine neue Seite soll gespeichert werden
            new_page_data["datetime"] = new_page_data["lastupdatetime"] # Erstellungszeit
            #~ new_page_data["position"] = 0
            try:
                self.db.insert(
                        table   = "pages",
                        data    = new_page_data,
                    )
                del( self.session["make_new_page"] )
            except Exception, e:
                print "<h3>Error to insert new side:'%s'</h3><p>Use browser back botton!</p>" % e

            # Setzt die aktuelle Seite auf die neu erstellte. Das herrausfinden der ID ist
            # nicht ganz so einfach, weil Seitennamen doppelt vorkommen können. Allerdings
            # ist es doch sehr unwahrscheinlich das auch "lastupdatetime" doppelt ist...
            # Na, und wenn schon, dann wird halt die erste genommen ;)
            self.CGIdata["page_id"] = self.db.select(
                select_items    = ["id"],
                from_table      = "pages",
                where           = [
                    ("name",new_page_data["name"]),
                    ("lastupdatetime",new_page_data["lastupdatetime"])
                ]
            )[0]["id"]

            self.page_msg( "New side saved." )
        else:
            # Eine Seite wurde editiert.
            try:
                self.db.update(
                        table   = "pages",
                        data    = new_page_data,
                        where   = ("id",self.CGIdata["page_id"]),
                        limit   = 1
                    )
            except Exception, e:
                print "<h3>Error to update side data: '%s'</h3>" % e

            self.page_msg( "New side data updated." )

    #_______________________________________________________________________
    # Delete a page

    def select_del_page( self ):
        """
        Auswahl welche Seite gelöscht werden soll
        """
        internal_page = self.db.get_internal_page("select_page_to_del")

        internal_page['content'] = internal_page['content'] % {
            "url"         : self.action_url + "select_del_page",
            "side_option" : self.tools.forms().SideOptionList( with_id = True, select = self.CGIdata["page_id"] )
        }
        return internal_page

    def delete_page( self ):
        """
        Löscht die Seite, die ausgewählt wurde
        """
        side_id_to_del = self.CGIdata["side_id_to_del"]

        try:
            comment = self.CGIdata["comment"]
        except KeyError:
            comment = ""

        # Hat die Seite noch Unterseiten?
        parents = self.db.select(
                select_items    = ["name"],
                from_table      = "pages",
                where           = [ ("parent",side_id_to_del) ]
            )
        if parents != ():
            # Hat noch Unterseiten
            msg = "Can't delete Page!"
            self.page_msg( msg )
            print "h3. %s" % msg
            print
            print "Page has parent pages:"
            for side in parents:
                print "* %s" % cgi.escape( side["name"] )
            print "Please move parents."

            # "Menü" wieder anzeigen
            return self.select_del_page()

        try:
            self.archive_page( side_id_to_del, "delete page", comment )
        except Exception, e:
            self.page_msg( "Delete page error:" )
            self.page_msg( "Can't archive side with ID %s: %s" % (side_id_to_del, e) )
            return

        if self.CGIdata["page_id"] == side_id_to_del:
            # Die aktuelle Seite wird gelöscht, also kann sie nicht mehr angezeigt werden.
            # Deswegen gehen wir halt zu parent Seite ;)
            self.CGIdata["page_id"] = self.db.parentID_by_id( side_id_to_del )
            if self.CGIdata["page_id"] == 0:
                # Die oberste Ebene hat ID 0, obwohl es evtl. keine Seite gibt, die ID 0 hat :(
                # Da nehmen wir doch lieber die default-Seite...
                self.CGIdata["page_id"] = self.preferences["core"]["defaultPageName"]

        start_time = time.time()
        self.db.delete(
            table = "pages",
            where = ("id",side_id_to_del),
            limit=1
        )
        duration_time = time.time()-start_time
        self.page_msg(
            "Side with ID %s deleted in %.2fsec." % ( side_id_to_del, duration_time )
        )

        # "Menü" wieder anzeigen
        return self.select_del_page()

    #_______________________________________________________________________

    def archive_page( self, page_id, type, comment ):
        """
        Archiviert die Seite mit der ID >page_id<
        Keine Fehlerabfrage, ob Seiten-ID richtig ist!
        """
        start_time = time.time()
        self.db.insert(
            table = "archive",
            data = {
                "userID"    : self.session["user_id"],
                "type"      : type,
                "date"      : self.tools.convert_time_to_sql( time.time() ),
                "comment"   : comment,
                "content"   : pickle.dumps( self.get_page_data( page_id ) )
            }
        )
        duration_time = time.time()-start_time
        self.page_msg(
            "Archived side in %.2fsec." % duration_time
        )

    #_______________________________________________________________________

    def sequencing( self ):
        """
        Formular zum ändern der Seiten-Reihenfolge
        """

        internal_page = self.db.get_internal_page("sequencing")["content"]

        self.data = self.db.make_order_data()

        self.parent_list = []
        for site in self.data:
            if not site["parent"] in self.parent_list:
                self.parent_list.append( site["parent"] )

        MyOptionMaker = self.tools.html_option_maker()

        position_list = [""] + [str(i) for i in xrange(-10,11)]
        self.position_option = MyOptionMaker.build_from_list( position_list, "" )

        print internal_page % {
            "url"       : self.action_url + "save_positions",
            "form_data" : self.make_order_page(),
        }

    def make_order_page( self, id = 0, deep = 0, form_data="" ):
        """
        Generiert die Liste für die Positionsänderung
        """
        form_data += '<ul>\n'
        for site in self.data:
            if site["parent"] == id:
                form_data += '<li>'

                form_data += "<strong>%s</strong>" % cgi.escape( site["name"] )

                form_data += '<span class="forms">'
                form_data += 'current position: <strong>%s</strong> ' % site["position"]
                form_data += '<select name="page_id_%s">\n' % site["id"]
                form_data += '%s</select>' % self.position_option
                form_data += '<button type="submit" name="Submit">save</button>'
                form_data += '</span>'

                form_data += "</li>\n"

                if site["id"] in self.parent_list:
                    form_data += self.make_order_page( site["id"], deep +1 )

        form_data += "</ul>\n"
        return form_data

    def save_positions( self ):
        """
        Positionsänderungen speichern
        """
        #~ self.CGIdata.debug()
        for key,value in self.CGIdata.iteritems():
            if key.startswith("page_id_"):
                try:
                    page_id = int( key[8:] )
                    position = int( value )
                except Exception,e:
                    self.page_msg(
                        "Can't change page position (%s,%s): %s" % (key, value, e)
                    )
                    continue

                self.db.change_page_position( page_id, position)
                self.page_msg( "Save position %s for page with ID %s" % (position,page_id) )

        # Menu wieder anzeigen
        self.sequencing()









