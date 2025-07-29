import unittest
from unittest.mock import Mock
from django_extensions.management.shells import import_items


class TestImportItems(unittest.TestCase):
    def setUp(self):
        self.style = Mock()
        self.style.ERROR = Mock(return_value="ERROR")
        self.style.SQL_COLTYPE = Mock(return_value="SQL_COLTYPE")

    def test_simple_import(self):
        result = import_items(["import sys"], self.style, quiet_load=True)
        self.assertIn("sys", result)
        self.assertEqual(result["sys"].__name__, "sys")

    def test_dotted_import(self):
        result = import_items(["import http.client"], self.style, quiet_load=True)
        self.assertIn("http", result)
        self.assertEqual(result["http"].__name__, "http")
        self.assertTrue(hasattr(result["http"], "client"))
        self.assertEqual(result["http"].client.__name__, "http.client")

    def test_import_with_alias(self):
        result = import_items(["import json as j"], self.style, quiet_load=True)
        self.assertIn("j", result)
        self.assertEqual(result["j"].__name__, "json")

    def test_from_import(self):
        result = import_items(
            ["from collections import defaultdict"], self.style, quiet_load=True
        )
        self.assertIn("defaultdict", result)
        self.assertEqual(result["defaultdict"].__name__, "defaultdict")

    def test_from_import_star(self):
        result = import_items(["from math import *"], self.style, quiet_load=True)
        self.assertIn("sin", result)
        self.assertIn("cos", result)
        self.assertTrue(callable(result["sin"]))
        self.assertTrue(callable(result["cos"]))


if __name__ == "__main__":
    unittest.main()
