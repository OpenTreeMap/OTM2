{% load instance_config %}
{% load i18n %}

// Data structures pulled from django
var otm = otm || {};
otm.settings = otm.settings || {};

otm.settings.utfGrid = {
    plotIdKey: 'the_plot_id'
}

otm.settings.urls = {
    'filterQueryArgumentName': 'q'
}

{% if not settings.TILE_HOST = None %}
    otm.settings.tileHost = "{{ settings.TILE_HOST }}";
{% endif %}

{% if request.user.is_authenticated %}
    otm.settings.loggedIn = true;
{% else %}
    otm.settings.loggedIn = false;
{% endif %}

otm.settings.loginUrl = "{% url 'django.contrib.auth.views.login' %}?next=";

otm.settings.staticUrl = '{{ STATIC_URL }}';

otm.settings.geocoder = {
    maxLocations: 20,
    errorString: '{% trans "That address was not found near this map" %}',
    threshold: 80
};

{% if request.instance %}
    otm.settings.instance = {
        'id': '{{ request.instance.id }}',
        'url': '{{ SITE_ROOT }}{{ request.instance.url_name }}/',
        'name': '{{ request.instance.name }}',
        'rev': '{{ request.instance.geo_rev_hash }}',
        'center': {
            'x': '{{ request.instance.center.x }}',
            'y': '{{ request.instance.center.y }}'
        },
        'extent': {{ request.instance.extent_as_json|safe }},
        'basemap': {
            'type': '{{ request.instance.basemap_type }}',
            'data': '{{ request.instance.basemap_data }}',
            'bing_api_key': '{{ BING_API_KEY }}'
        },
        'primaryColor': '{{ request.instance.config|primary_color }}',
        'secondaryColor': '{{ request.instance.config|secondary_color }}'
    }
{% endif %}
