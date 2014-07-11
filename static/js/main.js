$(document).ready(function() {
	$("#next-word").keypress(function(e) {
		if (e.which == 13) {
			nextword($(this).val(), function(result) {
				if (result) {
					$('#next-word').parent().removeClass('has-error');
				} else {
					$('#next-word').parent().addClass('has-error');
				}
			});
			return false;
		}
	});
});

var nextword = function(word, callback) {
	if ($('#last-word').html()[$('#last-word').html().length - 1] != word[0]) {
		callback(false);
	}
	$.getJSON('/next', $.param({w: word}), function(data) {
		callback(data);
	});
};
