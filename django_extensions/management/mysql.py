# -*- coding: utf-8 -*-
from six.moves import configparser


def parse_mysql_cnf(dbinfo):
    """
    Attempt to parse mysql database config file for connection settings.
    Ideally we would hook into django's code to do this, but read_default_file is handled by the mysql C libs
    so we have to emulate the behaviour

    Settings that are missing will return ''
    returns (user, password, database_name, database_host, database_port)
    """
    read_default_file = dbinfo.get('OPTIONS', {}).get('read_default_file')
    if read_default_file:
        config = configparser.RawConfigParser({
            'user': '',
            'password': '',
            'database': '',
            'host': '',
            'port': '',
            'socket': '',
        })
        import os
        config.read(os.path.expanduser(read_default_file))
        try:
            user = config.get('client', 'user')
            password = config.get('client', 'password')
            database_name = config.get('client', 'database')
            database_host = config.get('client', 'host')
            database_port = config.get('client', 'port')
            socket = config.get('client', 'socket')

            if database_host == 'localhost' and socket:
                # mysql actually uses a socket if host is localhost
                database_host = socket

            return user, password, database_name, database_host, database_port

        except configparser.NoSectionError:
            pass

    return '', '', '', '', ''
