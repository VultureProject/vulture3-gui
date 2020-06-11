function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function add_priority_selector(element){
var priority_html = "\
    <div id='"+element.id+"' class='form-group carp_configuration'> \
	<label class='col-sm-4 control-label'>Priority of "+element.text+"</label>\
    	<div class='col-sm-5'>\
    	<input class='form-control has-popover' data-container='body' data-content='Priority of Listener' data-placement='right' id='id_"+element.id+"' name='carp_priority_"+element.id+"' type='number' />\
    	</div>\
    </div>";
return priority_html;
}


function handle_form_errors(data){
    if (typeof(data['form_errors']) !== 'undefined'){
        $('.errorlist').remove();
        $.each(data['form_errors'], function(field_name, error_list){
            field_selector = $('#id_'+field_name);
            var ul = $('<ul/>').insertAfter(field_selector);
            $.each(error_list, function(idx, err_msg){
                console.log(err_msg);
                var li = $('<li/>').addClass('errorlist').attr('role', 'menuitem').appendTo(ul);
                var group = $('<span/>').text(err_msg).appendTo(li);
            });
        });
    }
}


function listener_status(addr, port, node_name, id, data, lang){
    var label        = addr;
    var container    = $('#listener_'+id);
    var status       = data['status'];
    var need_restart = data['need_restart'];

    if (status === 'stop'){
        var status = '<span class="label label-danger">' + lang[0] + '</span>';
        var action = '&nbsp;<a class="action_button" href="/management/start/'+ id +'"><i class="fa fa-play"></i></a>';
    
    } else if (status === 'run'){
        var status = '<span class="label label-success">' + lang[1] + '</span>';
        var action = '&nbsp;<a class="action_button" href="/management/stop/'+ id +'"><i class="fa fa-pause"></i></a>';
    
    } else if (status === 'Error'){
        var status = '<span class="label label-warning">' + lang[2] + '</span>';
        var action = '&nbsp;<a href="#"><i class="fa fa-exclamation"></i></a>';
    }

    if (need_restart === 'true' && status !== 'Error'){
        action = action + '&nbsp;<a class="action_button" href="/management/reload/' + id + '"><span><i class="fa fa-refresh fa-spin"></i></span></a>';
    }

    action = action+'&nbsp;<a href="#" data-href="/management/download/' + id + '" data-action="download" class="dl_button"><span><i class="fa fa-download"></i></span></a>';
    container.html("<td>" + label + "</td><td>" + port + "</td><td>" + status + "</td><td>" + action + "</td>");
}