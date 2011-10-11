from django.core.management.base import NoArgsCommand
from django.conf import settings

class Command(NoArgsCommand):
    help = """Generates the SQL to create your database for you, as specified in settings.py
The envisioned use case is something like this:

    ./manage.py sqlcreate | mysql -u <db_administrator> -p
    ./manage.py sqlcreate | psql -U <db_administrator> -W"""
    
    requires_model_validation = False
    can_import_settings = True
    
    def handle_noargs(self, **options):
        #print "%s %s %s %s" % (settings.DATABASE_ENGINE, settings.DATABASE_NAME, settings.DATABASE_USER, settings.DATABASE_PASSWORD)
        engine = settings.DATABASE_ENGINE
        dbname = settings.DATABASE_NAME
        dbuser = settings.DATABASE_USER
        dbpass = settings.DATABASE_PASSWORD
        dbhost = settings.DATABASE_HOST
        
        # django settings file tells you that localhost should be specified by leaving
        # the DATABASE_HOST blank
        if len(dbhost) == 1:
            dbhost = 'localhost'
        
        if engine == 'mysql':
            print "CREATE DATABASE %s;" % dbname
            print "GRANT ALL PRIVILEGES ON %s.* to '%s'@'%s' identified by '%s';" % (
                    dbname, dbuser, dbhost, dbpass)
            
        elif engine == 'postgresql_psycopg2':
            print "CREATE USER %s WITH password '%s';" % (dbuser, dbpass)
            print "CREATE DATABASE %s;" % dbname
            
            
        else:
            raise CommandError, "I don't know how to handle %s", engine