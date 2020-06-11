String.format = function() {
    // The string containing the format items (e.g. "{0}")
    // will and always has to be the first argument.
    var theString = arguments[0];
    
    // start with the second argument (i = 1)
    for (var i = 1; i < arguments.length; i++) {
        // "gm" = RegEx options for Global search (more than one instance)
        // and for Multiline search
        var regEx = new RegExp("\\{" + (i - 1) + "\\}", "gm");
        theString = theString.replace(regEx, arguments[i]);
    }
    
    return theString;
}

$(function(){
    $('#cluster_select').bind("change", updateFields);
    function updateFields () {
        var id = $(this).val();
        document.location.href= '/services/pf/' + id;
    }

    $('.link-tab').click(function(){
      window.location.href = ($(this).attr('href'));
    });

    var control = {
        'protocol': "",
        'action'  : "",
        'inet'    : ""
    }

    var protocol = JSON.parse($('#protocol').val());
    control['protocol'] = "<select class='protocol form-control'>";
    for (var i in protocol)
        control['protocol'] += "<option value='"+protocol[i][0]+"'>"+protocol[i][1]+"</option>";
    control['protocol'] += "</select>";

    var action = JSON.parse($('#action').val());
    control['action'] = "<select class='action form-control'>";
    for (var i in action)
        control['action'] += "<option value='"+action[i][0]+"'>"+action[i][1]+"</option>";
    control['action'] += "</select>";

    control['inet'] = "<select class='inet form-control'><option value='inet'>IPV4</option><option value='inet6'>IPV6</option></select>";

    var direction = JSON.parse($('#direction').val());
    control['direction'] = "<select class='direction form-control'>";
    for (var i in direction)
        control['direction'] += "<option value='"+direction[i][0]+"'>"+direction[i][1]+"</option>";
    control['direction'] += "</select>";

    var interfaces = JSON.parse($('#interfaces').val());
    control['interfaces'] = "<select class='interfaces form-control'>";
    for (var i in interfaces)
        control['interfaces'] += "<option value='"+interfaces[i][0]+"'>"+interfaces[i][1]+"</option>";
    control['interfaces'] += "</select>";

    $('.addlink').on('click', function(){
        var table = $(this).data('table');

        if (table == 'table_rules_pf'){
            var log = "";
            var duplicate = 'duplicate_rule';
        }

        // Add a line in the rule table
        var theme = String.format("<tr><td>{0}</td><td>{1}</td><td><input type='checkbox' {2} class='log form-control'/></td><td>{3}</td><td>{4}</td><td>{5}</td><td><input type='text' class='src_ip multiple form-control'/></td><td><input type='text' class='dst_ip multiple form-control'/></td><td><input type='text' class='port multiple form-control'/></td><td><input type='text' class='flags form-control'/></td><td><input type='text' class='rate form-control'/></td><td><input type='text' class='form-control comment'/></td><td><a href='#' class='{6}''><i class='fa fa-copy'></i></a><a href='#' class='del_rule'><i class='fa fa-trash-o'></i></a></td></tr>", control['action'], control['direction'], log, control['interfaces'], control['inet'], control['protocol'], duplicate);

        $('#'+table+' tbody').append(theme);
        $('.protocol').on('change', protocol_changed);
        $('.del_rule').on('click', del_rule);
        $('.duplicate_rule').on('click', duplicate_rule);

    });

    $('.protocol').on('change', protocol_changed);
    function protocol_changed(){
        //Remove port when some protocols are selected
        var port_input = $(this).parents()[1].children[8].children[0];
        if ($(this).val() === 'icmp' || $(this).val() === 'icmp6'  || $(this).val() === "udp" || $(this).val() === 'all'){
            $(port_input).val('');
            $(port_input).prop('readonly', true);
        } else {
            $(port_input).prop('readonly', false);
        }

        var inet_input = $(this).parents()[1].children[4].children[0];
        if ($(this).val() === 'icmp6') {
            $(inet_input).val('inet6');
        }
        else if ($(this).val() === 'icmp') {
            $(inet_input).val('inet');
        }

    }

    $('.del_rule').on('click', del_rule);
    function del_rule(){
        $($(this).parents('tr')).remove();
    }

    $('.duplicate_rule').on('click', duplicate_rule);
    function duplicate_rule(){
        $('.duplicate_rule').unbind('click');
        $('.del_rule').unbind('click');

        var rule = $($(this).parents('tr')).html();
        
        $('#table_rules_pf tbody').append("<tr>"+rule+"</tr>");
        $('.duplicate_rule').on('click', duplicate_rule);
        $('.del_rule').on('click', del_rule);
    }

    function build_rule(){
        var all_rules = [];
        $('#table_rules_pf tbody tr').each(function(){
            var td = $(this).children('td');

            if (td.text() !== ""){
                var rule = {
                    'action'     : $($(td[0]).children()[0]).val(),
                    'direction'  : $($(td[1]).children()[0]).val(),
                    'log'        : $($(td[2]).children()[0]).is(':checked'),
                    'interface'  : $($(td[3]).children()[0]).val(),
                    'inet'       : $($(td[4]).children()[0]).val(),
                    'protocol'   : $($(td[5]).children()[0]).val(),
                    'source'     : $($(td[6]).children()[0]).val(),
                    'destination': $($(td[7]).children()[0]).val(),
                    'port'       : $($(td[8]).children()[0]).val(),
                    'flags'      : $($(td[9]).children()[0]).val(),
                    'rate'       : $($(td[10]).children()[0]).val(),
                    'comment'    : $($(td[11]).children()[0]).val()
                }

                all_rules.push(rule)
            }
        })


        $('#pf_rules').val(JSON.stringify(all_rules));
        $('#form_pf').submit();
    }

    $('#save').on('click', function(){
        build_rule();
    });

    function load_rules(table, type_rule){
        var rules = JSON.parse($('#'+type_rule).val());
        for (var i in rules){
            var rule          = JSON.parse(rules[i]);
            var protocol      = JSON.parse($('#protocol').val());
            var protocol_html = "<select class='protocol form-control'>";
            for (var x in protocol){
                var proto = "";
                rule['protocol'] === protocol[x][0] ? proto = "selected='selected'" : proto = "";
                protocol_html += "<option value='"+protocol[x][0]+"' "+proto+">"+protocol[x][1]+"</option>";
            }
            protocol_html += "</select>";

            var action      = JSON.parse($('#action').val());
            var action_html = "<select class='action form-control'>";
            for (var x in action){
                var act = "";
                rule['action'] === action[x][0] ? act = "selected='selected'" : act = "";
                action_html += "<option value='"+action[x][0]+"' "+act+">"+action[x][1]+"</option>";
            }
            action_html += "</select>";

            var direction      = JSON.parse($('#direction').val());
            var direction_html = "<select class='direction form-control'>";
            for (var x in direction){
                var act = "";
                rule['direction'] === direction[x][0] ? act = "selected='selected'" : act = "";
                direction_html += "<option value='"+direction[x][0]+"' "+act+">"+direction[x][1]+"</option>";
            }
            direction_html += "</select>";

            var inet = "", inet6 = "";
            if (rule['inet'] === 'inet')
                inet = "selected='selected'";
            else if (rule['inet'] === 'inet6')
                inet6 = "selected='selected'";

            var inet_html = String.format("<select class='inet form-control'><option value='inet' {0}>IPV4</option><option value='inet6' {1}>IPV6</option></select>", inet, inet6);

            var interfaces      = JSON.parse($('#interfaces').val());
            var interfaces_html = "<select class='interfaces form-control'>";
            for (var x in interfaces){
                var intf = "";
                rule['interface'] === interfaces[x][0] ? intf = "selected='selected'" : intf = "";
                interfaces_html += "<option value='"+interfaces[x][0]+"' "+intf+">"+interfaces[x][1]+"</option>";
            }
            interfaces_html += "</select>";

            var log = "";
            var port_disabled = "";

            if (type_rule == 'pf_rules'){
                rule['log'] === true ? log = "checked='checked'" : log = '';
                var duplicate = 'duplicate_rule';
            }

            if (rule['protocol'] === 'ICMP' || rule['protocol'] === 'ALL')
                port_disabled = "disabled='disabled'"
            else
                port_disabled = ""

            var line = String.format("<tr><td>{0}</td><td>{1}</td><td><input type='checkbox' class='log form-control' {2}/></td><td>{3}</td><td>{4}<td>{5}</td><td><input type='text' class='src_ip multiple form-control' value='{6}'/></td><td><input type='text' class='dst_ip multiple form-control' value='{7}'/></td><td><input type='text' class='port multiple form-control' value='{8}'/></td><td><input type='text' class='form-control flags' value='{9}'/></td><td><input type='text' class='form-control rate' value='{10}'/></td><td><input type='text' class='form-control comment' value='{11}'/></td><td><a href='#' class='{10}'><i class='fa fa-copy'></i></a><a href='#' class='del_rule'><i class='fa fa-trash-o'></i></a></td></tr>", action_html, direction_html, log, interfaces_html, inet_html, protocol_html, rule['source'], rule['destination'], rule['port'], rule['flags'], rule['rate'], rule['comment'], duplicate)

            $('#'+table+' tbody').append(line);
        }

        $('.del_rule').on('click', del_rule);
        $('.protocol').on('change', protocol_changed);
    
        if (type_rule === 'pf_rules')
            $('.duplicate_rule').on('click', duplicate_rule);

    }

    load_rules('table_rules_pf', 'pf_rules')

})
