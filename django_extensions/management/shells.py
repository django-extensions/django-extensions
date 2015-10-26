import traceback

import django
import six


class ObjectImportError(Exception):
    pass


def import_items(import_directives, style, quiet_load=False):
    """
    Import the items in import_directives and return a list of the imported items

    Each item in import_directives should be one of the following forms
        * a tuple like ('module.submodule', ('classname1', 'classname2')), which indicates a 'from module.submodule import classname1, classname2'
        * a tuple like ('module.submodule', 'classname1'), which indicates a 'from module.submodule import classname1'
        * a tuple like ('module.submodule', '*'), which indicates a 'from module.submodule import *'
        * a simple 'module.submodule' which indicates 'import module.submodule'.

    Returns a dict mapping the names to the imported items
    """
    imported_objects = {}
    for directive in import_directives:
        try:
            # First try a straight import
            if isinstance(directive, six.string_types):
                imported_object = __import__(directive)
                imported_objects[directive.split('.')[0]] = imported_object
                if not quiet_load:
                    print(style.SQL_COLTYPE("import %s" % directive))
                continue
            elif isinstance(directive, (list, tuple)) and len(directive) == 2:
                if not isinstance(directive[0], six.string_types):
                    if not quiet_load:
                        print(style.ERROR("Unable to import %r: module name must be of type string" % directive[0]))
                    continue
                if isinstance(directive[1], (list, tuple)) and all(isinstance(e, six.string_types) for e in directive[1]):
                    # Try the ('module.submodule', ('classname1', 'classname2')) form
                    imported_object = __import__(directive[0], {}, {}, directive[1])
                    imported_names = []
                    for name in directive[1]:
                        try:
                            imported_objects[name] = getattr(imported_object, name)
                        except AttributeError:
                            if not quiet_load:
                                print(style.ERROR("Unable to import %r from %r: %r does not exist" % (name, directive[0], name)))
                        else:
                            imported_names.append(name)
                    if not quiet_load:
                        print(style.SQL_COLTYPE("from %s import %s" % (directive[0], ', '.join(imported_names))))
                elif isinstance(directive[1], six.string_types):
                    # If it is a tuple, but the second item isn't a list, so we have something like ('module.submodule', 'classname1')
                    # Check for the special '*' to import all
                    if directive[1] == '*':
                        imported_object = __import__(directive[0], {}, {}, directive[1])
                        for k in dir(imported_object):
                            imported_objects[k] = getattr(imported_object, k)
                        if not quiet_load:
                            print(style.SQL_COLTYPE("from %s import *" % directive[0]))
                    else:
                        imported_object = getattr(__import__(directive[0], {}, {}, [directive[1]]), directive[1])
                        imported_objects[directive[1]] = imported_object
                        if not quiet_load:
                            print(style.SQL_COLTYPE("from %s import %s" % (directive[0], directive[1])))
                else:
                    if not quiet_load:
                        print(style.ERROR("Unable to import %r from %r: names must be of type string" % (directive[1], directive[0])))
            else:
                if not quiet_load:
                    print(style.ERROR("Unable to import %r: names must be of type string" % directive))
        except ImportError:
            try:
                if not quiet_load:
                    print(style.ERROR("Unable to import %r" % directive))
            except TypeError:
                if not quiet_load:
                    print(style.ERROR("Unable to import %r from %r" % directive))

    return imported_objects


def import_objects(options, style):
    # Django 1.7 introduced the app registry which must be initialized before we
    # can call get_apps(). Django already does this for us when we are invoked
    # as manage.py command, but we have to do it ourselves if when running as
    # iPython notebook extension, so we call django.setup() if the app registry
    # isn't initialized yet. The try/except can be removed when support for
    # Django 1.6 is dropped.
    try:
        from django.apps import apps
        from django import setup
    except ImportError:
        from django.db.models.loading import get_models, get_apps

        def get_apps_and_models():
            for app_mod in get_apps():
                app_models = get_models(app_mod)
                yield app_mod, app_models
    else:
        if not apps.ready:
            setup()

        def get_apps_and_models():
            for app in apps.get_app_configs():
                if app.models_module:
                    yield app.models_module, app.get_models()

    mongoengine = False
    try:
        from mongoengine.base import _document_registry
        mongoengine = True
    except:
        pass

    from django.conf import settings
    imported_objects = {}

    dont_load_cli = options.get('dont_load')  # optparse will set this to [] if it doensnt exists
    dont_load_conf = getattr(settings, 'SHELL_PLUS_DONT_LOAD', [])
    dont_load = dont_load_cli + dont_load_conf
    quiet_load = options.get('quiet_load')

    model_aliases = getattr(settings, 'SHELL_PLUS_MODEL_ALIASES', {})

    # Perform pre-imports before any other imports
    SHELL_PLUS_PRE_IMPORTS = getattr(settings, 'SHELL_PLUS_PRE_IMPORTS', {})
    if SHELL_PLUS_PRE_IMPORTS:
        if not quiet_load:
            print(style.SQL_TABLE("# Shell Plus User Imports"))
        imports = import_items(SHELL_PLUS_PRE_IMPORTS, style, quiet_load=quiet_load)
        for k, v in six.iteritems(imports):
            imported_objects[k] = v

    load_models = {}

    if mongoengine:
        for name, mod in six.iteritems(_document_registry):
            name = name.split('.')[-1]
            app_name = mod.__module__.split('.')[-2]
            if app_name in dont_load or ("%s.%s" % (app_name, name)) in dont_load:
                continue

            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(name)

    for app_mod, app_models in get_apps_and_models():
        if not app_models:
            continue

        app_name = app_mod.__name__.split('.')[-2]
        if app_name in dont_load:
            continue

        app_aliases = model_aliases.get(app_name, {})
        for mod in app_models:
            if "%s.%s" % (app_name, mod.__name__) in dont_load:
                continue

            if mod.__module__:
                # Only add the module to the dict if `__module__` is not empty.
                load_models.setdefault(mod.__module__, [])
                load_models[mod.__module__].append(mod.__name__)

    if not quiet_load:
        print(style.SQL_TABLE("# Shell Plus Model Imports"))

    for app_mod, models in sorted(six.iteritems(load_models)):
        try:
            app_name = app_mod.split('.')[-2]
        except IndexError:
            # Some weird model naming scheme like in Sentry.
            app_name = app_mod
        app_aliases = model_aliases.get(app_name, {})
        model_labels = []

        for model_name in sorted(models):
            try:
                imported_object = getattr(__import__(app_mod, {}, {}, [model_name]), model_name)

                if "%s.%s" % (app_name, model_name) in dont_load:
                    continue

                alias = app_aliases.get(model_name, model_name)
                imported_objects[alias] = imported_object
                if model_name == alias:
                    model_labels.append(model_name)
                else:
                    model_labels.append("%s (as %s)" % (model_name, alias))

            except AttributeError as e:
                if options.get("traceback"):
                    traceback.print_exc()
                if not quiet_load:
                    print(style.ERROR("Failed to import '%s' from '%s' reason: %s" % (model_name, app_mod, str(e))))
                continue

        if not quiet_load:
            print(style.SQL_COLTYPE("from %s import %s" % (app_mod, ", ".join(model_labels))))

    # Imports often used from Django
    if getattr(settings, 'SHELL_PLUS_DJANGO_IMPORTS', True):
        if not quiet_load:
            print(style.SQL_TABLE("# Shell Plus Django Imports"))
        SHELL_PLUS_DJANGO_IMPORTS = {
            'django.core.cache': ['cache'],
            'django.core.urlresolvers': ['reverse'],
            'django.conf': ['settings'],
            'django.db': ['transaction'],
            'django.db.models': ['Avg', 'Count', 'F', 'Max', 'Min', 'Sum', 'Q'],
            'django.utils': ['timezone'],
        }
        if django.VERSION[:2] >= (1, 7):
            SHELL_PLUS_DJANGO_IMPORTS['django.db.models'].append("Prefetch")
        if django.VERSION[:2] >= (1, 8):
            SHELL_PLUS_DJANGO_IMPORTS['django.db.models'].extend(["Case", "When"])
        imports = import_items(SHELL_PLUS_DJANGO_IMPORTS.items(), style, quiet_load=quiet_load)
        for k, v in six.iteritems(imports):
            imported_objects[k] = v

    # Perform post-imports after any other imports
    SHELL_PLUS_POST_IMPORTS = getattr(settings, 'SHELL_PLUS_POST_IMPORTS', {})
    if SHELL_PLUS_POST_IMPORTS:
        if not quiet_load:
            print(style.SQL_TABLE("# Shell Plus User Imports"))
        imports = import_items(SHELL_PLUS_POST_IMPORTS, style, quiet_load=quiet_load)
        for k, v in six.iteritems(imports):
            imported_objects[k] = v

    return imported_objects
