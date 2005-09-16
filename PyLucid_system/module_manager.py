#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Module Manager

# by jensdiemer.de (steht unter GPL-License)


"""

__version__="0.1.0"

__history__="""
v0.1.0
    - Komplett neu Programmiert!
v0.0.8
    - Andere Handhabung von Modul-Ausgaben auf stderr. Diese sehen nur eingeloggte User als
        page_msg.
v0.0.7
    - NEU: Module können nun auch nur normale print Ausgaben machen, die dann in die
        Seite "eingeblendet" werden sollen
    - NEU: "direct_out"-Parameter, wird z.B. für das schreiben des Cookies in user_auth.py
        verwendet. Dann werden print-Ausgaben nicht zwischengespeichert.
v0.0.6
    - Fehler beim import sehen nur Admins
v0.0.5
    - Debug mit page_msg
v0.0.4
    - "must_login" und "must_admin" muß nun in jedem Modul definiert worden sein.
    - Fehlerabfrage beim Module/Aktion starten
v0.0.3
    - NEU: start_module()
v0.0.2
    - Großer Umbau :)
v0.0.1
    - erste Version
"""


import sys, os, glob, imp, cgi
import cgitb;cgitb.enable()


debug = False
#~ debug = True

class module_manager:
    def __init__( self, PyLucid ):
        self.PyLucid        = PyLucid
        self.page_msg       = PyLucid["page_msg"]
        self.session        = PyLucid["session"]
        self.CGIdata        = PyLucid["CGIdata"]
        self.tools          = PyLucid["tools"]
        self.parser         = PyLucid["parser"]
        self.config         = PyLucid["config"]

        self.CGI_dependency_checker = CGI_dependency_check( PyLucid )

        self.data = {}

    def read_module_info( self, package_name ):
        for module_path in glob.glob( "%s/*.py" % package_name ):
            filename = os.path.split( module_path )[1]
            module_name = os.path.splitext( filename )[0]
            self.data[module_name] = package_name

    def run_tag( self, tag ):
        """
        Ausführen von:
        <lucidTag:'tag'/>
        """
        if tag.find(".") != -1:
            module_name, method_name = tag.split(".",1)
        else:
            module_name = tag
            method_name = "lucidTag"

        try:
            return self._run_module_method( module_name, method_name )
        except run_module_error, e:
            self.page_msg( "run tag %s, error %s" % (tag,e) )
            return str(e)

    def run_function( self, function_name, function_info ):
        """
        Ausführen von:
        <lucidFunction:'function_name'>'function_info'</lucidFunction>
        """
        module_name = function_name
        method_name = "lucidFunction"

        try:
            return self._run_module_method( module_name, method_name, function_info )
        except run_module_error, e:
            self.page_msg( "Error", e )
            return str(e)

    def run_command( self ):
        """
        ein Kommando ausführen.
        """
        #~ print "OK2"
        #~ sys.exit(2)
        try:
            command = self.CGIdata["command"]
            action = self.CGIdata["action"]
        except KeyError, e:
            self.page_msg( "Error in command: KeyError", e )
            return

        if debug == True: self.page_msg( "Command: %s; action: %s" % (command, action) )

        try:
            return self._run_module_method( command, action )
        except run_module_error, e:
            self.page_msg( "Error run command:", e )


    def _run_module_method( self, module_name, main_method, method_parameter=None ):
        """
        Führt eine Methode eines Module aus.
        Kommt es irgendwo zu einem Fehler, ist es die selbsterstellte
        "run_module_error"-Exception mit einer passenden Fehlermeldung.
        """
        #~ if (debug==True) and (not self.data.has_key( module_name )):
            #~ self.page_msg( "module name %s unknown (method: %s)" % (module_name,main_method) )

        try:
            package_name = self.data[module_name]
        except KeyError:
            raise run_module_error(
                "[module name '%s' unknown (method: %s)]" % ( module_name, main_method )
            )

        module              = self._get_module( package_name, module_name )
        module_class        = self._get_module_class( module, module_name )
        method_properties   = self._get_method_properties( module_name, module_class, main_method )


        try:
            self._check_rights( module_name, method_properties, module_class, main_method )
        except run_module_error, e:
            if method_properties.has_key( "no_rights_error" ) and \
            (method_properties["no_rights_error"] == True):
                return ""
            else:
                raise run_module_error( e )

        current_method = self.CGI_dependency_checker.get_current_method(
            module_name, method_properties, main_method, self.class_debug
        )

        class_instance  = self._make_class_instance( module_name, module_class )

        if method_properties.has_key("direct_out"):
            direct_out = method_properties["direct_out"]
        else:
            direct_out = False

        self.put_data_to_module( module_name, class_instance )

        result = self._run_method( module_name, class_instance, current_method, direct_out, method_parameter )

        if method_properties.has_key("has_Tags") and method_properties["has_Tags"] == True:
            result = self.parser.parse( result )

        return result

    def _get_module( self, package_name, module_name ):
        """
        Liefert das Modul als Objekt zurück
        """
        try:
            return __import__(
                "%s.%s" % (package_name, module_name),
                globals(), locals(),
                [module_name]
            )
        except Exception, e:
            raise run_module_error(
                "[Can't import Modul '%s': %s]" % ( module_name, e )
            )

    def _get_module_class( self, module, module_name ):
        """
        Liefert die Klasse im Module als Objekt zurück
        """
        try:
            return getattr( module, module_name )
        except Exception, e:
            raise run_module_error(
                "[Can't get class '%s' from module '%s': %s]" % ( module_name, module_name, e )
            )

    def _make_class_instance( self, module_name, module_class ):
        """
        Erstellt von der ungebundenen Klasse eine Instanz
        """
        try:
            return module_class( self.PyLucid )
        except Exception, e:
            raise run_module_error(
                "[Can't make instance from class %s: %s]" % (module_name, e)
            )

    def _get_method_properties( self, module_name, module_class, method ):
        """
        Liefert aus der Modul-Klasse die Module-Manager Einstellungen zurück
        """
        def check_type( module_name, data, info, method="" ):
            if type(data) != dict:
                raise run_module_error(
                    "[Wrong %s data for module %s %s]" % (info, module_name, method)
                )

        try:
            class_properties = getattr( module_class, "module_manager_data" )
        except Exception, e:
            raise run_module_error(
                "Can't get module_manager_data from %s for method %s" % (module_name, method)
            )

        check_type( module_name, class_properties, "module_manager_data" )

        if class_properties.has_key("debug"):
            self.class_debug = class_properties["debug"]
            if self.class_debug == True:
                self.page_msg( "-"*30 )
                self.page_msg(
                    "Debug for %s.%s:" % (module_class, method)
                )
        else:
            self.class_debug = False

        try:
            method_properties = class_properties[method]
        except Exception, e:
            raise run_module_error(
                "%s has no rights defined for method '%s' or CGI_dependent_actions faulty" % (module_name, method)
            )

        check_type( module_name, method_properties, "module_manager_data", method )

        return method_properties


    def _check_rights( self, module_name, method_properties, module_class, method ):
        """
        Überprüft ob der aktuelle User das Modul überhaupt ausführen darf.
        """
        try:
            must_login = method_properties["must_login"]
        except Exception, e:
            must_login = True
            self.page_msg(
                "must_login not defined (%s) in Module %s for method %s" % (e, module_name, method)
            )

        if must_login == True:
            if self.session.ID == False:
                    raise run_module_error(
                        "[You must login to use %s for method %s]" % (module_name, method)
                    )

            try:
                must_admin = method_properties["must_admin"]
            except Exception, e:
                must_admin = True
                self.page_msg(
                    "must_admin not defined (%s) in %s for method %s" % (e, module_name, method)
                )

            if (must_admin == True) and (self.session["isadmin"] == False):
                raise run_module_error(
                    "You must be an admin to use method %s from module %s!" % (method, module_name)
                )

    def put_data_to_module( self, module_name, class_instance ):
        """
        Daten (Link-URLs) in die Modul-Klasse "einfügen".
        """
        class_instance.link_url = "%s%s" % (
            self.config.system.poormans_url, self.config.system.page_ident
        )
        class_instance.base_url = "%s?page_id=%s" % (
            self.config.system.real_self_url, self.CGIdata["page_id"]
        )
        class_instance.command_url = "%s?page_id=%s&command=%s" % (
            self.config.system.real_self_url, self.CGIdata["page_id"], module_name
        )
        class_instance.action_url = "%s?page_id=%s&command=%s&action=" % (
            self.config.system.real_self_url, self.CGIdata["page_id"], module_name
        )
        # Zum automatischen erstellen eines Menüs:
        class_instance.module_manager_build_menu = self.build_menu

    def _run_method( self, module_name, class_instance, method, direct_out, method_parameter ):
        def run( method_parameter ):
            if method_parameter == None:
                return unbound_method()
            else:
                return unbound_method( method_parameter )

        # Methode aus Klasse erhalten
        if self.config.system.ModuleManager_error_handling == True:
            try:
                unbound_method = getattr( class_instance, method )
            except Exception, e:
                raise run_module_error(
                    "[Can't get method '%s' from module '%s': %s]" % ( method, module_name, e )
                )
        else:
            unbound_method = getattr( class_instance, method )

        if direct_out != True:
            redirector = self.tools.redirector()

        # Methode "ausführen"
        if self.config.system.ModuleManager_error_handling == True:
            try:
                direct_output = run( method_parameter )
            except Exception, e:
                if direct_out != True:
                    redirector.get() # stdout wiederherstellen
                raise run_module_error(
                    "[Can't run method '%s' from module '%s': %s]" % ( method, module_name, e )
                )
        else:
            direct_output = run( method_parameter )

        if direct_out != True:
            return redirector.get()
        else:
            return direct_output

    #________________________________________________________________________________________

    def build_menu( self, module_manager_data, action_url ):
        """
        Generiert automatisch aus den module_manager_data ein "Action"-Menü.
        Wird zur aufgerufenden Klasse übertragen.
        """
        menu_data = {}
        for method, data in module_manager_data.iteritems():
            #~ self.page_msg( method, data )
            try:
                data = data["menu_info"]
            except:
                #~ self.page_msg( "No menu_info for %s" % method )
                continue

            try:
                section     = data["section"]
                description = data["description"]
            except Exception, e:
                self.page_msg( "Error in menu_info:", e )
                continue

            if not menu_data.has_key( section ):
                menu_data[section] = []

            menu_data[section].append(
                [ method, description ]
            )

        #~ self.page_msg( "Debug:", menu_data )

        print "<ul>"
        for section, data in menu_data.iteritems():
            print "\t<li><h5>%s</h5></li>" % section
            print "\t<ul>"
            for item in data:
                print '\t\t<li><a href="%s%s">%s</a></li>' % (
                    action_url, item[0], item[1]
                )
            print "\t</ul>"
        print "</ul>"

    #________________________________________________________________________________________

    def debug( self ):
        import inspect
        self.page_msg( "-"*30 )
        self.page_msg(
            "ModuleManager Debug (from '...%s' line %s):" % (inspect.stack()[1][1][-20:], inspect.stack()[1][2])
        )
        for module_name, package_name  in self.data.iteritems():
            self.page_msg( "%s.%s" % (package_name, module_name) )
        self.page_msg( "-"*30 )


class run_module_error(Exception):
        pass



class CGI_dependency_check:
    def __init__( self, PyLucid ):
        self.CGIdata    = PyLucid["CGIdata"]
        self.page_msg   = PyLucid["page_msg"]

    def get_current_method( self, module_name, method_properties, main_method, debug ):
        """
        Wertet CGI_dependent_actions in den method_properties aus.
        """
        self.module_name    = module_name
        self.main_method    = main_method
        self.debug          = debug

        if not method_properties.has_key("CGI_dependent_actions"):
            # Es gibt keine CGI-Daten abhängige Funktionen
            if self.debug == True:
                self.page_msg(
                    "No CGI_dependent_actions found in %s %s" % (module_name, main_method)
                )
            return main_method

        CGI_dependent_actions = method_properties["CGI_dependent_actions"]
        if type( CGI_dependent_actions ) != dict:
            raise run_module_error(
                "[Error in CGI_dependent_actions Format for %s.%s]" % ( module_name, main_method )
            )

        for method,dependency in CGI_dependent_actions.iteritems():
            if self.check_dependency( dependency, method ) == True:
                # Eine Abhängige methode ist vorhanden
                if self.debug == True:
                    self.page_msg( "current method: %s" % method )
                return method

        if self.debug == True:
            self.page_msg( "current method: %s" % main_method )
        return main_method

    def check_dependency( self, dependency, sub_method ):
        """
        CGI_dependent_actions
        """
        if self.debug == True: self.page_msg( "*** check sub_method %s:" % sub_method )

        if type( dependency ) != dict:
            self.page_msg(
                "Error in CGI_dependent_actions. Modul %s method %s: statements is not from type dict." % (
                    self.module_name, sub_method
                )
            )
            return False

        if not (dependency.has_key("CGI_laws") or dependency.has_key("CGI_must_have") ):
            self.page_msg(
                "Error in CGI_dependent_actions. Modul %s method %s: statements has no key CGI_laws or CGI_must_have" % (
                    self.module_name, sub_method
                )
            )
            return False

        if dependency.has_key( "CGI_laws" ):
            if self._check_CGI_laws( dependency["CGI_laws"] ) != True:
                if self.debug == True: self.page_msg( "check_CGI_laws failt" )
                return False
            else:
                if self.debug == True: self.page_msg( "CGI_laws OK" )
        else:
            if self.debug == True: self.page_msg( "no CGI_laws defined" )

        if dependency.has_key( "CGI_must_have" ):
            if not type( dependency["CGI_must_have"] ) in (list,tuple):
                self.page_msg(
                    "Error in CGI_dependent_actions. Modul %s method %s: CGI_must_have statements are not type list or tuple." % (
                            self.module_name, sub_method
                        )
                    )
                return False
            if self._check_CGI_has_keys( dependency["CGI_must_have"] ) != True:
                if self.debug == True: self.page_msg( "CGI_must_have failt" )
                return False
            else:
                if self.debug == True: self.page_msg( "CGI_must_have OK" )
        else:
            if self.debug == True: self.page_msg( "no CGI_must_have defined" )

        if self.debug == True: self.page_msg( "CGI_dependent_actions OK" )
        return True

    def _check_CGI_has_keys( self, keys ):
        for key in keys:
            if not self.CGIdata.has_key( key ):
                if self.debug == True:
                    self.page_msg( "Error: key %s not found in keys %s" % (key,keys) )
                return False
        return True

    def _check_CGI_laws( self, CGI_laws ):
        for key,value in CGI_laws.iteritems():

            if not self.CGIdata.has_key( key ):
                if self.debug == True:
                    self.page_msg( "key %s not found in CGI_laws (%s)" % (key,CGI_laws) )
                return False

            if type( value ) == str:
                if not self.CGIdata[key] == value:
                    self.page_msg(
                        "Error in CGIdata for %s: CGIdata key %s is not equal %s" % (
                            self.module_name, key, value
                        )
                    )
                    return False
            elif value == int:
                try:
                    self.CGIdata[key] = int( self.CGIdata[key] )
                except Exception, e:
                    self.page_msg(
                        "Error in CGIdata for %s: CGIdata key %s is not type int" % (
                            self.module_name, key
                        )
                    )
            else:
                self.page_msg(
                    "Error in CGI_dependent_actions for %s: The CGI_law type %s for key %s not supported" % (
                        self.module_name, cgi.escape( str(value) ), key
                    )
                )
                return False

        return True






