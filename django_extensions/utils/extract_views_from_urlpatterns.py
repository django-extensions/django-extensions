from django.core.exceptions import ViewDoesNotExist
from django.urls import URLPattern, URLResolver
from django.utils import translation


class RegexURLPattern:  # type: ignore
    pass


class RegexURLResolver:  # type: ignore
    pass


class LocaleRegexURLResolver:  # type: ignore
    pass


def extract_views_from_urlpatterns(
    urlpatterns, languages=((None, None),), base="", namespace=None
):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a three-tuple: (view_func, regex, name)
    """
    views = []
    for p in urlpatterns:
        if isinstance(p, (URLPattern, RegexURLPattern)):
            try:
                if not p.name:
                    name = p.name
                elif namespace:
                    name = "{0}:{1}".format(namespace, p.name)
                else:
                    name = p.name
                pattern = describe_pattern(p)
                views.append((p.callback, base + pattern, name))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, (URLResolver, RegexURLResolver)):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = "{0}:{1}".format(namespace, p.namespace)
            else:
                _namespace = p.namespace or namespace
            pattern = describe_pattern(p)
            if isinstance(p, LocaleRegexURLResolver):
                for language in languages:
                    with translation.override(language[0]):
                        views.extend(
                            extract_views_from_urlpatterns(
                                patterns,
                                languages,
                                base + pattern,
                                namespace=_namespace,
                            )
                        )
            else:
                views.extend(
                    extract_views_from_urlpatterns(
                        patterns, languages, base + pattern, namespace=_namespace
                    )
                )
        elif hasattr(p, "_get_callback"):
            try:
                views.append((p._get_callback(), base + describe_pattern(p), p.name))
            except ViewDoesNotExist:
                continue
        elif hasattr(p, "url_patterns") or hasattr(p, "_get_url_patterns"):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(
                extract_views_from_urlpatterns(
                    patterns, languages, base + describe_pattern(p), namespace=namespace
                )
            )
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views


def describe_pattern(p):
    return str(p.pattern)
