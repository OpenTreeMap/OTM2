"use strict";

var $ = require('jquery'),
    _ = require('underscore'),
    OL = require('OpenLayers'),
    makeLayerFilterable = require('./makeLayerFilterable');

exports.ZOOM_DEFAULT = 11;
exports.ZOOM_PLOT = 18;

exports.init = function(options) {
    var config = options.config,
        map = createMap($(options.selector)[0], config),
        plotLayer = createPlotTileLayer(config),
        boundsLayer = createBoundsTileLayer(config),
        utfLayer = createPlotUTFLayer(config);

    exports.map = map;

    exports.updateGeoRevHash = function(geoRevHash) {
        if (geoRevHash !== config.instance.rev) {
            config.instance.rev = geoRevHash;
            plotLayer.url = getPlotLayerURL(config, 'png');
            utfLayer.url = getPlotLayerURL(config, 'grid.json');
            plotLayer.redraw({force: true});
            utfLayer.redraw({force: true});
        }
    };

    exports.setFilter = function (filter) {
        plotLayer.setFilter(filter);
        utfLayer.setFilter(filter);
    };

    exports.setCenterAndZoomIn = function(location, zoom) {
        map.setCenter(new OL.LonLat(location.x, location.y),
                      Math.max(map.getZoom(), zoom));
    };

    // Bing maps uses a 1-based zoom so XYZ layers on the base map have
    // a zoom offset that is always one less than the map zoom:
    // > map.setCenter(center, 11)
    // > map.zoom
    //   12
    // So this forces the tile requests to use the correct Z offset
    if (config.instance.basemap.type === 'bing') {
        plotLayer.zoomOffset = 1;
        utfLayer.zoomOffset = 1;
    }

    map.addLayer(plotLayer);
    map.addLayer(utfLayer);
    map.addLayer(boundsLayer);

    var center = options.center || config.instance.center,
        zoom = options.zoom || exports.ZOOM_DEFAULT;
    map.setCenter(new OL.LonLat(center.x, center.y), zoom);
};

function createMap(elmt, config) {
    var map = new OL.Map({
        theme: null,
        div: elmt,
        projection: 'EPSG:3857',
        layers: getBasemapLayers(config)
    });

    return map;
}

function getBasemapLayers(config) {
    var layer;
    if (config.instance.basemap.type === 'bing') {
        layer = new OL.Layer.Bing({
            name: 'Road',
            key: config.instance.basemap.bing_api_key,
            type: 'Road',
            isBaseLayer: true
        });
    } else if (config.instance.basemap.type === 'tms') {
        layer = new OL.Layer.XYZ(
            'xyz',
            config.instance.basemap.data);
    } else {
        layer = new OL.Layer.Google(
            "Google Streets",
            {numZoomLevels: 20});
    }
    return [layer];
}

function createPlotTileLayer(config) {
    var url = getPlotLayerURL(config, 'png'),
        layer = new OL.Layer.XYZ(
            'tiles',
            url,
            { isBaseLayer: false,
              sphericalMercator: true });
    makeLayerFilterable(layer, url, config.urls.filterQueryArgumentName);
    return layer;
}

function createPlotUTFLayer(config) {
    var url = getPlotLayerURL(config, 'grid.json'),
        layer = new OL.Layer.UTFGrid({
            url: url,
            utfgridResolution: 4
        });
    makeLayerFilterable(layer, url, config.urls.filterQueryArgumentName);
    return layer;
}

// The ``url`` property of the OpenLayers XYZ layer supports a single
// string or an array of strings. ``getPlotLayerURL`` looks at
// ``config.tileHosts`` and returns a single string if only one host
// is defined, or an array of strings if multiple hosts are defined.
function getPlotLayerURL(config, extension) {
    var urls = [],
        // Using an array with a single undefined element when
        // ``config.tileHosts`` is falsy allows us to always
        // use an ``_.each`` loop to generate the url string,
        // simplifying the code path
        hosts = config.tileHosts || [undefined];
    _.each(hosts, function(host) {
        var prefix = host ? '//' + host : '';
        urls.push(prefix + '/tile/' +
        config.instance.rev +
        '/database/otm/table/treemap_plot/${z}/${x}/${y}.' +
        extension + '?instance_id=' + config.instance.id);
    });
    return urls.length === 1 ? urls[0] : urls;
}

function createBoundsTileLayer(config) {
    return new OL.Layer.XYZ(
        'bounds',
        getBoundsLayerURL(config, 'png'),
        { isBaseLayer: false,
          sphericalMercator: true });
}

function getBoundsLayerURL(config, extension) {
    return '/tile/' +
        config.instance.rev +
        '/database/otm/table/treemap_boundary/${z}/${x}/${y}.' +
        extension + '?instance_id=' + config.instance.id;
}
