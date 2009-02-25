/*
 * jQuery plugin: autoCompletefb(AutoComplete Facebook)
 * @requires jQuery v1.2.2 or later
 * using plugin:jquery.autocomplete.js
 *
 * Credits:
 * - Idea: Facebook
 * - Guillermo Rauch: Original MooTools script
 * - InteRiders <http://interiders.com/> 
 * - Jannis Leidel (refactoring)
 *
 * Copyright (c) 2008 Widi Harsojo <wharsojo@gmail.com>, http://wharsojo.wordpress.com/
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 */

;(function($) {

$.fn.extend({
	autocompletefb: function(options) {
		var settings =  {
			urlLookup: [""],
			acOptions: {},
			foundClass: ".acfb-data",
			inputClass: ".acfb-input",
			removeFindCallback: function(o){}
		}
		if(options) $.extend(settings, options);
		return $.Autocompleter.Facebook(this, settings);
	}
});

$.Autocompleter.Facebook = function(input, settings) {
	function getData() {
		var result = '';
		$(settings.foundClass).each(function(i) {
			if (i>0)result+=',';
			result += $('span.label', this).attr('id');
		});
		return result;
	}
	function clearData() {
		$(settings.foundClass, input).remove();
		$(input).focus();
		return input;
	}
	function removeFind(o) {
		$(o).unbind('click').parent().remove();
		$(input).focus();
		settings.removeFindCallback(o);
		return input;
	}
	function createItem(data) {
		var row = '<li class="acfb-data ' + settings.foundClass.replace(/\./, '') + '">' +
		          '<span class="label" id="' + settings.acOptions.formatResult(data) + '">' +
		          settings.acOptions.formatItem(data) + '</span><span class="close"></span></li>';
		var inserted_row = $(input).before(row);
		$('span.close', inserted_row[0].previousSibling).click(function(){
			removeFind(this);
		});
	}
	$(settings.foundClass+" span.close").click(function(){
		removeFind(this);
	});
	autocomplete = $(input).autocomplete(
		settings.urlLookup,
		settings.acOptions
	).result(function(event, data, formatted) {
		createItem(data);
		$(input).val('').focus();
	});
	$(input).focus();
	return {
		createItem: createItem,
		getData: getData,
		clearData: clearData,
		removeFind: removeFind,
		autocomplete: autocomplete,
		input: input
	}
};

})(jQuery);
