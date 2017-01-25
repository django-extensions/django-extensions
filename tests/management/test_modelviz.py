# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django_extensions.management.modelviz import generate_graph_data


class ModelVizTests(SimpleTestCase):
    def test_generate_graph_data_can_render_label(self):
        app_labels = ['auth']
        data = generate_graph_data(app_labels)

        models = data['graphs'][0]['models']
        user_data = [x for x in models if x['name'] == 'User'][0]
        relation_labels = [x['label'] for x in user_data['relations']]
        self.assertIn("groups (user)", relation_labels)
