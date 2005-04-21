#!/usr/bin/python
# -*- coding: UTF-8 -*-

__version__="0.0.1"

"""configuration

 dbconf
--------
Hier wird von dbcondig.py die DB-Daten eingetragen.
Damit man Lokal, per Remote-SQL-Abfrage das ganze auch benutzen
kann, wird hierbei schon mal die Werte für den SQL-Connect hinterlegt.


 preferences
-------------
Hier werden von preferences.py Einstellungen von
der Tabelle preferences gespeichert.
"""


class system:
    # Pfad zur Konfigurations-Datei
    PHPdbconfig = "lucid/dbConfig.php"


dbconf = {
    "dbHost"            : 'Server-URL',
    "dbDatabaseName"    : '',
    "dbUserName"        : 'SQL_user',
    "dbPassword"        : 'SQL_pass',
    "dbTablePrefix"     : 'lucid_'
}

preferences = {}