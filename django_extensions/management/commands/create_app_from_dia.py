import os, re, django_extensions
from optparse import make_option
from subprocess import Popen, PIPE
from django.core.management.base import CommandError, LabelCommand, \
    _make_writeable

EXTENSIONS_PATH = django_extensions.__path__[0]

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--diagram', '-d', action='store', dest='dia_path',
            help='The diagram path of the app to be created'),
        make_option('--parent_path', '-p', action='store', dest='parent_path',
            help='The parent path of the app to be created'),
    )

    help = ("Creates a Django application directory structure based on a "
        "dia diagram.")
    args = "[appname]"
    label = 'application name'

    requires_model_validation = False
    can_import_settings = True

    def handle_label(self, label, **options):
        project_path = os.getcwd()
        project_name = os.path.split(project_path)[-1]
        app_name =label
        app_template = os.path.join(EXTENSIONS_PATH, 'conf', 'app_template')
        app_path = os.path.join(options.get('parent_path') or project_path,
            app_name)
        dia_path = os.path.join(options.get('dia_path') or project_path,
            '%s.dia' % app_name)

        if not os.path.exists(app_template):
            raise CommandError("The template path, %r, does not exist." %
                app_template)

        if not os.path.exists(dia_path):
            raise CommandError("The diagram path, %r, does not exist."
                % dia_path)

        if not re.search(r'^\w+$', label):
            raise CommandError("%r is not a valid application name. "
                "Please use only numbers, letters and underscores." % label)
        try:
            os.makedirs(app_path)
        except OSError, e:
            raise CommandError(e)

        copy_template(app_template, app_path, project_name, app_name)
        generate_models_and_admin(dia_path, app_path, project_name, app_name)


def copy_template(app_template, copy_to, project_name, app_name):
    """copies the specified template directory to the copy_to location"""
    import shutil

    # walks the template structure and copies it
    for d, subdirs, files in os.walk(app_template):
        relative_dir = d[len(app_template)+1:]
        if relative_dir and not os.path.exists(os.path.join(copy_to,
         relative_dir)):
            os.mkdir(os.path.join(copy_to, relative_dir))
        for i, subdir in enumerate(subdirs):
            if subdir.startswith('.'):
                del subdirs[i]
        for f in files:
            if f.endswith('.pyc') or f.startswith('.DS_Store'):
                continue
            path_old = os.path.join(d, f)
            path_new = os.path.join(copy_to, relative_dir, f.replace(
                'app_name', app_name))
            if os.path.exists(path_new):
                path_new = os.path.join(copy_to, relative_dir, f)
                if os.path.exists(path_new):
                    continue
            path_new = path_new.rstrip(".tmpl")
            fp_old = open(path_old, 'r')
            fp_new = open(path_new, 'w')
            fp_new.write(fp_old.read().replace('{{ app_name }}', app_name).\
                replace('{{ project_name }}', project_name))
            fp_old.close()
            fp_new.close()
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write(style.NOTICE("Notice: Couldn't set "
                    "permission bits on %s. You're probably using an uncommon "
                    "filesystem setup. No problem.\n" % path_new))


def generate_models_and_admin(dia_path, app_path, project_name, app_name):
    """Generates the models.py and admin.py files"""

    def format_text(string, indent=False):
        """format string in lines of 80 or less characters"""
        retval = ''
        while string:
            line = string[:77]
            last_space = line.rfind(' ')
            if last_space != -1 and len(string)>77:
                retval += "%s \\\n" % string[:last_space]
                string = string[last_space+1:]
            else:
                retval += "%s\n" % string
                string = ''
            if string and indent:
                string = '    %s' % string
        return retval

    dia2django_path = os.path.join(EXTENSIONS_PATH, 'utils', 'dia2django.py')
    model_path = os.path.join(app_path, 'models.py')
    admin_path = os.path.join(app_path, 'admin.py')

    # Call dia2django models generator
    model_file = Popen([dia2django_path, dia_path], stdout=PIPE).\
        communicate()[0]
    classes = re.findall('class (\w+)', model_file)

    # Generate the models and admin py files
    model_fh = open(model_path, 'w')
    model_fh.write('from django.db import models\n')
    model_fh.write(model_file)
    model_fh.close()
    admin_fh = open(admin_path, 'w')
    admin_fh.write('from django.contrib.admin import site, ModelAdmin\n')
    admin_fh.write(format_text('from %s.%s.models import %s' %
        (project_name, app_name, ', '.join(classes)), indent=True))
    register_text = '\n'.join(map((lambda t: 'site.register(%s)' %t), classes))
    admin_fh.write(format_text('\n\n%s' % register_text))
    admin_fh.close()
