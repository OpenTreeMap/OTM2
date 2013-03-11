from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from django.conf import settings
from treemap.models import Instance, Tree
from functools import wraps

class InvalidInstanceException(Exception):
    pass

def instance_request(view_fn):
    @wraps(view_fn)
    def wrapper(request, instance_id, *args, **kwargs):
        request.instance = get_object_or_404(Instance, pk=instance_id)
        return view_fn(request, *args, **kwargs)

    return wrapper

@instance_request
def index(request):
    return render_to_response('treemap/index.html',RequestContext(request))

@instance_request
def trees(request):
    return render_to_response('treemap/map.html',RequestContext(request))

@instance_request
def tree_detail(request, tree_id):
    tree = get_object_or_404(Tree, pk=tree_id)
    return render_to_response('treemap/tree_detail.html',RequestContext(request))

@instance_request
def settings_js(request):
    return render_to_response('treemap/settings.js', 
                              { 'BING_API_KEY': settings.BING_API_KEY },
                              RequestContext(request),
                              mimetype='application/x-javascript')
