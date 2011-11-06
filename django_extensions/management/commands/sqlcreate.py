import django
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
import sys

class Command(NoArgsCommand):
    help = """Generates the SQL to create your database for you, as specified in settings.py
The envisioned use case is something like this:

    ./manage.py sqlcreate [--router=<routername>] | mysql -u <db_administrator> -p
    ./manage.py sqlcreate [--router=<routername>] | psql -U <db_administrator> -W"""

    requires_model_validation = False
    can_import_settings = True

    @staticmethod
    def set_db_settings(**options):
        if django.get_version() >= "1.2":
            router = options.get('router')
            if router == None:
                return False

            # retrieve this with the 'using' argument
            dbinfo = settings.DATABASES.get(router)
            settings.DATABASE_ENGINE = dbinfo.get('ENGINE').split('.')[-1]
            settings.DATABASE_USER = dbinfo.get('USER')
            settings.DATABASE_PASSWORD = dbinfo.get('PASSWORD')
            settings.DATABASE_NAME = dbinfo.get('NAME')
            settings.DATABASE_HOST = dbinfo.get('HOST')
            settings.DATABASE_PORT = dbinfo.get('PORT')
            return True
        else:
            # settings are set for django < 1.2 no modification needed
            return True

    def handle_noargs(self, **options):

        if django.get_version() >= "1.2":
            got_db_settings = self.set_db_settings(**options)
            if not got_db_settings:
                raise CommandError("You are using Django %s which requires to specify the db-router.\nPlease specify the router by adding --router=<routername> to this command." % django.get_version())

        #print "%s %s %s %s" % (settings.DATABASE_ENGINE, settings.DATABASE_NAME, settings.DATABASE_USER, settings.DATABASE_PASSWORD)
        engine = settings.DATABASE_ENGINE
        dbname = settings.DATABASE_NAME
        dbuser = settings.DATABASE_USER
        dbpass = settings.DATABASE_PASSWORD
        dbhost = settings.DATABASE_HOST

        # django settings file tells you that localhost should be specified by leaving
        # the DATABASE_HOST blank
        if not dbhost:
            dbhost = 'localhost'

        if engine == 'mysql':
            sys.stderr.write("""-- WARNING!: https://docs.djangoproject.com/en/dev/ref/databases/#collation-settings
-- Please read this carefully! Collation will be set to utf8_bin to have case-sensitive data.
""")
            print "CREATE DATABASE %s CHARACTER SET utf8 COLLATE utf8_bin;" % dbname
            print "GRANT ALL PRIVILEGES ON %s.* to '%s'@'%s' identified by '%s';" % (
                    dbname, dbuser, dbhost, dbpass)
        elif engine == 'postgresql_psycopg2':
            print "CREATE USER %s WITH ENCRYPTED PASSWORD '%s';" % (dbuser, dbpass)
            print "CREATE DATABASE %s WITH ENCODING 'UTF-8' OWNER \"%s\";" % (dbname, dbuser)
            #print "GRANT ALL PRIVILEGES ON DATABASE %s TO %s" % (dbname, dbuser)
        elif engine == 'sqlite3':
            sys.stderr.write("-- manage.py syncdb will automatically create a sqlite3 database file.\n")
        else:
            # CREATE DATABASE is not SQL standard, but seems to be supported by most.
            sys.stderr.write("-- Don't know how to handle '%s' falling back to SQL.\n" % engine)
            print "CREATE DATABASE %s;" % dbname
            print "GRANT ALL PRIVILEGES ON DATABASE %s to %s" % (dbname, dbuser)
