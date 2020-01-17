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

    def test_render_unicode_field_label(self):
        app_labels = ['django_extensions']
        data = generate_graph_data(app_labels, verbose_names=True)
        models = data['graphs'][0]['models']
        model = [x for x in models if x['name'] == 'UnicodeVerboseNameModel'][0]
        fields = dict((_f['name'], _f['label']) for _f in model['fields'])
        expected = {
            'id': u'ID',
            'cafe': u'Café',
            'parent_cafe': u'Café latte',
        }
        self.assertEqual(expected, fields)
