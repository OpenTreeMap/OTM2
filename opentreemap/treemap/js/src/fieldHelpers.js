// Helper functions for fields defined by the field.html template

"use strict";

var $ = require('jquery'),
    _ = require('underscore');

var getField = exports.getField = function ($fields, name) {
    return $fields.filter('[data-field="' + name + '"]');
};
var getSerializableField = exports.getSerializableField = function ($fields, name) {
    // takes a jQuery collection of edit fields and returns the
    // actual input or select field that will be serialized
    return getField($fields, name).find('[name="' + name + '"]');
};

var excludeButtons = exports.excludeButtons = function (selector) {
    return $(selector).filter(":not(.btn)");
};

exports.formToDictionary = function ($form, $editFields, $displayFields) {
    $displayFields = $displayFields || $();

    var isTypeaheadHiddenField = function(name) {
        return getSerializableField($editFields, name).is('[data-typeahead-hidden]');
    };
    var getDisplayValue = function(type, name) {
        var $displayField;
        if (isTypeaheadHiddenField(name)) {
            return $form.find('[data-typeahead-restore="' + name + '"]').val();
        }
        $displayField = getField($displayFields, name);
        if ($displayField.is('[data-value]')) {
            if (type === 'bool') {
                return $displayField.attr('data-value') === "True";
            }
            return $displayField.attr('data-value');
        }
        return undefined;
    };

    var result = {};
    _.each($form.serializeArray(), function(item) {
        var type = getField($editFields, item.name).attr('data-type'),
            displayValue = getDisplayValue(type, item.name);

        if (item.value === displayValue) {
            return;  // Don't serialize unchanged values
        }

        if (type === 'bool') {
            // Handled below so we catch unchecked checkboxes which
            // serializeArray ignores
        } else if (item.value === '' && (type === 'int' || type === 'float')) {
            // convert empty numeric fields to null
            result[item.name] = null;
        } else if (item.value === '' && isTypeaheadHiddenField(item.name)) {
            // convert empty foreign key id strings to null
            result[item.name] = null;
        } else {
            result[item.name] = item.value;
        }
    });
    $form.find('[name][type="checkbox"]').not('[disabled]').each(function(i, elem) {
        if (elem.checked !== getDisplayValue('bool', elem.name)) {
            result[elem.name] = elem.checked;
        }
    });
    return result;
};
