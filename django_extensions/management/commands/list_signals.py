# -*- coding: utf-8 -*-
# Based on https://gist.github.com/voldmar/1264102
# and https://gist.github.com/runekaagaard/2eecf0a8367959dc634b7866694daf2c

import gc
import inspect
import weakref
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.signals import (
    ModelSignal, pre_init, post_init, pre_save, post_save, pre_delete,
    post_delete, m2m_changed, pre_migrate, post_migrate
)
from django.utils.encoding import force_str


MSG = '{module}.{name} #{line}'

SIGNAL_NAMES = {
    pre_init: 'pre_init',
    post_init: 'post_init',
    pre_save: 'pre_save',
    post_save: 'post_save',
    pre_delete: 'pre_delete',
    post_delete: 'post_delete',
    m2m_changed: 'm2m_changed',
    pre_migrate: 'pre_migrate',
    post_migrate: 'post_migrate',
}


def get_all_models():
    """
    Returns set of all models defined in all apps.

    This implementation is required because apps.get_models() is an internal API and
    doesn't return abstract models.
    """
    result = set()
    generation = {Model}
    while generation:
        generation = {sc for c in generation for sc in c.__subclasses__()}
        result.update(generation)

    return result


class Command(BaseCommand):
    help = 'List all signals by model and signal type'

    def handle(self, *args, **options):
        model_lookup = {id(m): m for m in get_all_models()}

        signals = [obj for obj in gc.get_objects() if isinstance(obj, ModelSignal)]
        models = defaultdict(lambda: defaultdict(list))

        for signal in signals:
            signal_name = SIGNAL_NAMES.get(signal, 'unknown')
            for receiver in signal.receivers:
                lookup, receiver = receiver
                if isinstance(receiver, weakref.ReferenceType):
                    receiver = receiver()
                if receiver is None:
                    continue
                receiver_id, sender_id = lookup

                model = model_lookup.get(sender_id, '_unknown_')
                if model:
                    models[model][signal_name].append(MSG.format(
                        name=receiver.__name__,
                        module=receiver.__module__,
                        line=inspect.getsourcelines(receiver)[1],
                        path=inspect.getsourcefile(receiver))
                    )

        output = []
        for key in sorted(models.keys(), key=str):
            verbose_name = force_str(key._meta.verbose_name)
            output.append('{}.{} ({})'.format(
                key.__module__, key.__name__, verbose_name))
            for signal_name in sorted(models[key].keys()):
                lines = models[key][signal_name]
                output.append('    {}'.format(signal_name))
                for line in lines:
                    output.append('        {}'.format(line))

        return '\n'.join(output)
