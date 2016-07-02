# -*- coding: utf-8 -*-
from unittest import skipIf, skipUnless

import six
from django.test import SimpleTestCase
from django_extensions.management.modelviz import generate_graph_data


class ModelVizTests(SimpleTestCase):
    @skipIf(six.PY3, 'FIXME Python 3 renders labels funny, see below')
    def test_generate_graph_data_can_render_label(self):
        app_labels = ['auth']
        data = generate_graph_data(app_labels)

        models = data['graphs'][0]['models']
        user_data = [x for x in models if x['name'] == 'User'][0]
        relation_labels = [x['label'] for x in user_data['relations']]
        self.assertIn("groups (user)", relation_labels)

    @skipUnless(six.PY3, 'DELETEME Python 3 should render the same as Python 2')
    def test_generate_graph_data_formats_labels_as_bytes(self):
        app_labels = ['auth']
        data = generate_graph_data(app_labels)

        models = data['graphs'][0]['models']
        user_data = [x for x in models if x['name'] == 'User'][0]
        relation_labels = [x['label'] for x in user_data['relations']]
        self.assertIn("groups (b'user')", relation_labels)
