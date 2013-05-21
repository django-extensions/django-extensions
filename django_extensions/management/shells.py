

class ObjectImportError(Exception):
    pass


def import_objects(options, style):
    # XXX: (Temporary) workaround for ticket #1796: force early loading of all
    # models from installed apps. (this is fixed by now, but leaving it here
    # for people using 0.96 or older trunk (pre [5919]) versions.
    from django.db.models.loading import get_models, get_apps
    mongoengine = False
    try:
        # check what mongoengine version is so we make sure this works
        from mongoengine.base import _document_registry
        mongoengine = True
    except:
        pass

    loaded_models = get_models()  # NOQA

    from django.conf import settings
    imported_objects = {'settings': settings}

    dont_load_cli = options.get('dont_load')  # optparse will set this to [] if it doensnt exists
    dont_load_conf = getattr(settings, 'SHELL_PLUS_DONT_LOAD', [])
    dont_load = dont_load_cli + dont_load_conf
    quiet_load = options.get('quiet_load')

    model_aliases = getattr(settings, 'SHELL_PLUS_MODEL_ALIASES', {})

    load_models = {}
    if mongoengine:
        load_models = {}
        for name, mod in _document_registry.items():
            app_name = mod.__module__.split('.')[-2]
            if app_name in dont_load or ("%s.%s" % (app_name, name)) in dont_load:
                continue

            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(name)

    for app_mod in get_apps():
        app_models = get_models(app_mod)
        if not app_models:
            continue

        app_name = app_mod.__name__.split('.')[-2]
        if app_name in dont_load:
            continue

        for mod in app_models:
            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(mod.__name__)

    for app_mod, models in load_models.items():
        app_name = app_mod.split('.')[-2]
        app_aliases = model_aliases.get(app_name, {})
        model_labels = []

        for model_name in models:
            try:
                imported_object = getattr(__import__(app_mod, {}, {}, model_name), model_name)

                if "%s.%s" % (app_name, model_name) in dont_load:
                    continue

                alias = app_aliases.get(model_name, model_name)
                imported_objects[alias] = imported_object
                if model_name == alias:
                    model_labels.append(model_name)
                else:
                    model_labels.append("%s (as %s)" % (model_name, alias))

            except AttributeError as e:
                if not quiet_load:
                    print(style.ERROR("Failed to import '%s' from '%s' reason: %s" % (model_name,
                        app_name, str(e))))
                continue

        if not quiet_load:
            print(style.SQL_COLTYPE("From '%s' autoload: %s" % (app_mod, ", ".join(model_labels))))

    return imported_objects
