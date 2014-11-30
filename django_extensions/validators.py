import unicodedata

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


@deconstructible
class NoControlCharactersValidator(object):
    message = _("Control Characters like new lines or tabs are not allowed.")
    code = "no_control_characters"
    whitelist = None

    def __init__(self, message=None, code=None, whitelist=None):
        if message:
            self.message = message
        if code:
            self.code = code
        if whitelist:
            self.whitelist = whitelist

    def __call__(self, value):
        value = force_text(value)
        whitelist = self.whitelist
        category = unicodedata.category
        for character in value:
            if whitelist and character in whitelist:
                continue
            if category(character)[0] == "C":
                params = {'value': value, 'whitelist': whitelist}
                raise ValidationError(self.message, code=self.code, params=params)

    def __eq__(self, other):
        return (
            isinstance(other, NoControlCharactersValidator) and
            (self.whitelist == other.whitelist) and
            (self.message == other.message) and
            (self.code == other.code)
        )


@deconstructible
class NoWhitespaceValidator(object):
    message = _("Leading and Trailing whitespace is not allowed.")
    code = "no_whitespace"

    def __init__(self, message=None, code=None, whitelist=None):
        if message:
            self.message = message
        if code:
            self.code = code

    def __call__(self, value):
        value = force_text(value)
        if value != value.strip():
            params = {'value': value}
            raise ValidationError(self.message, code=self.code, params=params)

    def __eq__(self, other):
        return (
            isinstance(other, NoWhitespaceValidator) and
            (self.message == other.message) and
            (self.code == other.code)
        )
