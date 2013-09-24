"use strict";

var $ = require('jquery'),
    _ = require('underscore'),
    otmTypeahead = require('./otmTypeahead'),  // Override typeahead from bootstrap
    inlineEditForm = require('./inlineEditForm'),
    mapManager = require('./mapManager'),
    plotMover = require('./plotMover'),
    plotMarker = require('./plotMarker'),
    csrf = require('./csrf'),
    imageUploadPanel = require('./imageUploadPanel');

exports.init = function(options) {
    // Set up cross-site forgery protection
    $.ajaxSetup(csrf.jqueryAjaxSetupOptions);

    _.each(options.typeaheads, function(typeahead) {
        otmTypeahead.create(typeahead);
    });

    var udfRowTemplate = _.template(
        '<tr data-value-id="">' +
            '<% _.each(fields, function (field) { %>' +
            '<td> <%= field %> </td>' +
            '<% }) %>' +
            '</tr>');

    // Wire up collection udfs
    $('a[data-udf-id]').click(function() {
        var id = $(this).data('udf-id');
        var fields = $('table[data-udf-id="' + id + '"] * [data-field-name]').toArray();

        var data = _.map(fields, function(field) { return $(field).val(); });

        $(this).closest('table').append(udfRowTemplate({
            fields: data
        }));
    });

    imageUploadPanel.init(options.imageUploadPanel);

    var form = inlineEditForm.init(
            _.extend(options.inlineEditForm,{ onSaveBefore: onSaveBefore }));

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
        inlineEditForm: form,
        editLocationButton: options.plotLocation.edit,
        cancelEditLocationButton: options.plotLocation.cancel,
        location: options.plotLocation.location
    });

    function onSaveBefore(data) {
        plotMover.onSaveBefore(data);
    }
};
