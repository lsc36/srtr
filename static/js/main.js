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
	window.setTimeout(updater.poll, 0);
});

var nextword = function(word, callback) {
	if ($('#last-word').html()[$('#last-word').html().length - 1] != word[0]) {
		callback(false);
	}
	$.getJSON('/next', $.param({w: word}), function(data) {
		callback(data);
	});
};

var updater = {
	errorSleepTime: 500,
	position: null,

	poll: function() {
		var args = {};
		if (updater.position) args.pos = updater.position;
		$.getJSON('/update', $.param(args), updater.onSuccess)
			.fail(updater.onError);
	},

	onSuccess: function(response) {
		updater.update(response);
		updater.errorSleepTime = 500;
		window.setTimeout(updater.poll, 0);
	},

	onError: function(response) {
		updater.errorSleepTime *= 2;
		console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
		window.setTimeout(updater.poll, updater.errorSleepTime);
	},

	update: function(response) {
		updater.position = response.position;
		var last_word = response.last_word;
		$('#last-word').html(last_word);
		$('#position').html('#' + updater.position);
		$('#next-word').attr('placeholder', last_word[last_word.length - 1] + '...')
	}
};
