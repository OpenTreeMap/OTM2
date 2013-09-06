from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import unittest
import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from pyvirtualdisplay import Display

import uitests


class Command(BaseCommand):
    """
    Uses a custom test runner to run UI acceptance tests
    from the 'tests' package
    """
    option_list = BaseCommand.option_list + (
        make_option('-s', '--skip-debug-check',
                    action='store_true',
                    dest='skip_debug',
                    help='skip the debug'), )

    def handle(self, *args, **options):
        if settings.DEBUG is False and not options['skip_debug']:
            raise Exception('These tests add data to the currently '
                            'select database backend. If this is a '
                            'production database a failing test could '
                            'leave extra data behind (such as users) or '
                            'delete data that already exists.')

        suite = unittest.TestLoader().loadTestsFromModule(uitests)

        disp = Display(visible=0, size=(800, 600))
        disp.start()

        try:
            uitests.setUpModule()
            rslt = unittest.TextTestRunner(verbosity=2).run(suite)
        finally:
            uitests.tearDownModule()
            disp.stop()

        if not rslt.wasSuccessful():
            sys.exit(1)
