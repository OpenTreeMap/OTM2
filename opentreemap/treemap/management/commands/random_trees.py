from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.contrib.gis.geos import Point
from treemap.models import ImportEvent, Plot, Tree
from optparse import make_option
from ._private import InstanceDataCommand

import random
import math


class Command(InstanceDataCommand):

    option_list = InstanceDataCommand.option_list + (
        make_option('-r', '--radius',
                    action='store',
                    type='int',
                    dest='radius',
                    default=5000,
                    help='Number of meters from the center'),
        make_option('-n', '--number-of-trees',
                    action='store',
                    type='int',
                    dest='n',
                    default=100000,
                    help='Number of trees to create'),
        make_option('-p', '--prob-of-tree',
                    action='store',
                    type='int',
                    dest='ptree',
                    default=50,
                    help=('Probability that a given plot will '
                          'have a tree (0-100)')))

    def handle(self, *args, **options):
        """ Create some seed data """
        instance, user = self.setup_env(*args, **options)

        n = options['n']
        print("Will create %s plots" % n)

        tree_prob = float(max(100, min(0, options['ptree']))) / 100.0
        max_radius = options['radius']

        center_x = instance.center.x
        center_y = instance.center.y

        import_event = ImportEvent(imported_by=user)
        import_event.save()

        ct = 0
        cp = 0
        for i in xrange(0, n):
            mktree = random.random() < tree_prob
            radius = random.gauss(0.0, max_radius)
            theta = random.random() * 2.0 * math.pi

            x = math.cos(theta) * radius + center_x
            y = math.sin(theta) * radius + center_y

            plot = Plot(instance=instance,
                        geom=Point(x, y),
                        import_event=import_event)

            plot.save_with_user(user)
            cp += 1

            if mktree:
                tree = Tree(plot=plot,
                            import_event=import_event,
                            instance=instance)
                tree.save_with_user(user)
                ct += 1

        print("Created %s trees and %s plots" % (ct, cp))
