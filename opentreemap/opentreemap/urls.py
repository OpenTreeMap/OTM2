from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic import RedirectView

from treemap.views import (user_view, root_settings_js_view,
                           profile_to_user_view)

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Setting permanent=False in case we want to allow customizing favicons
    # per instance in the future
    (r'^favicon\.ico$', RedirectView.as_view(
        url='/static/img/favicon.ico', permanent=False)),
    url(r'^', include('geocode.urls')),
    url(r'^(?P<instance_id>\d+)/', include('treemap.urls')),
    url(r'^(?P<instance_id>\d+)/eco/', include('ecobenefits.urls')),
    url(r'^config/settings.js$', root_settings_js_view),
    url(r'^users/(?P<username>\w+)/', user_view),
    url(r'^api/v2/', include('api.urls')),
    # The profile view is handled specially by redirecting to
    # the page of the currently logged in user
    url(r'^accounts/profile/$', profile_to_user_view),
    url(r'^accounts/', include('registration_backend.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('', url(r'^admin/', include(admin.site.urls)))
