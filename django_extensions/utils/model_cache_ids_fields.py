# -*- coding: utf-8 -*-
from django.db.models.signals import m2m_changed


def make_link_ids_and_many_to_many(model_class, many_attribute, ids_attribute):
    """Signal update ids fields for many to many relationship
    """
    def link_ids_and_many_to_many(sender, action=None, instance=None, pk_set=None, **kwargs):
        if action == 'post_add':
            ids = getattr(instance, ids_attribute)
            new_ids = list(set(ids + list(pk_set)))
            setattr(instance, ids_attribute, new_ids)
            instance.save()
        elif action == 'post_remove':
            ids = getattr(instance, ids_attribute)
            new_ids = list(set(ids) - pk_set)
            setattr(instance, ids_attribute, new_ids)
            instance.save()
        elif action == 'post_clear':
            setattr(instance, ids_attribute, [])
            instance.save()

    m2m_changed.connect(link_ids_and_many_to_many, sender=getattr(model_class, many_attribute).through, weak=False)
