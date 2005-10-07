#!/usr/bin/python
# -*- coding: UTF-8 -*-

__author__  = "Jens Diemer (www.jensdiemer.de)"
__license__ = "GNU General Public License (GPL)"
__url__     = "http://www.PyLucid.org"

"""
Erzeugt das Administration-Menü
(ehemals front_menu aus dem alten page-renderer)

<lucidTag:admin_menu/>
Sollte im Template für jede Seite eingebunden werden.
"""

__version__="0.0.4"

__history__="""
v0.0.4
    - nutzt nun self.db.print_internal_page()
v0.0.3
    - Anpassung an wegfall von apply_markup
v0.0.2
    - lucidTag ist nicht mehr front_menu sondern admin_menu
v0.0.1
    - erste Version
"""

__todo__ = """
"""

# Python-Basis Module einbinden
#~ import



class admin_menu:

    global_rights = {
        "must_login"    : True,
        "must_admin"    : True,
        "has_Tags"      : False,
    }

    module_manager_data = {
        #~ "debug" : True,
        "debug" : False,

        "lucidTag" : {
            "must_login"    : True,
            "must_admin"    : False,
            "has_Tags"      : True,
            "no_rights_error" : True, # Fehlermeldung, wenn der User nicht eingeloggt ist, wird nicht angezeigt
        },
        "edit_page_link"    : global_rights,
        "new_page_link"     : global_rights,
        "del_page_link"     : global_rights,
        "sub_menu_link"     : global_rights,
        "sub_menu"          : {
            "must_login"    : True,
            "must_admin"    : True,
            "has_Tags"      : True,
        },
    }

    def __init__( self, PyLucid ):
        self.db = PyLucid["db"]
        self.page_msg = PyLucid["page_msg"]
        self.config = PyLucid["config"]
        self.CGIdata = PyLucid["CGIdata"]

    def lucidTag( self ):
        """
        Front menu anzeigen
        """
        self.db.print_internal_page("admin_menu")

    def edit_page_link( self ):
        print '<a href="%s&amp;command=pageadmin&amp;action=edit_page">edit page</a>' % self.base_url

    def new_page_link( self ):
        print '<a href="%s&amp;command=pageadmin&amp;action=new_page">new page</a>' % self.base_url

    def sub_menu_link( self ):
        print '<a href="%ssub_menu">sub menu</a>' % self.action_url

    def sub_menu( self ):
        return self.db.get_internal_page("admin_sub_menu")
