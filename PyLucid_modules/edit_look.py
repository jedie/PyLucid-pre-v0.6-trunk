#!/usr/bin/python
# -*- coding: UTF-8 -*-

# by jensdiemer.de (steht unter GPL-License)

"""
Editor für alles was mit aussehen zu tun hat:
    - edit_style
    - edit_template
    - edit_internal_page
"""

__author__ = "Jens Diemer (www.jensdiemer.de)"

__version__="0.1.0"

__history__="""
v0.1.0
    - Komplettumbau für neuen Module-Manager
v0.0.4
    - Bug: Internal-Page Edit geht nun wieder
v0.0.3
    - Bug: Edit Template: http://sourceforge.net/tracker/index.php?func=detail&aid=1273348&group_id=146328&atid=764837
v0.0.2
    - NEU: Clonen von Stylesheets und Templates nun möglich
    - NEU: Löschen von Stylesheets und Templates geht nun
    - Änderung der "select"-Tabellen, nun Anpassung per CSS möglich
v0.0.1
    - erste Version
"""

__todo__ = """
"""

# Python-Basis Module einbinden
import sys, cgi



#_______________________________________________________________________


class edit_look:

    global_rights = {
            "must_login"    : True,
            "must_admin"    : True,
    }

    module_manager_data = {
        #~ "debug" : True,
        "debug" : False,

        "edit_style" : {
            "must_login"    : True,
            "must_admin"    : True,
            "CGI_dependent_actions" : {
                "edit_style_form"   : {
                    "CGI_laws"      : { "edit" : int }
                },
                "del_style"         : {
                    "CGI_laws"      : { "del" : int }
                },
                "copy_style"        : {
                    "CGI_laws"      : { "duplicate" : "True" },
                    "CGI_must_have" : ("clone_name","new_name"),
                },
                "save_style"        : {
                    "CGI_laws"      : { "Submit":"save", "save" : int },
                    "CGI_must_have" : ("description","content"),
                },
            }
        },

        "edit_template": {
            "must_login"    : True,
            "must_admin"    : True,
            "CGI_dependent_actions" : {
                "edit_template_form"    : {
                    "CGI_laws"          : { "edit" : int }
                },
                "del_template"          : {
                    "CGI_laws"          : { "del" : int }
                },
                "copy_template"         : {
                    "CGI_laws"          : { "duplicate" : "True" },
                    "CGI_must_have"     : ("clone_name","new_name"),
                },
                "save_template"         : {
                    "CGI_laws"          : { "Submit":"save", "save" : int },
                    "CGI_must_have"     : ("description","content"),
                },
            }
        },

        "edit_internal_page" : {
            "must_login"    : True,
            "must_admin"    : True,
            "CGI_dependent_actions" : {
                "edit_internal_page_form"   : { "CGI_must_have": ("edit",) },
                "save_internal_page"        : {
                    "CGI_laws"      : { "Submit":"save" },
                    "CGI_must_have" : ("name","markup","content","description")
                },
            }
        },
    }

    def __init__( self, PyLucid ):
        self.config     = PyLucid["config"]
        #~ self.config.debug()
        self.CGIdata    = PyLucid["CGIdata"]
        #~ self.CGIdata.debug()
        self.db         = PyLucid["db"]
        self.tools      = PyLucid["tools"]
        self.page_msg   = PyLucid["page_msg"]

    #_______________________________________________________________________
    ## Stylesheet

    def edit_style( self ):
        self.edit_style_select_page()

    def edit_style_select_page( self ):
        print "<h2>Edit styles v%s</h2>" % __version__
        self.select_table(
            form_link   = "edit_style",
            table_data  = self.db.get_style_list()
        )

    def edit_style_form( self ):
        """ Seite zum editieren eines Stylesheet """
        style_id = self.CGIdata["edit"]
        try:
            edit_data = self.db.get_style_data( style_id )
        except IndexError:
            print "bad style id!"
            return

        self.make_edit_page(
            edit_data           = edit_data,
            internal_page_name  = "edit_style",
            order               = "edit_style",
            id                  = style_id,
        )

    def copy_style( self ):
        """ Ein Stylesheet soll kopiert werden """
        clone_name = self.CGIdata["clone_name"]
        new_name = self.CGIdata["new_name"]

        style_content = self.db.get_style_data_by_name( clone_name )["content"]

        style_data = {
            "name"          : new_name,
            "description"   : "clone of '%s'" % clone_name,
            "content"       : style_content,
        }
        self.db.new_style( style_data )

        self.page_msg( "style '%s' duplicated to '%s'" % (clone_name, new_name) )
        self.edit_style_select_page()

    def save_style( self ):
        """ Speichert einen editierten Stylesheet """
        style_id = self.CGIdata["save"]

        style_data = {
            "description"   : self.CGIdata["description"],
            "content"       : self.CGIdata["content"]
        }
        self.db.update_style( style_id, style_data )
        self.page_msg( "Style saved!" )
        self.edit_style_select_page()

    def del_style( self ):
        """ Lösche ein Stylesheet """
        style_id = self.CGIdata["del"]
        self.page_msg( "Delete Style (id:'%s')" % style_id )
        self.db.delete_style( style_id )
        self.edit_style_select_page()

    #_______________________________________________________________________
    ## Template

    def edit_template( self ):
        self.edit_template_select_page()

    def edit_template_select_page( self ):
        """ generiert eine Tabelle zur Template Auswahl """
        print "<h2>Edit template v%s</h2>" % __version__
        self.select_table(
            form_link   = "edit_template",
            table_data  = self.db.get_template_list()
        )

    def edit_template_form( self ):
        """ Seite zum editieren eines template """
        template_id = self.CGIdata["edit"]
        try:
            edit_data = self.db.get_template_data( template_id )
        except IndexError:
            print "bad template id!"
            return

        self.make_edit_page(
            edit_data           = edit_data,
            internal_page_name  = "edit_template",
            order               = "edit_template",
            id                  = template_id,
        )

    def copy_template( self ):
        """ Ein Template soll kopiert werden """
        clone_name  = self.CGIdata["clone_name"]
        new_name    = self.CGIdata["new_name"]

        template_content = self.db.get_template_data_by_name( clone_name )["content"]

        template_data = {
            "name"          : new_name,
            "description"   : "clone of '%s'" % clone_name,
            "content"       : template_content,
        }
        self.db.new_template( template_data )

        self.page_msg( "template '%s' duplicated to '%s'" % (clone_name, new_name) )
        self.edit_template_select_page()

    def save_template( self ):
        """ Speichert einen editierten template """
        template_id = self.CGIdata["save"]
        template_data = {
            "description"   : self.CGIdata["description"],
            "content"       : self.CGIdata["content"]
        }
        self.db.update_template( template_id, template_data )
        print "<h3>template saved!</h3>"
        self.edit_template_select_page()

    def del_template( self ):
        """ Lösche ein Template """
        template_id = self.CGIdata["del"]
        self.page_msg( "Delete Template (id:'%s')" % template_id )
        self.db.delete_template( template_id )
        self.edit_template_select_page()

    #_______________________________________________________________________
    ## Methoden für Stylesheet- und Template-Editing

    def make_edit_page( self, edit_data, internal_page_name, order, id ):
        """ Erstellt die Seite zum Stylesheet/Template editieren """

        internal_page   = self.db.get_internal_page(internal_page_name)["content"]

        try:
            print internal_page % {
                "name"          : edit_data["name"],
                "url"           : "%s%s&save=%s" % (self.action_url, order, id),
                "content"       : cgi.escape( edit_data["content"] ),
                "description"   : cgi.escape( edit_data["description"] ),
                "back"          : "%s%s" % (self.action_url, order),
            }
        except KeyError, e:
            print "<h1>generate internal Page fail:</h1><h4>KeyError:'%s'</h4>" % e
            return

    def select_table( self, form_link, table_data ):
        """ Erstellt die Tabelle zum auswählen eines Style/Templates """

        form_tag = '<form name="%s" method="post" action="%s%s">' % (
            form_link, self.action_url, form_link
        )

        print form_tag
        print 'Duplicate <select name="clone_name">'
        print self.tools.html_option_maker().build_from_list( [i["name"] for i in table_data] )
        print '</select> to a new named: '
        print '<input name="new_name" value="" size="20" maxlength="50" type="text">'
        print '<button type="submit" name="duplicate" value="True">clone</button>'
        print '</form>'

        print form_tag
        print '<table id="edit_%s_select" class="edit_table">' % type

        JS = '''onclick="return confirm('Are you sure to delete the item ?')"'''

        for item in table_data:
            print "<tr>"
            print '<td>'
            print '<span class="name">%s</span><br/>' % item["name"]
            print '<span class="description">%s</span>' % item["description"]
            print "</td>"

            print '<td><button type="submit" name="edit" value="%s">edit</button></td>' % item["id"]
            print '<td><button type="submit" name="del" value="%s" %s>del</button></td>' % (
                item["id"], JS
            )

            print "</tr>"
        print '</table></form>'

    #_______________________________________________________________________
    ## Interne Seiten editieren

    def edit_internal_page( self ):
        """ Tabelle zum auswählen einer Internen-Seite zum editieren """
        print "<h2>Edit internal page v%s</h2>" % __version__
        print '<table id="edit_internal_pages_select" class="edit_table">'

        page_list = self.db.get_internal_page_list()
        for item in page_list:
            print "<tr>"
            print "<td>%s</td>" % item["name"]

            print '<td><a href="%sedit_internal_page&edit=%s">edit</a></td>' % (
                self.action_url, item["name"]
            )
            print "<td>%s</td>" % item["description"]
            print "</tr>"
        print "</table>"

    def edit_internal_page_form( self ):
        """ Formular zum editieren einer internen Seite """
        internal_page_name = self.CGIdata["edit"]

        try:
            # Daten der internen Seite, die editiert werden soll
            edit_data = self.db.get_internal_page_data( internal_page_name )
        except IndexError:
            self.page_msg( "bad internal-page name: '%s' !" % cgi.escape(internal_page_name) )
            self.edit_internal_page_select()
            return

        # Daten der interne Seite zum editieren der internen Seiten holen ;)
        edit_page   = self.db.get_internal_page("edit_internal_page")

        OptionMaker = self.tools.html_option_maker()
        markup_option   = OptionMaker.build_from_list( self.config.available_markups, edit_data["markup"] )

        form_url = "%sedit_internal_page&name=%s" % ( self.action_url, internal_page_name )

        try:
            edit_page["content"] = edit_page["content"] % {
                "name"          : internal_page_name,
                "url"           : form_url,
                "content"       : cgi.escape( edit_data["content"] ),
                "description"   : cgi.escape( edit_data["description"] ),
                "markup_option" : markup_option,
                "back"          : form_url,
            }
        except KeyError, e:
            return "<h1>generate internal Page fail:</h1><h4>KeyError:'%s'</h4>" % e

        print edit_page["content"]
        #~ return edit_page["content"], edit_page["markup"]

    def save_internal_page( self ):
        """ Speichert einen editierte interne Seite """
        try:
            internal_page_name = self.CGIdata["name"]
        except Exception, e:
            print "CGI-Error:", e
            return

        try:
            page_data = {
                "content"       : self.CGIdata["content"],
                "description"   : self.CGIdata["description"],
                "markup"        : self.CGIdata["markup"],
            }
        except KeyError,e:
            print "Formdata not complete.", e
            print "set internal Pages to default with install_PyLucid.py"
            print "(use back-Button!)"
            return

        self.db.update_internal_page( internal_page_name, page_data )

        self.page_msg( "internal page '%s' saved!" % cgi.escape( internal_page_name ) )

        # Auswahl wieder anzeigen lassen
        self.edit_internal_page()

    #_______________________________________________________________________
    ## Allgemeine Funktionen

    def error( *msg ):
        page  = "<h2>Error.</h2>"
        page += "<p>%s</p>" % "<br/>".join( [str(i) for i in msg] )
        return page

