from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from contextlib import contextmanager
from optparse import make_option
import json

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import fromstr
from django.conf import settings

from treemap.models import (User, Plot, Tree, Species)
from ._private import InstanceDataCommand


MODELS = {
    'tree': {
        'common_fields': {'plot', 'species', 'readonly', 'canopy_height',
                          'date_planted', 'date_removed', 'height'},
        'renamed_fields': {'dbh': 'diameter'},
        'undecided_fields': {'import_event'},
        'removed_fields': {'tree_owner', 'steward_name', 'sponsor',
                           'species_other1', 'species_other2',
                           'orig_species', 'present', 'last_updated',
                           'last_updated_by', 's_order', 'photo_count',
                           'projects', 'condition', 'canopy_condition',
                           'url', 'pests', 'steward_user'},
        'missing_fields': {'instance', },
        'value_transformers': {
            'plot': (lambda x: Plot.objects.get(pk=x)),
            'species': (lambda x: Species.objects.get(pk=x)),
            }
    },
    'plot': {
        'common_fields': {'width', 'length', 'address_street', 'address_zip',
                          'address_city', 'owner_orig_id', 'readonly'},
        'renamed_fields': {'geometry': 'geom'},
        'undecided_fields': {'import_event'},
        'removed_fields': {'type', 'powerline_conflict_potential',
                           'sidewalk_damage', 'neighborhood',
                           'neighborhoods', 'zipcode', 'geocoded_accuracy',
                           'geocoded_address', 'geocoded_lat', 'geocoded_lon',
                           'present', 'last_updated', 'last_updated_by',
                           'data_owner', 'owner_additional_id',
                           'owner_additional_properties'},
        'missing_fields': {'instance', },
        'value_transformers': {
            'geometry': (lambda x: fromstr(x, srid=4326)),
        },
    },
    'species': {
        'common_fields': {'bloom_period', 'common_name', 'cultivar_name',
                          'fact_sheet', 'fall_conspicuous',
                          'flower_conspicuous', 'fruit_period', 'gender',
                          'genus', 'native_status', 'palatable_human',
                          'plant_guide', 'species', 'symbol',
                          'wildlife_value'},
        'renamed_fields': {'v_max_height': 'max_height',
                           'v_max_dbh': 'max_dbh'},
        'undecided_fields': set(),
        'removed_fields': {'alternate_symbol', 'v_multiple_trunks',
                           'tree_count', 'resource', 'itree_code',
                           'other_part_of_name', 'family',
                           'scientific_name'},
        'value_transformers': {
            'v_max_height': (lambda x: x or 10000),
            'v_max_dbh': (lambda x: x or 10000),
        },
    },
    'user': {
        'common_fields': {'username', 'password', 'email', 'date_joined',
                          'first_name', 'last_name', 'is_active',
                          'is_superuser', 'is_staff', 'last_login'},
        'renamed_fields': {},
        'undecided_fields': set(),
        'removed_fields': {'groups', 'user_permissions'},
        'missing_fields': {'roles', 'reputation'},
        'value_transformers': {},
    },
}


def validate_model(model_name, data_hash):
    """
    Makes sure the fields specified in the MODELS global
    account for all of the provided data
    """
    common_fields = MODELS[model_name]['common_fields']
    renamed_fields = MODELS[model_name]['renamed_fields']
    removed_fields = MODELS[model_name]['removed_fields']
    undecided_fields = MODELS[model_name]['undecided_fields']
    expected_fields = (common_fields |
                       set(renamed_fields.keys()) |
                       removed_fields |
                       undecided_fields)

    provided_fields = set(data_hash['fields'].keys())

    if expected_fields != provided_fields:
        raise Exception('model validation failure. \n\n'
                        'Expected: %s \n\n'
                        'Got %s\n\n'
                        'Symmetric Difference: %s'
                        % (expected_fields, provided_fields,
                           expected_fields.
                           symmetric_difference(provided_fields)))


def hash_to_model(model_cls, model_name, data_hash, instance, user):
    """
    Takes a model specified in the MODELS global and a
    hash of json data and attempts to populate a django
    model. Does not save.
    """

    validate_model(model_name, data_hash)

    common_fields = MODELS[model_name]['common_fields']
    renamed_fields = MODELS[model_name]['renamed_fields']

    model = model_cls()

    identity = (lambda x: x)

    for field in common_fields.union(renamed_fields):
        transform_value_fn = MODELS[model_name]['value_transformers']\
            .get(field, identity)
        try:
            transformed_value = transform_value_fn(data_hash['fields'][field])
            field = renamed_fields.get(field, field)
            setattr(model, field, transformed_value)
        except ObjectDoesNotExist as d:
            print("Warning: %s ... SKIPPING" % d)

    # hasattr will not work here because it
    # just calls getattr and looks for exceptions
    # not differentiating between DoesNotExist
    # and AttributeError
    try:
        getattr(model, 'instance')
    except ObjectDoesNotExist:
        model.instance = instance
    except AttributeError:
        pass

    model.pk = data_hash['pk']

    return model


@contextmanager
def more_permissions(role, user, system_user):
    """
    Temporarily adds more permissions to a user

    This is useful for odd CRUD events that take place
    outside of the normal context of the app, like imports
    and migrations.
    """
    backup_roles = list(user.roles.all())
    user.roles.clear()
    user.roles.add(role)
    user.save_with_user(system_user)
    yield user
    user.roles.remove(role)
    user.roles.add(*backup_roles)
    user.save_with_user(system_user)


def try_save_user_hash_to_model(model_cls, model_name, model_hash,
                                instance, system_user, god_role,
                                user_field_to_try):
    """
    Tries to save an object with the app user that should own
    the object. If not possible, falls back to the system_user.
    """
    model = hash_to_model(model_cls, model_name, model_hash,
                          instance, system_user)

    potential_user_id = model_hash['fields'][user_field_to_try]
    if potential_user_id:
        user = User.objects.get(pk=potential_user_id)
    else:
        user = system_user

    with more_permissions(god_role, user, system_user) as elevated_user:
        model.save_with_user(elevated_user)

    return model


class Command(InstanceDataCommand):

    option_list = InstanceDataCommand.option_list + (
        make_option('-s', '--species-fixture',
                    action='store',
                    type='string',
                    dest='species_fixture',
                    help='path to json dump containing species data'),
        make_option('-u', '--user-fixture',
                    action='store',
                    type='string',
                    dest='user_fixture',
                    help='path to json dump containing user data'),
        make_option('-p', '--plot-fixture',
                    action='store',
                    type='string',
                    dest='plot_fixture',
                    help='path to json dump containing plot data'),
        make_option('-t', '--tree-fixture',
                    action='store',
                    type='string',
                    dest='tree_fixture',
                    help='path to json dump containing tree data'),
    )

    def handle(self, *args, **options):
        """ Create some seed data """

        if settings.DEBUG:
            print('In order to run this command you must manually'
                  'set DEBUG=False in your settings file.')
            return 1

        if options['instance']:
            instance, system_user = self.setup_env(*args, **options)
        else:
            print('Invalid instance provided.')
            return 1

        species_hashes = []
        user_hashes = []
        plot_hashes = []
        tree_hashes = []

        try:
            species_file = open(options['species_fixture'], 'r')
            species_hashes = json.load(species_file)
        except:
            print('No valid species fixture provided ... SKIPPING')

        try:
            user_file = open(options['user_fixture'], 'r')
            user_hashes = json.load(user_file)
        except:
            print('No valid user fixture provided    ... SKIPPING')

        try:
            plot_file = open(options['plot_fixture'], 'r')
            plot_hashes = json.load(plot_file)
        except:
            print('No valid plot fixture provided    ... SKIPPING')

        try:
            tree_file = open(options['tree_fixture'], 'r')
            tree_hashes = json.load(tree_file)
        except:
            print('No valid tree fixture provided    ... SKIPPING')

        ##########################################
        # models saved with system user
        ##########################################

        if user_hashes:
            for user_hash in user_hashes:
                user = hash_to_model(User, 'user', user_hash,
                                     instance, system_user)
                user.save_with_user(system_user)

        if species_hashes:
            for species_hash in species_hashes:
                species = hash_to_model(Species, 'species', species_hash,
                                        instance, system_user)
                species.save()

        ##########################################
        # models saved with app user (if possible)
        ##########################################

        from treemap.tests import make_god_role
        god_role = make_god_role(instance)

        if plot_hashes:
            for plot_hash in plot_hashes:
                try_save_user_hash_to_model(Plot, 'plot', plot_hash,
                                            instance, system_user,
                                            god_role, 'data_owner')

        if tree_hashes:
            for tree_hash in tree_hashes:
                try_save_user_hash_to_model(Tree, 'tree', tree_hash,
                                            instance, system_user,
                                            god_role, 'steward_user')
