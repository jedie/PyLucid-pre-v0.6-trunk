#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Abwicklung von Login/Logout
"""

__version__ = "v0.1.2"

__history__ = """
v0.1.2
    - Verbesserungen:
        - Für Rückmeldungen wird nun page_msg benutzt
        - Nach einem Fehlgeschlagenen Login, wird das login Form mit dem alten Usernamen angezeigt
v0.1.1
    - logout benötigt auch "direct_out": True, damit der Cookie auch gelöscht wird ;)
v0.1.0
    - Anpassung an neuen Module-Manager
v0.0.2
    - time.sleep() bei falschem Login
    - Fehleranzeige beim Login mit Variable "Debug" veränderbar
v0.0.1
    - Umgebaut für den Module-Manager
    - aus der Klasse PyLucid_system.userhandling rausgenommen
"""



# Standart Python Module
import os, sys, md5, time
from Cookie import SimpleCookie

## Dynamisch geladene Module:
## import random -> auth.make_login_page()


# eigene Module
from PyLucid_system import crypt


# =True: Login-Fehler sind aussagekräftiger: Sollte allerdings
# wirklich nur zu Debug-Zwecke eingesetzt werden!!!
# Gleichzeitig wird Modul-Manager Debug ein/aus geschaltet
#~ Debug = True
Debug = False



class auth:

    module_manager_data = {
        "debug" : Debug,

        "login" : {
            "must_login"    : False,
            "direct_out"    : True,
        },
        "logout" : {
            "must_login"    : False,
            "must_admin"    : False,
            "direct_out"    : True,
        },
        "check_login" : {
            "must_login"    : False,
            "direct_out"    : True,
        },
    }

    def __init__( self, PyLucid ):
        self.MyCookie = SimpleCookie()

        self.config     = PyLucid["config"]
        #~ self.config.debug()
        self.CGIdata    = PyLucid["CGIdata"]
        #~ self.CGIdata.debug()
        self.log        = PyLucid["log"]
        self.session    = PyLucid["session"]
        #~ self.session.debug()
        self.db         = PyLucid["db"]
        self.page_msg   = PyLucid["page_msg"]

    ####################################################
    # LogIn

    def login( self ):
        """
        Der User will einloggen.
        Holt das LogIn-Formular aus der DB und stellt es zusammen
        """
        import random

        login_form = self.db.get_internal_page( "login_form" )["content"]

        url = "%s?page_id=%s&command=auth&action=check_login" % (
            self.config.system.real_self_url, self.CGIdata["page_id"]
        )

        try:
            # Alten Usernamen, nach einem Fehlgeschlagenen Login, wieder anzeigen
            username = self.CGIdata["user"]
        except KeyError:
            username = ""

        try:
            return login_form % {
                    "user"          : username,
                    "md5"           : self.config.system.md5javascript,
                    "md5manager"    : self.config.system.md5manager,
                    "rnd"           : random.randint(10000,99999),
                    "url"           : url
                }
        except Exception, e:
            return "Error in login_form! Please check DB. (%s)" % e

    def check_login( self ):
        """
        Überprüft die Daten vom abgeschickten LogIn-Formular und logt den User ein
        """
        try:
            username    = self.CGIdata["user"]
            form_pass1  = self.CGIdata["md5pass1"]
            form_pass2  = self.CGIdata["md5pass2"]
            rnd         = self.CGIdata["rnd"]
            md5login    = self.CGIdata["use_md5login"]
        except KeyError, e:
            # Formulardaten nicht vollst�ndig
            msg  = "<h1>Internal Error:</h1>"
            msg += "<h3>Form data not complete: '%s'</h3>" %e
            msg += "Did you run 'install_PyLucid.py'? Check login form in SQL table 'pages_internal'.<br/>"
            if Debug: msg += "CGI-Keys: " + str(self.CGIdata.keys())
            return msg

        if md5login != 1:
            return "Klartext passwort Übermittlung noch nicht fertig!"

        return self.check_md5_login( username, form_pass1, form_pass2, rnd )

    def _error( self, log_msg, public_msg ):
        """Fehler werden abhängig vom Debug-Status angezeigt/gespeichert"""
        self.log( log_msg )
        time.sleep(3)
        self.page_msg( public_msg )
        if Debug:
            # Debug Modus: Es wird mehr Informationen an den Client geschickt
            self.page_msg( "Debug:",log_msg )
        # Login-Form wieder anzeigen
        return self.login()

    def check_md5_login( self, username, form_pass1, form_pass2, rnd ):
        """
        Überprüft die md5-JavaScript-Logindaten
        """

        if (len( form_pass1 ) != 32) or (len( form_pass2 ) != 32):
            return self._error(
                "Error-0: len( form_pass ) != 32",
                "LogIn Error! (error:0)"
            )

        try:
            # Daten zum User aus der DB holen
            db_userdata = self.db.md5_login_userdata( username )
        except Exception, e:
            # User exisiert nicht.
            return self._error(
                "Error: User '%s' unknown %s" % (username,e) ,
                "User '%s' unknown!" % username
            )

        # Ersten MD5 Summen vergleichen
        if form_pass1 != db_userdata["pass1"]:
            return self._error(
                'Error-1: form_pass1 != db_userdata["pass1"]',
                "LogIn Error: Wrong Password! (error:1)"
            )

        try:
            # Mit erster MD5 Summe den zweiten Teil des Passworts aus
            # der DB entschlüsseln
            db_pass2 = crypt.decrypt( db_userdata["pass2"], form_pass1 )
        except Exception, e:
            return self._error(
                "Error-2: decrypt db_pass2 failt: %s" % e ,
                "LogIn Error: Wrong Password! (error:2)"
            )

        # An den entschlüßelten, zweiten Teil des Passwortes, die Zufallszahl dranhängen...
        db_pass2 += str( rnd )
        # ...daraus die zweite MD5 Summe bilden
        db_pass2md5 = md5.new( db_pass2 ).hexdigest()

        # Vergleichen der zweiten MD5 Summen
        if db_pass2md5 != form_pass2:
            return self._error(
                'Error-3: db_pass2md5 != form_pass2 |%s|' % db_pass2 ,
                "LogIn Error: Wrong Password! (error:3)"
            )

        # Alles in Ordnung, User wird nun eingeloggt:

        self.session.makeSession() # Eine Session er�ffnen

        # Sessiondaten festhalten
        self.session["user_id"]     = db_userdata["id"]
        self.session["user"]        = username
        #~ sefl.session["user_group"]
        self.session["last_action"] = "login"
        if db_userdata['admin'] == 1:
            self.session["isadmin"] = True
        else:
            self.session["isadmin"] = False
        self.session.update_session()

        self.log.write( "OK:Session erstellt. User:'%s' sID:'%s'" % (username, self.session.ID) )
        self.page_msg( "You are logged in." )

    def logout( self ):
        self.session.delete_session()
        self.page_msg( "You are logged out." )



