from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import logging

from optparse import make_option

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import MultiPolygon, Polygon, GEOSGeometry

from treemap.instance import Instance
from treemap.models import Tree, Plot, Boundary, InstanceUser, User

from treemap.audit import (Role, FieldPermission,
                           add_all_permissions_on_model_to_role)

logger = logging.getLogger('')


class Command(BaseCommand):
    """
    Create a new instance with a single editing role.
    """

    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    help='Specify admin user id'),
        make_option('--center',
                    dest='center',
                    help='Specify the center of the map as an X,Y pair'),
        make_option('--geojson',
                    dest='geojson',
                    help=('Specify a boundary via a geojson file. Must be '
                          'projected in EPSG3857'))
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise Exception(
                'Expected instance name as the first argument')

        name = args[0]

        if not options['user']:
            logger.warning('An admin user was not specified. While not a '


                           'problem initially, no users will be able to '
                           'modify many parts of this instance. It is '
                           'recommended that you create a user first and call '
                           'this command with "--user"')

        if options.get('center', None) and options.get('geojson', None):
            raise Exception('You must specifiy only one of '
                            '"center" and "geojson"')
        elif (not options.get('center', None) and
              not options.get('geojson', None)):
            raise Exception('You must specifiy at least one of '
                            '"center" and "geojson"')

        if options['center']:
            center = options['center'].split(',')
            if len(center) != 2:
                raise Exception('Center should be an x,y pair in EPSG3857')

            x = int(center[0])
            y = int(center[1])
            offset = 50000
            bounds = Polygon(((x - offset, y - offset),
                              (x - offset, y + offset),
                              (x + offset, y + offset),
                              (x + offset, y - offset),
                              (x - offset, y - offset)))

            bounds = MultiPolygon((bounds, ))
        else:
            bounds = GEOSGeometry(open(options['geojson']).read())

        # Instances need roles and roles needs instances... crazy
        # stuff we're going to create the needed role below however,
        # we'll temporarily use a 'dummy role'. The dummy role has
        # no instance.
        dummy_roles = Role.objects.filter(instance__isnull=True)
        if len(dummy_roles) == 0:
            dummy_role = Role.objects.create(name='empty', rep_thresh=0)
        else:
            dummy_role = dummy_roles[0]

        instance = Instance(
            config={},
            name=name,
            bounds=bounds,
            is_public=True,
            default_role=dummy_role)

        instance.full_clean()
        instance.save()

        instance.boundaries = Boundary.objects.filter(
            geom__intersects=bounds)

        role = Role.objects.create(
            name='user', instance=instance, rep_thresh=0)

        for model in [Tree, Plot]:
            add_all_permissions_on_model_to_role(
                model, role, FieldPermission.WRITE_DIRECTLY)

        instance.default_role = role
        instance.save()

        user = User.objects.get(pk=options['user'])
        InstanceUser(
            instance=instance,
            user=user,
            role=role,
            admin=True).save_with_user(user)
