import os
from django.core.management.base import CommandError, AppCommand, _make_writeable
from optparse import make_option

class Command(AppCommand):
    option_list = AppCommand.option_list + (
    )

    help = ("Creates a Django jobs command directory structure for the given app name"
            " in the current directory.")
    args = "[appname]"
    label = 'application name'

    requires_model_validation = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = True

    def handle_app(self, app, **options):
        directory = os.getcwd()
        app_name = app.__name__.split('.')[-2]
        project_dir = os.path.join(directory, app_name)
        if not os.path.exists(project_dir):
            try:
                os.mkdir(project_dir)
            except OSError, e:
                raise CommandError(e)
        
        copy_template('jobs_template', project_dir)
            
def copy_template(template_name, copy_to):
    """copies the specified template directory to the copy_to location"""
    import extensions
    import re
    import shutil
    
    template_dir = os.path.join(extensions.__path__[0], 'conf', template_name)

    # walks the template structure and copies it
    for d, subdirs, files in os.walk(template_dir):
        relative_dir = d[len(template_dir)+1:]
        if relative_dir and not os.path.exists(os.path.join(copy_to, relative_dir)):
            os.mkdir(os.path.join(copy_to, relative_dir))
        for i, subdir in enumerate(subdirs):
            if subdir.startswith('.'):
                del subdirs[i]
        for f in files:
            if f.endswith('.pyc') or f.startswith('.DS_Store'):
                continue
            path_old = os.path.join(d, f)
            path_new = os.path.join(copy_to, relative_dir, f)
            if os.path.exists(path_new):
                path_new = os.path.join(copy_to, relative_dir, f)
                if os.path.exists(path_new):
                    continue
            fp_old = open(path_old, 'r')
            fp_new = open(path_new, 'w')
            fp_new.write(fp_old.read())
            fp_old.close()
            fp_new.close()
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write(style.NOTICE("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new))
