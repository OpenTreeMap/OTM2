"use strict";

// For modal dialog on jquery
require('bootstrap');

var $ = require('jquery'),
    _ = require('underscore'),
    otmTypeahead = require('./otmTypeahead'),  // Override typeahead from bootstrap
    inlineEditForm = require('./inlineEditForm'),
    mapManager = require('./mapManager'),
    plotMover = require('./plotMover'),
    plotMarker = require('./plotMarker');

function addModalTrigger(element) {
    var $e = $(element);
    var $target = $($e.data('modal'));

    $e.click(function() {
        $target.modal('toggle');
    });
}

exports.init = function(options) {
    _.each(options.typeaheads, function(typeahead) {
        otmTypeahead.create(typeahead);
    });

    addModalTrigger(options.photos.show);
    var $form = $(options.photos.form);
    $(options.photos.upload).click(function() { $form.submit(); });
    
    inlineEditForm.init(
        _.extend(options.inlineEditForm, { onSaveBefore: onSaveBefore }));

    mapManager.init({
        config: options.config,
        selector: '#map',
        center: options.plotLocation.location,
        zoom: mapManager.ZOOM_PLOT
    });

    plotMarker.init(mapManager.map);

    plotMover.init({
        mapManager: mapManager,
        plotMarker: plotMarker,
        inlineEditForm: inlineEditForm,
        editLocationButton: options.plotLocation.edit,
        cancelEditLocationButton: options.plotLocation.cancel,
        location: options.plotLocation.location
    });

    function onSaveBefore(data) {
        plotMover.onSaveBefore(data);
    }
};
