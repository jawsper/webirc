const webSocketBridge = new channels.WebSocketBridge();

function get_tab_by_id(id)
{
	let selector = ".tab-nav[data-id='" + id + "']";
	return $(selector);
}
function get_panel_by_id(id)
{
	let selector = ".tab-pane[data-id='" + id + "']";
	return $(selector);
}

function get_panel_or_create(id)
{
	let panel = get_panel_by_id(id);
	// make sure the tab exists, even if we don't have the name yet.
	if(panel.length == 0)
	{
		create_tab(id, id);
		webSocketBridge.send({
			'action': 'screen_name',
			'screen_id': id,
		})
		panel = get_panel_by_id(id);
	}
	return panel;
}

function name_to_nick(name)
{
	if(!name) return name;
	let split_pos = name.indexOf('!');
	if(split_pos > 0) name = name.substring(0, split_pos);
	return name;
}

function prettify_text(text)
{
	return text.replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank">$1</a>');
}

function create_tab(id, title)
{
	let current_tab = get_tab_by_id(id);
	if(current_tab.length > 0)
	{
		$('.title', current_tab).text(title);
		return;
	}

	if(!this.tab_template)
	{
		this.tab_template = $('#template-tab').html();
	}
	if(!this.panel_template)
	{
		this.panel_template = $('#template-tabpanel').html();	
	}
	
	let data = {
		'tab_id': id,
		'tab_title': title
	}
	let tab = $(Mustache.render(this.tab_template, data));
	let panel = $(Mustache.render(this.panel_template, data));
	let active = $('li', '#tab_container > ul').length == 0;
	if(active)
	{
		tab.addClass('active');
		panel.addClass('active');
	}
	else
	{
		tab.addClass('unread');
	}
	$('#tab_container > ul').append(tab);
	$('#tab_container > .tab-content').append(panel);
}

function delete_tab(id)
{
	get_tab_by_id(id).remove();
	get_panel_by_id(id).remove();
}

function process_command(screen_id, command, arguments)
{
	console.debug({'screen_id': screen_id, 'command': command, 'args': arguments});
}

function process_input(screen_id, message)
{
	// allow // to send raw commands over the wire
	if(message.substring(0, 2) == '//')
	{
		message = message.substring(1);
	}
	else if(message.substring(0, 1) == '/')
	{
		var command = message.substring(1);
		let arg_split = command.indexOf(' ');
		var arguments = '';
		if(arg_split > -1)
		{
			arguments = command.substring(arg_split + 1);
			command = command.substring(0, arg_split);
		}
		process_command(screen_id, command, arguments);
		return;
	}
	else if(!screen_id)
	{
		return;
	}
	webSocketBridge.send({
		'action': 'message',
		'screen_id': screen_id,
		'text': message
	});
}

function auto_load_messages(screen_id)
{
	let panel = get_panel_by_id(screen_id);
	let messages = $('.message', panel);
	let last_message = messages.filter(':last');
	let moment = null;
	if(last_message.length != 0)
	{
		moment = new Date(last_message.data('time'));
		// console.debug(moment);
	}

	// console.debug(panel);
	// console.debug(messages);
	// console.debug(last_message);

	load_messages(screen_id, moment, false);
	// todo: be smart, and only request needed messages
}

function load_messages(screen_id, moment, before)
{
	let data = {
		'action': 'load_events',
		'screen_id': screen_id,
	}
	if(moment)
	{
		data['moment'] = moment.strftime('%FT%T%z')
		data['before'] = before ? true : false;
	}
	webSocketBridge.send(data);
}

function set_screen_names(screen_id, names)
{
	if(!this.name_template)
	{
		this.name_template = $('#template-name').html();
	}
	// console.debug(screen_id, names);
	// console.debug(this.name_template);
	let panel = get_panel_by_id(screen_id);	
	let names_container = $('.names', panel);
	names_container.empty();
	let name_template = this.name_template;
	$.each(names, function(_, name)
	{
		let rendered = $(Mustache.render(name_template, {
			'name': name
		}));
		names_container.append(rendered);
	});
}

function set_connection_status(connected)
{
	$('.connection-status').toggleClass('connected', connected);
}

function set_topics(screen_id, topic)
{
	let panel = get_panel_by_id(screen_id);
	let topic_container = $('.topic', panel);
	topic_container.text(topic);
}

$(function()
{
	$(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
		e.target // newly activated tab
		e.relatedTarget // previous active tab
		// console.debug(e);
		let tab = $(e.target).closest('.tab-nav');
		tab.removeClass('unread');
	});
	$('#form_input').submit(function(e)
	{
		e.preventDefault();
		let input = $('.input', this);
		let text = input.val();
		if(text.length > 0)
		{
			input.val('');
			let tab_id = $('.tab-pane.active').data('id');
			process_input(tab_id, text);
		}
	})
	$(document).on('click', '.tab-nav .close-tab', function(e)
	{
		let tab_id = $(this).closest('.tab-nav').data('id');
		delete_tab(tab_id);
	});

	webSocketBridge.connect('/ws/');

	webSocketBridge.socket.addEventListener('open', function(e)
	{
		// console.debug('onopen');
		set_connection_status(true);
	});
	webSocketBridge.socket.addEventListener('error', function(e)
	{
		// console.debug('onerror');
	});
	webSocketBridge.socket.addEventListener('close', function(e)
	{
		// console.debug('onclose');
		set_connection_status(false);
	});

	webSocketBridge.listen(function(action, stream)
	{
		// console.log(action);
		if(action.screens)
		{
			$.each(action.screens, function(screen_id, screen_title)
			{
				create_tab(screen_id, screen_title);
				auto_load_messages(screen_id);
			});
		}
		if(action.names)
		{
			$.each(action.names, set_screen_names);
		}
		if(action.topics)
		{
			$.each(action.topics, set_topics);
		}
		if(action.events)
		{
			$.each(action.events, function(screen_id, events)
			{
				var last_event = null;
				$.each(events, function(_, event)
				{
					last_event = on_event(screen_id, event);
				});
				if(last_event)
				{
					last_event.output.scrollTop(last_event.output.prop('scrollHeight'));
				}
			});
		}
		// console.log(action, stream);
	});

});

function get_event_text(event)
{
	switch(event.type)
	{
		case 'join':
			return name_to_nick(event.source) + ' joined the channel'
		case 'part':
			return name_to_nick(event.source) + ' parted the channel' +
			(event.reason ? ' (' + event.reason + ')' : '');
		case 'kick':
			return name_to_nick(event.source) + ' kicked ' + 
				name_to_nick(event.target) + 
				(event.reason ? ' (' + event.reason + ')' : '')
			break;
		default:
			return event.text;
	}
}

function get_template(type)
{
	if(!this.templates) this.templates = {};
	if(!this.templates[type])
		this.templates[type] = $('#template-' + type).html();
	return this.templates[type];
}


function on_event(screen_id, event)
{
	console.debug(event);

	// message already exists
	if($('#event-' + event.id).length)
	{
		return;
	}

	let output = $('.output', get_panel_or_create(screen_id));

	let data = {
		'id': event.id,
		'time': new Date(event.moment).strftime('%Y-%m-%d %H:%M:%S'),
	}
	let template = get_template(event.type);
	if(!template)
	{
		if(event.type == 'privmsg' || event.type == 'notice' || event.type == 'action')
		{
			template = get_template('message');
		}
		else
		{
			template = get_template('event');
		}
	}

	if(event.type == 'privmsg' || event.type == 'notice' || event.type == 'action')
	{
		$.extend(data,
		{
			'raw_source': event.source,
			'source': name_to_nick(event.source),
			'text': prettify_text(event.text)
		});
		if(event.type == 'notice')
		{
			data['name_wrapper_l'] = '-';
			data['name_wrapper_r'] = '-';
		}
		else if(event.type == 'action')
		{
			data['name_wrapper_l'] = '!';
		}
		else
		{
			data['name_wrapper_l'] = '<';
			data['name_wrapper_r'] = '>';
		}
	}
	else
	{
		$.extend(data, {
			'raw_source': event.source,
			'source': name_to_nick(event.source),
			'raw_target': event.target,
			'target': name_to_nick(event.target),
			'reason': event.reason ? '(' + event.reason + ')' : '',
			'text': get_event_text(event)
		});
	}

	let rendered_event = $(Mustache.render(template, data));
	$(rendered_event).data('time', event.moment);
	
	output.append(rendered_event);

	let tab = get_tab_by_id(screen_id);
	if(!tab.hasClass('active'))
	{
		tab.addClass('unread');
	}
	return {'output': output, 'event': rendered_event};
}