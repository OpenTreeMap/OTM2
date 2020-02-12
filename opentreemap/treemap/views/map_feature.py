# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import datetime
import json
import hashlib
import re
import requests
from functools import wraps

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from django.contrib.gis.geos import Point, MultiPolygon, Polygon
from django.contrib.gis.db.models import GeometryField
from django.utils.translation import ugettext as _

from opentreemap.util import dotted_split
from treemap.lib.hide_at_zoom import (update_hide_at_zoom_after_move,
                                      update_hide_at_zoom_after_delete)

from treemap.units import Convertible
from treemap.models import (Tree, Species, MapFeature,
                            MapFeaturePhoto, TreePhoto, Favorite,
                            INaturalistPhoto, INaturalistObservation)
from treemap.util import (package_field_errors, to_object_name)

from treemap.images import get_image_from_request
from treemap.lib.photo import context_dict_for_photo
from treemap.lib.object_caches import udf_defs
from treemap.lib.map_feature import (get_map_feature_or_404,
                                     raise_non_instance_404,
                                     context_dict_for_plot,
                                     context_dict_for_resource)
from treemap.views.misc import add_map_info_to_context


def _request_to_update_map_feature(request, feature):
    request_dict = json.loads(request.body)
    feature, tree = update_map_feature(request_dict, request.user, feature)

    ctx_fn = (context_dict_for_plot if feature.is_plot
              else context_dict_for_resource)

    return {
        'ok': True,
        'geoRevHash': feature.instance.geo_rev_hash,
        'universalRevHash': feature.instance.universal_rev_hash,
        'featureId': feature.id,
        'treeId': tree.id if tree else None,
        'feature': ctx_fn(request, feature),
        'enabled': feature.instance.feature_enabled('add_plot'),
    }


def _add_map_feature_photo_helper(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    data = get_image_from_request(request)
    photo = feature.add_photo(data, request.user)
    # We must update a rev so that missing photo searches are up to date
    instance.update_universal_rev()
    return photo


def get_photo_context_and_errors(fn):
    @wraps(fn)
    def wrapper(request, instance, feature_id, *args, **kwargs):
        error = None
        try:
            fn(request, instance, feature_id, *args, **kwargs)
        except ValidationError as e:
            error = '; '.join(e.messages)
        feature = get_map_feature_or_404(feature_id, instance)
        photos = feature.photos()
        return {'photos': [context_dict_for_photo(request, photo)
                           for photo in photos],
                'feature': feature,
                'error': error}

    return wrapper


def map_feature_detail(request, instance, feature_id,
                       should_render=False, edit=False):
    context, partial = _map_feature_detail_context(
        request, instance, feature_id, edit)
    add_map_info_to_context(context, instance)

    if should_render:
        template = 'treemap/map_feature_detail.html'
        context['map_feature_partial'] = partial
        latlon = context['feature'].latlon
        context['map_query'] = '?z=%s/%s/%s' % (18, latlon.y, latlon.x)
        return render(request, template, context)
    else:
        return context


def _map_feature_detail_context(request, instance, feature_id, edit=False):
    feature = get_map_feature_or_404(feature_id, instance)
    ctx_fn = (context_dict_for_plot if feature.is_plot
              else context_dict_for_resource)
    context = ctx_fn(request, feature, edit=edit)

    if feature.is_plot:
        partial = 'treemap/partials/plot_detail.html'
        _add_plot_field_groups(context, instance)
    else:
        app = feature.__module__.split('.')[0]
        partial = '%s/%s_detail.html' % (app, feature.feature_type)

    return context, partial


def _add_plot_field_groups(context, instance):
    templates = {
        "tree.id": "treemap/field/tree_id_tr.html",
        "tree.species": "treemap/field/species_tr.html",
        "tree.diameter": "treemap/field/diameter_tr.html"
    }

    labels = {
        # 'plot-species' is used as the "label" in the 'field' tag,
        # but ulitmately gets used as an identifier in the template
        "tree.species": "plot-species",
        "tree.diameter": _("Trunk Diameter")
    }
    labels.update({
        v: k for k, v in context['tree'].scalar_udf_names_and_fields})
    labels.update({
        v: k for k, v in context['plot'].scalar_udf_names_and_fields})

    def info(group):
        group['fields'] = [
            (field, labels.get(field),
             templates.get(field, "treemap/field/tr.html"))
            for field in group.get('field_keys', [])
        ]
        group['collection_udfs'] = [
            next(udf for udf in udf_defs(instance)
                 if udf.full_name == udf_name)
            for udf_name in group.get('collection_udf_keys', [])
        ]

        return group

    context['field_groups'] = [
        info(group) for group in instance.web_detail_fields]


def render_map_feature_detail_partial(request, instance, feature_id, **kwargs):
    context, partial = _map_feature_detail_context(
        request, instance, feature_id)
    return render(request, partial, context)


def render_map_feature_detail(request, instance, feature_id, **kwargs):
    return map_feature_detail(request, instance, feature_id,
                              should_render=True, **kwargs)


def context_map_feature_detail(request, instance, feature_id, **kwargs):
    return map_feature_detail(request, instance, feature_id,
                              should_render=False, **kwargs)


def map_feature_photo_detail(request, instance, feature_id, photo_id):
    feature = get_map_feature_or_404(feature_id, instance)
    photo = get_object_or_404(MapFeaturePhoto, pk=photo_id,
                              map_feature=feature)
    return {'photo': context_dict_for_photo(request, photo)}


def plot_detail(request, instance, feature_id, edit=False, tree_id=None):
    feature = get_map_feature_or_404(feature_id, instance, 'Plot')
    return context_dict_for_plot(request, feature, edit=edit, tree_id=tree_id)


def render_map_feature_add(request, instance, type):
    if type in instance.map_feature_types[1:]:
        app = MapFeature.get_subclass(type).__module__.split('.')[0]
        try:
            template = '%s/%s_add.html' % (app, type)
        except:
            template = 'treemap/resource_add.html'
        return render(request, template, {'object_name': to_object_name(type)})
    else:
        raise_non_instance_404(type)


def add_map_feature(request, instance, type='Plot'):
    if type not in instance.map_feature_types:
        raise_non_instance_404(type)
    feature = MapFeature.get_subclass(type)(instance=instance)
    return _request_to_update_map_feature(request, feature)


def update_map_feature_detail(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    return _request_to_update_map_feature(request, feature)


def delete_map_feature(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    feature.delete_with_user(request.user)  # may raise AuthorizeException
    update_hide_at_zoom_after_delete(feature)
    return {'ok': True}


@transaction.atomic
def update_map_feature(request_dict, user, feature):
    """
    Update a map feature. Expects JSON in the request body to be:
    {'model.field', ...}

    Where model is either 'tree', 'plot', or another map feature type
    and field is any field on the model.
    UDF fields should be prefixed with 'udf:'.

    This method can be used to create a new map feature by passing in
    an empty MapFeature object (i.e. Plot(instance=instance))
    """
    feature_object_names = [to_object_name(ft)
                            for ft in feature.instance.map_feature_types]

    if isinstance(feature, Convertible):
        # We're going to always work in display units here
        feature.convert_to_display_units()

    def value_is_redundant(model, field_name, value):
        # The iOS app sends a key in `data` for every udf definition,
        # even if it hasn't changed.
        # If it is trying to delete a custom field that is not defined
        # for the model, flag it as redundant,
        # to avoid a `KeyError` when the update tries to delete them.
        if field_name.startswith('udf:') and \
                value in [[], '[]', '', None]:
            udf_name = field_name.replace('udf:', '')
            if udf_name not in model.udfs:
                return True
        return False

    def set_attr_on_model(model, attr, val):
        field_classname = \
            model._meta.get_field(attr).__class__.__name__

        if field_classname.endswith('PointField'):
            srid = val.get('srid', 3857)
            val = Point(val['x'], val['y'], srid=srid)
            val.transform(3857)
        elif field_classname.endswith('MultiPolygonField'):
            srid = val.get('srid', 4326)
            val = MultiPolygon(Polygon(val['polygon'], srid=srid), srid=srid)
            val.transform(3857)

        if attr == 'mapfeature_ptr':
            if model.mapfeature_ptr_id != value:
                raise Exception(
                    'You may not change the mapfeature_ptr_id')
        elif attr == 'id':
            if val != model.pk:
                raise Exception("Can't update id attribute")
        elif attr.startswith('udf:'):
            udf_name = attr[4:]

            if udf_name in [field.name
                            for field
                            in model.get_user_defined_fields()]:
                model.udfs[udf_name] = val
            else:
                raise KeyError('Invalid UDF %s' % attr)
        elif attr in model.fields():
            model.apply_change(attr, val)
        else:
            raise Exception('Malformed request - invalid field %s' % attr)

    def save_and_return_errors(thing, user):
        try:
            if isinstance(thing, Convertible):
                thing.convert_to_database_units()

            thing.save_with_user(user)
            return {}
        except ValidationError as e:
            return package_field_errors(thing._model_name, e)

    def skip_setting_value_on_tree(value, tree):
        # If the tree is not None, we always set a value.  If the tree
        # is None (meaning that we would be creating a new Tree
        # object) then we only want to set a value if the value is
        # non-empty.
        return (tree is None) and (value in ([], '[]', '', None))

    tree = None
    errors = {}

    rev_updates = ['universal_rev']
    old_geom = feature.geom
    for (identifier, value) in request_dict.iteritems():
        split_template = 'Malformed request - invalid field %s'
        object_name, field = dotted_split(identifier, 2,
                                          failure_format_string=split_template)
        if (object_name not in feature_object_names + ['tree']):
            raise ValueError(split_template % identifier)

        if (object_name == 'tree'
            and skip_setting_value_on_tree(
                value, feature.safe_get_current_tree())):
            continue
        elif object_name in feature_object_names:
            model = feature
        elif object_name == 'tree' and feature.feature_type == 'Plot':
            # Get the tree or spawn a new one if needed
            tree = (tree or
                    feature.safe_get_current_tree() or
                    Tree(instance=feature.instance))

            # We always edit in display units
            tree.convert_to_display_units()

            model = tree
            if field == 'species' and value:
                value = get_object_or_404(Species,
                                          instance=feature.instance, pk=value)
            elif field == 'plot' and value == unicode(feature.pk):
                value = feature
        else:
            raise ValueError(
                'Malformed request - invalid model %s' % object_name)

        if not value_is_redundant(model, field, value):
            set_attr_on_model(model, field, value)

        field_class = model._meta.get_field(field)
        if isinstance(field_class, GeometryField):
            rev_updates.append('geo_rev')
            rev_updates.append('eco_rev')
        elif identifier in ['tree.species', 'tree.diameter']:
            rev_updates.append('eco_rev')

    if feature.fields_were_updated():
        errors.update(save_and_return_errors(feature, user))
    if tree and tree.fields_were_updated():
        tree.plot = feature
        errors.update(save_and_return_errors(tree, user))

    if errors:
        # It simplifies the templates and client-side logic if the geometry
        # field errors are returned under the generic name
        if feature.geom_field_name in errors:
            errors['mapFeature.geom'] = errors[feature.geom_field_name]
        raise ValidationError(errors)

    if old_geom is not None and feature.geom != old_geom:
        update_hide_at_zoom_after_move(feature, user, old_geom)

    feature.instance.update_revs(*rev_updates)

    return feature, tree


def map_feature_hash(request, instance, feature_id, edit=False, tree_id=None):
    """
    Compute a unique hash for a given plot or tree

    tree_id is ignored since trees are included as a
    subset of the plot's hash. It is present here because
    this function is wrapped around views that can take
    tree_id as an argument
    """
    feature = get_map_feature_or_404(feature_id, instance)

    if request.user:
        pk = request.user.pk or ''

    return hashlib.md5(feature.hash + ':' + str(pk)).hexdigest()


@get_photo_context_and_errors
def add_map_feature_photo(request, instance, feature_id):
    _add_map_feature_photo_helper(request, instance, feature_id)


@get_photo_context_and_errors
def rotate_map_feature_photo(request, instance, feature_id, photo_id):
    orientation = request.POST.get('degrees', None)
    if orientation not in {'90', '180', '270', '-90', '-180', '-270'}:
        raise ValidationError('"degrees" must be a multiple of 90°')

    degrees = int(orientation)
    feature = get_map_feature_or_404(feature_id, instance)
    mf_photo = get_object_or_404(MapFeaturePhoto,
                                 pk=photo_id,
                                 map_feature=feature)

    image_data = mf_photo.image.read(settings.MAXIMUM_IMAGE_SIZE)
    mf_photo.set_image(image_data, degrees_to_rotate=degrees)
    mf_photo.save_with_user(request.user)


@get_photo_context_and_errors
def delete_photo(request, instance, feature_id, photo_id):
    feature = get_map_feature_or_404(feature_id, instance)
    photo_class = TreePhoto if feature.is_plot else MapFeaturePhoto
    mf_photo = get_object_or_404(photo_class, pk=photo_id, map_feature=feature)
    mf_photo.delete_with_user(request.user)  # may raise AuthorizeException


def map_feature_popup(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    context = {}
    context['features'] = [feature] + list(feature.nearby_map_features())
    if instance.canopy_enabled:
        context['boundaries_with_canopy'] = \
            _get_boundaries_with_canopy(instance, feature.geom)
    return context


def canopy_popup(request, instance):
    if instance.canopy_enabled:
        lng = request.GET['lng']
        lat = request.GET['lat']
        point = Point(float(lng), float(lat), srid=4326)
        result = _get_boundaries_with_canopy(instance, point)
        if result:
            return render(request, 'treemap/partials/canopy_popup.html',
                          {'boundaries_with_canopy': result})
    return HttpResponse('')


def _get_boundaries_with_canopy(instance, point):
    boundaries = instance.boundaries \
        .filter(geom__contains=point) \
        .exclude(canopy_percent__isnull=True) \
        .order_by('-sort_order')
    for boundary in boundaries:
        boundary.canopy_percent *= 100
    return boundaries


def favorite_map_feature(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    Favorite.objects.get_or_create(user=request.user, map_feature=feature)

    return {'success': True}


def unfavorite_map_feature(request, instance, feature_id):
    feature = get_map_feature_or_404(feature_id, instance)
    Favorite.objects.filter(user=request.user, map_feature=feature).delete()

    return {'success': True}


def inaturalist(request, *args, **kwargs):
    """
    """
    base_url = "https://www.inaturalist.org"

    app_id = 'db6db69ef86d5a21a4c9876bcaebad059db3b1ed90f30255c6d9e8bdaebf0513';
    app_secret = '19bcad3978b02e2f79fc7723bbd295a3c95f60f6246b99a3f751f21407bd6095';
    code = request.GET['code']
    redirect_uri = request.META['HTTP_REFERER']

    # to build up the redirect url
    #request.path
    #request.is_secure()
    #request.get_host()

    payload = {
        'client_id': app_id,
        'client_secret': app_secret,
        'code': code,
        'redirect_uri': 'http://localhost:7070/jerseycity/inaturalist/',
        'grant_type': 'authorization_code'
    }

    r = requests.post(
        url="{base_url}/oauth/token".format(base_url=base_url),
        data=payload
    )
    request.session['inaturalist_token'] = r.json()['access_token']
    import ipdb; ipdb.set_trace() # BREAKPOINT

    return HttpResponseRedirect(redirect_uri)


def get_photo_id_from_photo_detail_url(url, feature_id):
    """
    """
    return int(re.match(r'.*/{}/photo/(\d+)/detail'.format(feature_id), url).groups()[0])


def create_observation(token, latitude, longitude):
    """
    """
    base_url = "https://www.inaturalist.org"
    headers = {'Authorization': 'Bearer {}'.format(token)}
    params = {'observation': {
            'observed_on_string': datetime.datetime.now().isoformat(),
            'latitude': latitude,
            'longitude': longitude
        }
    }

    response = requests.post(
        url="{base_url}/observations.json".format(base_url=base_url),
        json=params,
        headers=headers
    )
    '''
    return {
        u'cached_votes_total': 0,
        u'captive': False,
        u'comments_count': 0,
        u'community_taxon_id': None,
        u'created_at': u'2020-01-07T22:04:44.757-05:00',
        u'created_at_utc': u'2020-01-08T03:04:44.757Z',
        u'delta': False,
        u'description': None,
        u'faves_count': 0,
        u'geoprivacy': None,
        u'iconic_taxon_id': None,
        u'iconic_taxon_name': None,
        u'id': 37388076,
        u'id_please': False,
        u'identifications_count': 0,
        u'last_indexed_at': u'2020-01-07T19:04:49.322-08:00',
        u'latitude': u'40.7083055556',
        u'license': u'CC-BY-NC',
        u'location_is_exact': False,
        u'longitude': u'-74.0893888889',
        u'map_scale': None,
        u'mappable': True,
        u'num_identification_agreements': 0,
        u'num_identification_disagreements': 0,
        u'oauth_application_id': 385,
        u'observation_photos_count': 0,
        u'observation_sounds_count': 0,
        u'observed_on': u'2020-01-07',
        u'observed_on_string': u'2020-01-07T21:04:44.393925',
        u'old_uuid': None,
        u'out_of_range': None,
        u'owners_identification_from_vision': None,
        u'place_guess': u'Hudson County, US-NJ, US',
        u'positional_accuracy': None,
        u'positioning_device': None,
        u'positioning_method': None,
        u'private_latitude': None,
        u'private_longitude': None,
        u'private_place_guess': None,
        u'private_positional_accuracy': None,
        u'project_observations': [],
        u'public_positional_accuracy': None,
        u'quality_grade': u'casual',
        u'site_id': 1,
        u'species_guess': None,
        u'taxon_geoprivacy': None,
        u'taxon_id': None,
        u'time_observed_at': u'2020-01-07T21:04:44.000-05:00',
        u'time_observed_at_utc': u'2020-01-08T02:04:44.000Z',
        u'time_zone': u'America/New_York',
        u'timeframe': None,
        u'updated_at': u'2020-01-07T22:04:44.757-05:00',
        u'updated_at_utc': u'2020-01-08T03:04:44.757Z',
        u'uri': None,
        u'user_id': 2384052,
        u'user_login': u'tzinckgraf',
        u'uuid': u'0e26bafc-bd23-48d0-9bda-806450093c88',
        u'zic_time_zone': None
    }
    '''
    return response.json()[0]


def add_photo_to_observation(token, observation_id, photo):
    base_url = "https://www.inaturalist.org"
    headers = {'Authorization': 'Bearer {}'.format(token)}
    data = {'observation_photo[observation_id]': observation_id}
    file_data = {'file': photo.image.file.file}

    response = requests.post(
        url="{base_url}/observation_photos".format(base_url=base_url),
        headers=headers,
        data=data,
        files=file_data
    )
    '''
    return {
        u'created_at': u'2020-01-07T22:17:04.531-05:00',
        u'created_at_utc': u'2020-01-08T03:17:04.531Z',
        u'id': 54883602,
        u'observation_id': 37388076,
        u'old_uuid': None,
        u'photo': {u'attribution': u'(c) Thomas Zinckgraf, some rights reserved (CC BY-NC)',
                    u'created_at': u'2020-01-07T22:17:02.709-05:00',
                    u'id': 59263063,
                    u'large_url': None,
                    u'license': 2,
                    u'license_name': u'Creative Commons Attribution-NonCommercial License',
                    u'license_url': u'http://creativecommons.org/licenses/by-nc/4.0/',
                    u'medium_url': None,
                    u'native_original_image_url': None,
                    u'native_page_url': None,
                    u'native_photo_id': u'59263063',
                    u'native_realname': u'Thomas Zinckgraf',
                    u'native_username': u'tzinckgraf',
                    u'small_url': None,
                    u'square_url': None,
                    u'subtype': None,
                    u'thumb_url': None,
                    u'type': u'LocalPhoto',
                    u'updated_at': u'2020-01-07T22:17:02.709-05:00',
                    u'user_id': 2384052},
        u'photo_id': 59263063,
        u'position': None,
        u'updated_at': u'2020-01-07T22:17:04.531-05:00',
        u'updated_at_utc': u'2020-01-08T03:17:04.531Z',
        u'uuid': u'db6b5a49-eb92-4b12-8d3f-83f388ac55f0'}
    '''


def inaturalist_add(request, instance, *args, **kwargs):
    try:
        token = request.session['inaturalist_token']
    except KeyError:
        return {'success': False}

    # INaturalistPhoto, INaturalistObservation

    body = json.loads(request.body)
    feature_id = body['featureId']
    feature = get_map_feature_or_404(feature_id, instance)
    tree = feature.safe_get_current_tree()
    photo_id = get_photo_id_from_photo_detail_url(body['photoDetailUrl'], feature_id)
    photo_class = TreePhoto if feature.is_plot else MapFeaturePhoto
    photo = get_object_or_404(photo_class, pk=photo_id, map_feature=feature)

    (longitude, latitude) = feature.latlon.coords

    observation = create_observation(token, latitude, longitude)
    photo_info = add_photo_to_observation(token, observation['id'], photo)

    import ipdb; ipdb.set_trace() # BREAKPOINT
    return {'success': True}
