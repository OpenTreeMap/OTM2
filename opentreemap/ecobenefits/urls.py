from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.conf.urls import patterns, include, url

from ecobenefits.views import tree_benefits, group_tree_benefits

urlpatterns = patterns(
    '',
    url(r'^benefit/tree/(?P<tree_id>\d+)/$', tree_benefits),
    url(r'^benefit/search$', group_tree_benefits)
)
