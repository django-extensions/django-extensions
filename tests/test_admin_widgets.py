# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils.text import Truncator

from django_extensions.admin import widgets

from .testapp import models


class ForeignKeySearchInputTestCase(TestCase):

    def test_widget_works(self):
        name = models.Name.objects.create(name="Name")
        person = models.Person.objects.create(
            name=name,
            age=30,
        )
        club = models.Club.objects.create(
            name='Club',
        )
        membership = models.Membership.objects.create(club=club, person=person)

        widget = widgets.ForeignKeySearchInput(
            models.Membership._meta.get_field('person').remote_field,
            ['person__name'],
        )

        label = widget.label_for_value(membership.pk)

        self.assertEqual(
            Truncator(person).words(14, truncate='...'),
            label,
        )

        # Just making sure rendering the widget doesn't cause any issue
        widget.render('person', person.pk)
        widget.render('person', None)

        # Check media to make sure rendering media doesn't cause any issue
        self.assertListEqual(
            [
                '/static/django_extensions/js/jquery.bgiframe.js',
                '/static/django_extensions/js/jquery.ajaxQueue.js',
                '/static/django_extensions/js/jquery.autocomplete.js',
            ],
            widget.media._js,
        )
        self.assertListEqual(
            ['/static/django_extensions/css/jquery.autocomplete.css'],
            list(widget.media._css['all']),
        )
