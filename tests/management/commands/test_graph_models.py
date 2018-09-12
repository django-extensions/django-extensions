# -*- coding: utf-8 -*-
import json
from django.core.management import call_command
from django.utils.six import StringIO


def test_graph_models():
    out = StringIO()
    call_command('graph_models', all_applications=True, stdout=out)

    output = out.getvalue()

    assert output.startswith("digraph model_graph {\n")
    assert output.endswith("}\n")
    assert "// Dotfile by Django-Extensions graph_models\n" in output
    assert "// Labels\n" in output
    assert "// Relations\n" in output


def test_graph_models_json():
    out = StringIO()
    call_command('graph_models', all_applications=True, json=True, stdout=out)

    output = out.getvalue()

    assert """"app_name": "django.contrib.auth", """ in output
    assert "created_at" in json.loads(output)
