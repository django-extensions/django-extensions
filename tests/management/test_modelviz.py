# -*- coding: utf-8 -*-
from django.test import SimpleTestCase
from django_extensions.management.modelviz import generate_graph_data, ON_DELETE_COLORS


class ModelVizTests(SimpleTestCase):
    def test_generate_graph_data_can_render_label(self):
        app_labels = ["auth"]
        data = generate_graph_data(app_labels)

        models = data["graphs"][0]["models"]
        user_data = [x for x in models if x["name"] == "User"][0]
        relation_labels = [x["label"] for x in user_data["relations"]]
        self.assertIn("groups (user)", relation_labels)

    def test_render_unicode_field_label(self):
        app_labels = ["django_extensions"]
        data = generate_graph_data(app_labels, verbose_names=True)
        models = data["graphs"][0]["models"]
        model = [x for x in models if x["name"] == "UnicodeVerboseNameModel"][0]
        fields = dict((_f["name"], _f["label"]) for _f in model["fields"])
        expected = {
            "id": "ID",
            "cafe": "Café",
            "parent_cafe": "Café latte",
        }
        self.assertEqual(expected, fields)

    def test_on_delete_color_coding(self):
        app_labels = ["django_extensions"]
        data = generate_graph_data(app_labels, color_code_deletions=True)

        models = data["graphs"][0]["models"]

        for model in models:
            relations = [
                x
                for x in model["relations"]
                if x["type"] in ("ForeignKey", "OneToOneField")
            ]

            for relation in relations:
                field = [
                    x["field"] for x in model["fields"] if x["name"] == relation["name"]
                ][0]
                on_delete = getattr(field.remote_field, "on_delete", None)
                expected_color = ON_DELETE_COLORS[on_delete]

                self.assertIn("color={}".format(expected_color), relation["arrows"])

    def test_disabled_on_delete_color_coding(self):
        app_labels = ["django_extensions"]
        data = generate_graph_data(app_labels)

        models = data["graphs"][0]["models"]

        for model in models:
            relations = [
                x
                for x in model["relations"]
                if x["type"] in ("ForeignKey", "OneToOneField")
            ]

            for relation in relations:
                self.assertNotIn("color=", relation["arrows"])
