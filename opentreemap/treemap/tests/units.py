# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.gis.geos import Point

from treemap.units import (is_convertible, is_formattable, get_display_value,
                           is_convertible_or_formattable, get_storage_value)
from treemap.models import Plot, Tree
from treemap.json_field import set_attr_on_json_field
from treemap.tests import make_instance, make_commander_user

UNIT_TEST_DISPLAY_DEFAULTS = {
    'test': {
        'unit_only': {'units': 'ft'},
        'digit_only': {'digits': 2},
        'both': {'units': 'ft', 'digits': 3}
    }
}


@override_settings(DISPLAY_DEFAULTS=UNIT_TEST_DISPLAY_DEFAULTS)
class UnitConverterTest(TestCase):
    def setUp(self):
        self.instance = make_instance()

    def test_is_convertible_or_formatbile(self):
        self.assertTrue(is_convertible_or_formattable('test', 'unit_only'))
        self.assertTrue(is_convertible_or_formattable('test', 'digit_only'))
        self.assertTrue(is_convertible_or_formattable('test', 'both'))

    def test_is_convertible(self):
        self.assertTrue(is_convertible('test', 'unit_only'))
        self.assertFalse(is_convertible('test', 'digit_only'))
        self.assertTrue(is_convertible('test', 'both'))

    def test_is_formatbile(self):
        self.assertFalse(is_formattable('test', 'unit_only'))
        self.assertTrue(is_formattable('test', 'digit_only'))
        self.assertTrue(is_formattable('test', 'both'))

    def test_get_display_value_unit_conversion(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.test.unit_only.units', 'in')
        val, display_val = get_display_value(
            self.instance, 'test', 'unit_only', 1)
        self.assertAlmostEqual(val, 12)
        self.assertEqual(display_val, '12.0')

    def test_get_display_value_no_unit_conversion_when_same_units(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.test.unit_only.units', 'ft')
        val, display_val = get_display_value(
            self.instance, 'test', 'unit_only', 1)
        self.assertEqual(val, 1)
        self.assertEqual(display_val, '1.0')

    def test_get_display_value_float_formatting(self):
        val, display_val = get_display_value(
            self.instance, 'test', 'digit_only', 1)
        self.assertEqual(val, 1)
        self.assertEqual(display_val, '1.00')

    def test_get_display_value_conversion(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.test.both.units', 'in')
        val, display_val = get_display_value(
            self.instance, 'test', 'both', 1)
        self.assertAlmostEqual(val, 12)
        self.assertEqual(display_val, '12.000')

    def test_get_storage_value(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.test.unit_only.units', 'in')
        self.assertAlmostEqual(1, get_storage_value(self.instance, 'test',
                                                    'unit_only', 12))


INTEGRATION_TEST_DISPLAY_DEFAULTS = {
    'plot': {
        'width': {'units': 'ft', 'digits': 2}
    },
    'tree': {
        'diameter': {'units': 'in', 'digits': 2},
    }
}


@override_settings(DISPLAY_DEFAULTS=INTEGRATION_TEST_DISPLAY_DEFAULTS)
class ConvertibleTest(TestCase):
    def setUp(self):
        self.instance = make_instance()
        self.user = make_commander_user(self.instance)
        self.plot = Plot(instance=self.instance, geom=Point(-7615441, 5953519))
        self.plot.save_with_user(self.user)
        self.tree = Tree(instance=self.instance, plot=self.plot)
        self.tree.save_with_user(self.user)

    def test_save_converts_width_when_units_differ(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.plot.width.units', 'in')
        self.plot.width = 12
        self.plot.save_with_user(self.user)

        updated_plot = Plot.objects.get(pk=self.plot.pk)
        self.assertAlmostEqual(1, updated_plot.width)

    def test_save_converts_diameter_when_units_differ(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.tree.diameter.units', 'ft')
        self.tree.diameter = 1
        self.tree.save_with_user(self.user)

        updated_tree = Tree.objects.get(pk=self.tree.pk)
        self.assertAlmostEqual(12, updated_tree.diameter)

    def test_save_does_not_convert_width_when_units_same(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.plot.width.units', 'ft')
        self.plot.width = 12
        self.plot.save_with_user(self.user)

        updated_plot = Plot.objects.get(pk=self.plot.pk)
        self.assertEqual(12, updated_plot.width)

    def test_save_does_not_convert_diameter_when_units_same(self):
        set_attr_on_json_field(
            self.instance, 'config.value_display.tree.diameter.units', 'in')
        self.tree.diameter = 1
        self.tree.save_with_user(self.user)

        updated_tree = Tree.objects.get(pk=self.tree.pk)
        self.assertEqual(1, updated_tree.diameter)
