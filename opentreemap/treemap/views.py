from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import urllib

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseServerError

from django.views.decorators.http import etag

from django.conf import settings

from treemap.util import json_api_call, render_template, instance_request

from treemap.search import create_filter

from treemap.audit import Audit, AuditUI
from treemap.models import Plot, Tree, User, Boundary, Species

from ecobenefits.views import _benefits_for_tree_dbh_and_species


def _plot_hash(request, instance, plot_id):
    return instance.scope_model(Plot).get(pk=plot_id).hash


def plot_detail(request, instance, plot_id):
    InstancePlot = instance.scope_model(Plot)
    plot = get_object_or_404(InstancePlot, pk=plot_id)

    return {'plot': plot}


def audits(request, instance):
    """
    Request a variety of different audit types.
    Params:
       - models
         Comma separated list of models (only Tree and Plot are supported)
       - model_id
         The ID of a specfici model. If specified, models must also
         be defined and have only one model

       - user
         Filter by a specific user

       - include_pending (default: true)
         Set to false to ignore edits that are currently pending

       - page_size
         Size of each page to return (up to PAGE_MAX)
       - page
         The page to return
    """

    PAGE_MAX = 100
    PAGE_DEFAULT = 20

    r = request.REQUEST

    page_size = min(int(r.get('page_size', PAGE_DEFAULT)), PAGE_MAX)
    page = int(r.get('page', 0))

    start_pos = page * page_size
    end_pos = start_pos + page_size

    models = []

    allowed_models = {
        'tree': 'Tree',
        'plot': 'Plot'
    }

    for model in r.get('models', "tree,plot").split(','):
        if model.lower() in allowed_models:
            models.append(allowed_models[model.lower()])
        else:
            raise Exception("Invalid model: %s" % model)

    model_id = r.get('model_id', None)

    if model_id is not None and len(models) != 1:
        raise Exception("You must specific one and only model "
                        "when looking up by id")

    user_id = r.get('user', None)
    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)

    audits = Audit.objects.filter(instance=instance)\
                          .filter(model__in=models)\
                          .order_by('-created', 'id')

    if user_id:
        audits = audits.filter(user=user)

    if model_id:
        audits = audits.filter(model_id=model_id)

    if r.get('include_pending', "true") == "false":
        audits = audits.exclude(requires_auth=True, ref_id__isnull=True)

    audits = [AuditUI(a) for a in audits[start_pos:end_pos]]

    query_vars = {k: v for (k, v) in request.GET.iteritems() if k != 'page'}

    next_page = None
    prev_page = None

    if len(audits) == page_size:
        query_vars['page'] = page + 1
        next_page = "?" + urllib.urlencode(query_vars)

    if page > 0:
        query_vars['page'] = page - 1
        prev_page = "?" + urllib.urlencode(query_vars)

    return {'audits': audits,
            'next_page': next_page,
            'prev_page': prev_page}


def boundary_to_geojson(request, boundary_id):
    boundary = Boundary.objects.get(pk=boundary_id)
    return HttpResponse(boundary.geom.geojson)


def boundary_autocomplete(request, instance):
    query = request.GET.get('q', '')
    max_items = request.GET.get('max_items', 10)

    boundaries = instance.boundaries\
                         .filter(name__startswith=query)\
                         .order_by('name')[:max_items]

    return [{'name': boundary.name, 'category': boundary.category}
            for boundary in boundaries]


def species_list(request, instance):
    species_set = Species.objects.order_by('common_name')

    return [{'common_name': species.common_name,
             'id': species.pk,
             'scientific_name': species.scientific_name}
            for species in species_set]


def _execute_filter(instance, filter_str):
    return create_filter(filter_str).filter(instance=instance)


def search_tree_benefits(request, instance, region='SoCalCSMA'):
    try:
        filter_str = request.REQUEST['q']
    except KeyError:
        return HttpResponseServerError("Please supply a 'filter' parameter")

    plots = _execute_filter(instance, filter_str)
    trees = Tree.objects.filter(plot_id__in=plots)

    num_calculated_trees = 0

    benefits = {'energy': 0.0, 'stormwater': 0.0,
                'co2': 0.0, 'airquality': 0.0}

    total_plots = plots.count()
    total_trees = trees.count()

    trees_for_eco = trees.exclude(species__isnull=True)\
                         .exclude(diameter__isnull=True)

    for tree in trees_for_eco:
        if tree.diameter and tree.species:
            tree_benefits = _benefits_for_tree_dbh_and_species(
                tree.diameter, tree.species, region)

            if tree_benefits:
                for key in benefits:
                    benefits[key] = tree_benefits[key]['value']

                    num_calculated_trees += 1

    if num_calculated_trees > 0 and total_trees > 0:

        # Extrapolate an average over the rest of the urban forest
        trees_without_benefit_data = total_trees - num_calculated_trees
        for benefit in benefits:
            avg_benefit = benefits[benefit] / num_calculated_trees
            extrp_benefit = avg_benefit * trees_without_benefit_data

            benefits[benefit] += extrp_benefit

        rslt = {'benefits': benefits,
                'basis': {'n_calc': num_calculated_trees,
                          'n_total_trees': total_trees,
                          'n_total_plots': total_plots,
                          'percent': (float(num_calculated_trees) /
                                      total_trees)}}
    else:
        rslt = {'benefits': benefits,
                'basis': {'n_calc': num_calculated_trees,
                          'n_total_trees': total_trees,
                          'n_total_plots': total_plots,
                          'percent': 0}}

    return rslt


audits_view = instance_request(
    render_template('treemap/recent_edits.html', audits))

index_view = instance_request(render_template('treemap/index.html'))
trees_view = instance_request(
    render_template('treemap/map.html',
                    {'bounds': Boundary.objects.all(),
                     'species': Species.objects.all()}))

plot_detail_view = instance_request(etag(_plot_hash)(
    render_template('treemap/plot_detail.html', plot_detail)))

settings_js_view = instance_request(
    render_template('treemap/settings.js',
                    {'BING_API_KEY': settings.BING_API_KEY},
                    mimetype='application/x-javascript'))


boundary_to_geojson_view = json_api_call(boundary_to_geojson)
boundary_autocomplete_view = instance_request(
    json_api_call(boundary_autocomplete))

search_tree_benefits_view = instance_request(
    json_api_call(search_tree_benefits))

species_list_view = json_api_call(instance_request(species_list))
