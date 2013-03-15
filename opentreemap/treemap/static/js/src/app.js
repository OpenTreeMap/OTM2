/* app.js */

//= require OpenLayers

/*globals $,OpenLayers,otm,document*/
/*jslint indent: 4, white: true */

var app = (function ($,OL,config) {
    "use strict";
    return {
        createMap: function (elmt) {
            var map = new OL.Map({
                div: elmt,
                projection: 'EPSG:3857',
                layers: this.getBasemapLayers(config)
            });

            map.setCenter(config.instance.center, 10);

            return map;
        },

        getBasemapLayers: function (config) {
            var layer;
            if (config.instance.basemap.type === 'bing') {
                layer = new OL.Layer.Bing({
                    name: 'Road',
                    key: config.instance.basemap.bing_api_key,
                    type: 'Road'
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
                extension;
        },

        createPlotTileLayer: function(config) {
            return new OL.Layer.XYZ(
                'tiles',
                this.getPlotLayerURL(config, 'png'),
            { isBaseLayer: false });

        },

        createPlotUTFLayer: function(config) {
            return new OL.Layer.UTFGrid({
                url: this.getPlotLayerURL(config, 'grid.json') +
                    '?interactivity=id',
                utfgridResolution: 4
            });
        },

        /**
         * Create a new utf movement control bound to all
         * utf layers.
         *
         * @param renderfn A single argument function
         *                 that takes in a hash of the last
         *                 point or 'undefined' if the mouse
         *                 isn't over a point
         */
        createUTFMovementControl: function(renderfn) {
            return new OL.Control.UTFGrid({
                callback: function(info) {
                    var idx, props;
                    for(idx in info) {
                        if (info.hasOwnProperty(idx)) {
                            props = info[idx] || {};
                            renderfn(props.data);
                        }
                    }
                },

                handlerMode: "move"
            });
        },

        onMove: function(data) {
            document.getElementById("attrs").innerHTML = JSON.stringify(data || {});
        },

        init: function () {
            var map = app.createMap($("#map")[0]),
                plotLayer = app.createPlotTileLayer(config),
                utfLayer = app.createPlotUTFLayer(config);

            map.addLayer(plotLayer);
            map.addLayer(utfLayer);

            map.addControl(app.createUTFMovementControl(app.onMove));
        }
    };
}($, OpenLayers, otm.settings));
