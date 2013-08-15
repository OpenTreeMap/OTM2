"use strict";

var Url = require('url'),
    QS = require('querystring');

exports.getUpdatedQueryString = function (k, v) {
    var url = Url.parse(window.location.href, true);
    var query = url.query || {};

    query[k] = v;

    return QS.stringify(query);
};

exports.getUpdateUrlByUpdatingQueryStringParam = function (k, v) {
    var url = Url.parse(window.location.href, true);
    var query = url.query || {};

    if (v == null) {
        delete query[k];
    } else {
        query[k] = v;
    }

    url.query = query;
    url.search = null;

    return Url.format(url);
};

exports.pushState = function (url) {
    history.pushState({}, '', url);
};

exports.parseQueryString = function () {
    var match,
        pl     = /\+/g,  // Regex for replacing addition symbol with a space
        search = /([^&=]+)=?([^&]*)/g,
        decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
        query  = window.location.search.substring(1),
        urlParams = {};

    while ((match = search.exec(query))) {
        urlParams[decode(match[1])] = decode(match[2]);
    }

    return urlParams;
};
