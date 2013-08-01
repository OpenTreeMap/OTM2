"use strict";

var $ = require('jquery'),
    _ = require('underscore'),
    OL = require('OpenLayers'),
    Bacon = require('baconjs'),

    Search = require('./search'),
    otmTypeahead = require('./otm.typeahead'),
    makeLayerFilterable = require('./makeLayerFilterable');

// These modules add features to the OpenLayers global
// so we do not need `var thing =`
require('./openLayersUtfGridEventStream');
require('./openLayersMapEventStream');

$.extend($.fn, Bacon.$);

/* BEGIN BACON HELPERS */

function keyCodeIs(keyCode) {
    return function(event) { return event.which === keyCode; };
}

var isEnterKey = keyCodeIs(13);

var truthyOrError = function (value) {
    return !!value ? value : Bacon.Error('The value ' + value + ' is not truthy');
};

/* END BACON HELPERS */

var app = {
    createMap: function (elmt, config) {
        var map = new OL.Map({
            theme: null,
            div: elmt,
            projection: 'EPSG:3857',
            layers: this.getBasemapLayers(config)
        });

        return map;
    },

    getBasemapLayers: function (config) {
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
    },

    getPlotLayerURL: function(config, extension) {
        return '/tile/' +
            config.instance.rev +
            '/database/otm/table/treemap_plot/${z}/${x}/${y}.' +
            extension + '?instance_id=' + config.instance.id;
    },

    createPlotTileLayer: function (config) {
        var url = this.getPlotLayerURL(config, 'png'),
            layer = new OL.Layer.XYZ(
                'tiles',
                url,
                { isBaseLayer: false,
                  sphericalMercator: true });
        makeLayerFilterable(layer, url, config.urls.filterQueryArgumentName);
        return layer;
    },

    createPlotUTFLayer: function (config) {
        var url = this.getPlotLayerURL(config, 'grid.json'),
            layer = new OL.Layer.UTFGrid({
                url: url,
                utfgridResolution: 4
            });
        makeLayerFilterable(layer, url, config.urls.filterQueryArgumentName);
        return layer;
    },

    getBoundsLayerURL: function(config, extension) {
        return '/tile/' +
            config.instance.rev +
            '/database/otm/table/treemap_boundary/${z}/${x}/${y}.' +
            extension + '?instance_id=' + config.instance.id;
    },

    createBoundsTileLayer: function (config) {
        return new OL.Layer.XYZ(
            'bounds',
            this.getBoundsLayerURL(config, 'png'),
            { isBaseLayer: false,
              sphericalMercator: true });
    },

    getPlotPopupContent: function(config, id) {
        var search = $.ajax({
            url: '/' + config.instance.id + '/plots/' + id + '/',
            type: 'GET',
            dataType: 'html'
        });
        return Bacon.fromPromise(search);
    },

    makePopup: function(latLon, html, size) {
        if (latLon && html) {
            return new OL.Popup("plot-popup", latLon, size, html, true);
        } else {
            return null;
        }
    }
};

module.exports = {
    init: function (config) {
        var map = app.createMap($("#map")[0], config),
            plotLayer = app.createPlotTileLayer(config),
            boundsLayer = app.createBoundsTileLayer(config),
            utfLayer = app.createPlotUTFLayer(config),
            zoom = 0,

            enterKeyPressStream = $('input[data-class="search"]')
                .asEventStream("keyup")
                .filter(isEnterKey),

            performSearchClickStream = $("#perform-search")
                .asEventStream("click"),

            triggerEventStream = enterKeyPressStream.merge(performSearchClickStream);

        // Bing maps uses a 1-based zoom so XYZ layers
        // on the base map have a zoom offset that is
        // always one less than the map zoom:
        // > map.setCenter(center, 11)
        // > map.zoom
        //   12
        // So this forces the tile requests to use
        // the correct Z offset
        if (config.instance.basemap.type === 'bing') {
            plotLayer.zoomOffset = 1;
            utfLayer.zoomOffset = 1;
        }

        map.addLayer(plotLayer);
        map.addLayer(utfLayer);
        map.addLayer(boundsLayer);

        var utfGridMoveControl = new OL.Control.UTFGrid();

        utfGridMoveControl
            .asEventStream('move')
            .map(function (o) { return JSON.stringify(o || {}); })
            .assign($('#attrs'), 'html');

        // The control must be added to the map after setting up the
        // event stream
        map.addControl(utfGridMoveControl);

        var utfGridClickControl = new OL.Control.UTFGrid();

        var clickedIdStream = utfGridClickControl
            .asEventStream('click')
            .map('.' + config.utfGrid.plotIdKey);

        var popupHtmlStream = clickedIdStream
            .map(truthyOrError) // Prevents making requests if id is undefined
            .flatMap(_.bind(app.getPlotPopupContent, app, config))
            .mapError(''); // No id or a server error both result in no content

        // The control must be added to the map after setting up the
        // event streams
        map.addControl(utfGridClickControl);

        var showPlotDetailPopup = (function(map) {
            var existingPopup;
            return function(popup) {
                if (existingPopup) { map.removePopup(existingPopup); }
                if (popup) { map.addPopup(popup); }
                existingPopup = popup;
            };
        }(map));

        var clickedLatLonStream = map.asEventStream('click').map(function (e) {
            return map.getLonLatFromPixel(e.xy);
        });

        // OpenLayers needs both the content and a coordinate to
        // show a popup so I zip map clicks together with content
        // requested via ajax
        clickedLatLonStream
            .zip(popupHtmlStream, app.makePopup) // TODO: size is not being sent to makePopup
            .onValue(showPlotDetailPopup);

        zoom = map.getZoomForResolution(76.43702827453613);
        map.setCenter(config.instance.center, zoom);

        Search.init(triggerEventStream, config, function (filter) {
            plotLayer.setFilter(filter);
            utfLayer.setFilter(filter);
        });

        otmTypeahead.create({
            name: "species",
            url: "/" + config.instance.id + "/species",
            input: "#species-typeahead",
            template: "#species-element-template",
            hidden: "#search-species"
        });
        otmTypeahead.create({
            name: "boundaries",
            url: "/" + config.instance.id + "/boundaries",
            input: "#boundary-typeahead",
            template: "#boundary-element-template",
            hidden: "#boundary"
        });
    }
};
