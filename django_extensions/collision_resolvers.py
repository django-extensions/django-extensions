# -*- coding: utf-8 -*-
import inspect
import sys
from abc import abstractmethod, ABCMeta
from typing import (  # NOQA
    Dict,
    List,
    Optional,
    Tuple,
)

import six
from django.utils.module_loading import import_string
from six import add_metaclass


@add_metaclass(ABCMeta)
class BaseCR:
    """
    Abstract base collision resolver. All collision resolvers needs to inherit from this class.
    To write custom collision resolver you need to overwrite resolve_collisions function.
    It receives Dict[str, List[str]], where key is model name and values are full model names
    (full model name means: module + model_name).
    You should return Dict[str, str], where key is model name and value is full model name.
    """
    @classmethod
    def get_app_name_and_model(cls, full_model_path):  # type: (str) -> Tuple[str, str]
        model_class = import_string(full_model_path)
        return model_class._meta.app_config.name, model_class.__name__

    @abstractmethod
    def resolve_collisions(self, namespace):  # type: (Dict[str, List[str]]) -> Dict[str, str]
        pass


class LegacyCR(BaseCR):
    """
    Default collision resolver. Model from last application in alphabetical order is selected.
    """
    def resolve_collisions(self, namespace):
        result = {}
        for name, models in namespace.items():
            result[name] = models[-1]
        return result


@add_metaclass(ABCMeta)
class AppsOrderCR(LegacyCR):
    APP_PRIORITIES = None  # type: Optional[List]

    def resolve_collisions(self, namespace):
        assert self.APP_PRIORITIES is not None, "You must define APP_PRIORITIES in your resolver class!"
        result = {}
        for name, models in namespace.items():
            if len(models) > 0:
                sorted_models = self._sort_models_depending_on_priorities(models)
                result[name] = sorted_models[0][1]
        return result

    def _sort_models_depending_on_priorities(self, models):  # type: (List[str]) -> List[Tuple[int, str]]
        models_with_priorities = []
        for model in models:
            try:
                app_name, _ = self.get_app_name_and_model(model)
                position = self.APP_PRIORITIES.index(app_name)
            except (ImportError, ValueError):
                position = sys.maxsize
            models_with_priorities.append((position, model))
        return sorted(models_with_priorities)


class InstalledAppsOrderCR(AppsOrderCR):
    """
    Collision resolver which selects first model from INSTALLED_APPS.
    You can set your own app priorities list by subclassing him and overwriting APP_PRIORITIES field.
    This collision resolver will select model from first app on this list.
    If both app's are absent on this list, resolver will choose model from first app in alphabetical order.
    """
    @property
    def APP_PRIORITIES(self):
        from django.conf import settings
        return getattr(settings, 'INSTALLED_APPS', [])


@add_metaclass(ABCMeta)
class PathBasedCR(LegacyCR):
    """
    Abstract resolver which transforms full model name into alias.
    To use him you need to overwrite transform_import function
    which should have one parameter. It will be full model name.
    It should return valid alias as str instance.
    """
    @abstractmethod
    def transform_import(self, module_path):  # type: (str) -> str
        pass

    def resolve_collisions(self, namespace):
        base_imports = super(PathBasedCR, self).resolve_collisions(namespace)
        for name, models in namespace.items():
            if len(models) <= 1:
                continue
            for model in models:
                new_name = self.transform_import(model)
                assert isinstance(new_name, str), "result of transform_import must be str!"
                base_imports[new_name] = model
        return base_imports


class FullPathCR(PathBasedCR):
    """
    Collision resolver which transform full model name to alias by changing dots to underscores.
    He also removes 'models' part of alias, because all models are in models.py files.
    Model from last application in alphabetical order is selected.
    """
    def transform_import(self, module_path):
        module, model = module_path.rsplit('.models', 1)
        module_path = module + model
        return module_path.replace('.', '_')


@add_metaclass(ABCMeta)
class AppNameCR(PathBasedCR):
    """
    Abstract collision resolver which transform pair (app name, model_name) to alias by changing dots to underscores.
    You must define MODIFICATION_STRING which should be string to format with two keyword arguments:
    app_name and model_name. For example: "{app_name}_{model_name}".
    Model from last application in alphabetical order is selected.
    """
    MODIFICATION_STRING = None  # type: Optional[str]

    def transform_import(self, module_path):
        assert self.MODIFICATION_STRING is not None, "You must define MODIFICATION_STRING in your resolver class!"
        app_name, model_name = self.get_app_name_and_model(module_path)
        app_name = app_name.replace('.', '_')
        return self.MODIFICATION_STRING.format(app_name=app_name, model_name=model_name)


class AppNamePrefixCR(AppNameCR):
    """
    Collision resolver which transform pair (app name, model_name) to alias "{app_name}_{model_name}".
    Model from last application in alphabetical order is selected.
    Result is different than FullPathCR, when model has app_label other than current app.
    """
    MODIFICATION_STRING = "{app_name}_{model_name}"


class AppNameSuffixCR(AppNameCR):
    """
    Collision resolver which transform pair (app name, model_name) to alias "{model_name}_{app_name}"
    Model from last application in alphabetical order is selected.
    """
    MODIFICATION_STRING = "{model_name}_{app_name}"


class AppNamePrefixCustomOrderCR(AppNamePrefixCR, InstalledAppsOrderCR):
    """
    Collision resolver which is mixin of AppNamePrefixCR and InstalledAppsOrderCR.
    In case of collisions he sets aliases like AppNamePrefixCR, but sets default model using InstalledAppsOrderCR.
    """
    pass


class AppNameSuffixCustomOrderCR(AppNameSuffixCR, InstalledAppsOrderCR):
    """
    Collision resolver which is mixin of AppNameSuffixCR and InstalledAppsOrderCR.
    In case of collisions he sets aliases like AppNameSuffixCR, but sets default model using InstalledAppsOrderCR.
    """
    pass


class FullPathCustomOrderCR(FullPathCR, InstalledAppsOrderCR):
    """
    Collision resolver which is mixin of FullPathCR and InstalledAppsOrderCR.
    In case of collisions he sets aliases like FullPathCR, but sets default model using InstalledAppsOrderCR.
    """
    pass


@add_metaclass(ABCMeta)
class AppLabelCR(PathBasedCR):
    """
    Abstract collision resolver which transform pair (app_label, model_name) to alias.
    You must define MODIFICATION_STRING which should be string to format with two keyword arguments:
    app_label and model_name. For example: "{app_label}_{model_name}".
    This is different from AppNameCR when the app is nested with several level of namespace:
    Gives sites_Site instead of django_contrib_sites_Site
    Model from last application in alphabetical order is selected.
    """
    MODIFICATION_STRING = None  # type: Optional[str]

    def transform_import(self, module_path):
        assert self.MODIFICATION_STRING is not None, "You must define MODIFICATION_STRING in your resolver class!"
        model_class = import_string(module_path)
        app_label, model_name = model_class._meta.app_label, model_class.__name__
        return self.MODIFICATION_STRING.format(app_label=app_label, model_name=model_name)


class AppLabelPrefixCR(AppLabelCR):
    """
    Collision resolver which transform pair (app_label, model_name) to alias "{app_label}_{model_name}".
    Model from last application in alphabetical order is selected.
    """
    MODIFICATION_STRING = "{app_label}_{model_name}"


class AppLabelSuffixCR(AppLabelCR):
    """
    Collision resolver which transform pair (app_label, model_name) to alias "{model_name}_{app_label}".
    Model from last application in alphabetical order is selected.
    """
    MODIFICATION_STRING = "{model_name}_{app_label}"


class CollisionResolvingRunner:
    def __init__(self):
        pass

    def run_collision_resolver(self, models_to_import):
        # type: (Dict[str, List[str]]) -> Dict[str, List[Tuple[str, str]]]
        dictionary_of_names = self._get_dictionary_of_names(models_to_import)  # type: Dict[str, str]
        return self._get_dictionary_of_modules(dictionary_of_names)

    @classmethod
    def _get_dictionary_of_names(cls, models_to_import):  # type: (Dict[str, List[str]]) -> (Dict[str, str])
        from django.conf import settings
        collision_resolver_class = import_string(getattr(
            settings, 'SHELL_PLUS_MODEL_IMPORTS_RESOLVER',
            'django_extensions.collision_resolvers.LegacyCR'
        ))

        cls._assert_is_collision_resolver_class_correct(collision_resolver_class)
        result = collision_resolver_class().resolve_collisions(models_to_import)
        cls._assert_is_collision_resolver_result_correct(result)

        return result

    @classmethod
    def _assert_is_collision_resolver_result_correct(cls, result):
        assert isinstance(result, dict), "Result of resolve_collisions function must be a dict!"
        for key, value in result.items():
            assert isinstance(key, str), "key in collision resolver result should be str not %s" % key
            assert isinstance(value, str), "value in collision resolver result should be str not %s" % value

    @classmethod
    def _assert_is_collision_resolver_class_correct(cls, collision_resolver_class):
        assert inspect.isclass(collision_resolver_class) and issubclass(
            collision_resolver_class, BaseCR), "SHELL_PLUS_MODEL_IMPORTS_RESOLVER " \
                                               "must be subclass of BaseCR!"
        getargspec = inspect.getfullargspec if six.PY3 else inspect.getargspec
        assert len(getargspec(collision_resolver_class.resolve_collisions).args) == 2, \
            "resolve_collisions function must take one argument!"

    @classmethod
    def _get_dictionary_of_modules(cls, dictionary_of_names):
        # type: (Dict[str, str]) -> Dict[str, List[Tuple[str, str]]]
        dictionary_of_modules = {}  # type: Dict[str, List[Tuple[str, str]]]
        for alias, model in dictionary_of_names.items():
            module_path, model_name = model.rsplit('.', 1)
            dictionary_of_modules.setdefault(module_path, [])
            dictionary_of_modules[module_path].append((model_name, alias))
        return dictionary_of_modules
