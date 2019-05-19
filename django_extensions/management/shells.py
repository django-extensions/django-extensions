# -*- coding: utf-8 -*-
import six
import traceback

from typing import (  # NOQA
    Dict,
    List,
    Tuple,
    Union,
)

from django.apps.config import MODELS_MODULE_NAME
from django.utils.module_loading import import_string
from django import VERSION as DJANGO_VERSION
from django_extensions.collision_resolvers import CollisionResolvingRunner
from django_extensions.import_subclasses import SubclassesFinder

SHELL_PLUS_DJANGO_IMPORTS = {
    'django.core.cache': ['cache'],
    'django.conf': ['settings'],
    'django.contrib.auth': ['get_user_model'],
    'django.db': ['transaction'],
    'django.db.models': [
        'Avg', 'Case', 'Count', 'F', 'Max', 'Min', 'Prefetch', 'Q', 'Sum', 'When',
    ],
    'django.utils': ['timezone'],
}
if DJANGO_VERSION < (1, 10):
    SHELL_PLUS_DJANGO_IMPORTS.update({
        'django.core.urlresolvers': ['reverse'],
    })
else:
    SHELL_PLUS_DJANGO_IMPORTS.update({
        'django.urls': ['reverse'],
    })
if DJANGO_VERSION >= (1, 11):
    SHELL_PLUS_DJANGO_IMPORTS['django.db.models'].extend([
        'Exists', 'OuterRef', 'Subquery',
    ])


class ObjectImportError(Exception):
    pass


def get_app_name(mod_name):
    """
    Retrieve application name from models.py module path

    >>> get_app_name('testapp.models.foo')
    'testapp'

    'testapp' instead of 'some.testapp' for compatibility:
    >>> get_app_name('some.testapp.models.foo')
    'testapp'
    >>> get_app_name('some.models.testapp.models.foo')
    'testapp'
    >>> get_app_name('testapp.foo')
    'testapp'
    >>> get_app_name('some.testapp.foo')
    'testapp'
    """
    rparts = list(reversed(mod_name.split('.')))
    try:
        try:
            return rparts[rparts.index(MODELS_MODULE_NAME) + 1]
        except ValueError:
            # MODELS_MODULE_NAME ('models' string) is not found
            return rparts[1]
    except IndexError:
        # Some weird model naming scheme like in Sentry.
        return mod_name


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
    from django.apps import apps
    from django import setup

    if not apps.ready:
        setup()

    from django.conf import settings

    dont_load_cli = options.get('dont_load', [])
    dont_load_conf = getattr(settings, 'SHELL_PLUS_DONT_LOAD', [])
    dont_load = dont_load_cli + dont_load_conf
    dont_load_any_models = '*' in dont_load
    quiet_load = options.get('quiet_load')
    model_aliases = getattr(settings, 'SHELL_PLUS_MODEL_ALIASES', {})
    app_prefixes = getattr(settings, 'SHELL_PLUS_APP_PREFIXES', {})
    SHELL_PLUS_PRE_IMPORTS = getattr(settings, 'SHELL_PLUS_PRE_IMPORTS', {})

    imported_objects = {}

    def get_dict_from_names_to_possible_models():  # type: () -> Dict[str, List[str]]
        """
        Collect dictionary from names to possible models. Model is represented as his full path.
        Name of model can be alias if SHELL_PLUS_MODEL_ALIASES or SHELL_PLUS_APP_PREFIXES is specified for this model.
        This dictionary is used by collision resolver.
        At this phase we can't import any models, because collision resolver can change results.
        :return: Dict[str, List[str]]. Key is name, value is list of full model's path's.
        """
        models_to_import = {}  # type: Dict[str, List[str]]
        for app_mod, models in sorted(six.iteritems(load_models)):
            app_name = get_app_name(app_mod)
            app_aliases = model_aliases.get(app_name, {})
            prefix = app_prefixes.get(app_name)

            for model_name in sorted(models):
                if "%s.%s" % (app_name, model_name) in dont_load:
                    continue

                alias = app_aliases.get(model_name)

                if not alias:
                    if prefix:
                        alias = "%s_%s" % (prefix, model_name)
                    else:
                        alias = model_name

                models_to_import.setdefault(alias, [])
                models_to_import[alias].append("%s.%s" % (app_mod, model_name))
        return models_to_import

    def import_subclasses():
        base_classes_to_import = getattr(settings, 'SHELL_PLUS_SUBCLASSES_IMPORT', [])  # type: List[Union[str, type]]
        if base_classes_to_import:
            if not quiet_load:
                print(style.SQL_TABLE("# Shell Plus Subclasses Imports"))
            perform_automatic_imports(SubclassesFinder(base_classes_to_import).collect_subclasses())

    def import_models():
        """
        Perform collision resolving and imports all models.
        When collisions are resolved we can perform imports and print information's, because it is last phase.
        This function updates imported_objects dictionary.
        """
        modules_to_models = CollisionResolvingRunner().run_collision_resolver(get_dict_from_names_to_possible_models())
        perform_automatic_imports(modules_to_models)

    def perform_automatic_imports(modules_to_classes):  # type: (Dict[str, List[Tuple[str, str]]]) -> ()
        """
        Import elements from given dictionary.
        :param modules_to_classes: dictionary from module name to tuple.
        First element of tuple is model name, second is model alias.
        If both elements are equal than element is imported without alias.
        """
        for full_module_path, models in modules_to_classes.items():
            model_labels = []
            for (model_name, alias) in sorted(models):
                try:
                    imported_objects[alias] = import_string("%s.%s" % (full_module_path, model_name))
                    if model_name == alias:
                        model_labels.append(model_name)
                    else:
                        model_labels.append("%s (as %s)" % (model_name, alias))
                except ImportError as e:
                    if options.get("traceback"):
                        traceback.print_exc()
                    if not options.get('quiet_load'):
                        print(style.ERROR(
                            "Failed to import '%s' from '%s' reason: %s" % (model_name, full_module_path, str(e))))
            if not options.get('quiet_load'):
                print(style.SQL_COLTYPE("from %s import %s" % (full_module_path, ", ".join(model_labels))))

    def get_apps_and_models():
        for app in apps.get_app_configs():
            if app.models_module:
                yield app.models_module, app.get_models()

    mongoengine = False
    try:
        from mongoengine.base import _document_registry
        mongoengine = True
    except ImportError:
        pass

    # Perform pre-imports before any other imports
    if SHELL_PLUS_PRE_IMPORTS:
        if not quiet_load:
            print(style.SQL_TABLE("# Shell Plus User Imports"))
        imports = import_items(SHELL_PLUS_PRE_IMPORTS, style, quiet_load=quiet_load)
        for k, v in six.iteritems(imports):
            imported_objects[k] = v

    load_models = {}

    if mongoengine and dont_load_any_models:
        for name, mod in six.iteritems(_document_registry):
            name = name.split('.')[-1]
            app_name = get_app_name(mod.__module__)
            if app_name in dont_load or ("%s.%s" % (app_name, name)) in dont_load:
                continue

            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(name)

    if not dont_load_any_models:
        for app_mod, app_models in get_apps_and_models():
            if not app_models:
                continue

            app_name = get_app_name(app_mod.__name__)
            if app_name in dont_load:
                continue

            for mod in app_models:
                if "%s.%s" % (app_name, mod.__name__) in dont_load:
                    continue

                if mod.__module__:
                    # Only add the module to the dict if `__module__` is not empty.
                    load_models.setdefault(mod.__module__, [])
                    load_models[mod.__module__].append(mod.__name__)

    import_subclasses()
    if not quiet_load:
        print(style.SQL_TABLE("# Shell Plus Model Imports%s") % (' SKIPPED' if dont_load_any_models else ''))

    import_models()

    # Imports often used from Django
    if getattr(settings, 'SHELL_PLUS_DJANGO_IMPORTS', True):
        if not quiet_load:
            print(style.SQL_TABLE("# Shell Plus Django Imports"))
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
