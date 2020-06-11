    $(function(){
    // exemple: String.format("{0}/{1}/{2}", "2012", "12", "12") --> 2012/12/12
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

    var logging_control = JSON.parse($('#logging_control').val());

    $('#reportrange_logs').html('Today');

    var reportrange = $('#reportrange_logs').daterangepicker({
        format             : 'MM/DD/YYYY HH:mm:ss',
        minDate            : '01/01/1970',
        showDropdowns      : true,
        showWeekNumbers    : true,
        timePicker         : true,
        timePickerIncrement: 1,
        timePicker12Hour   : true,
        ranges: {
            'Today'       : [moment().startOf('day'), moment().endOf('day')],
            'Yesterday'   : [moment().subtract(1,'days').startOf('day'), moment().subtract(1,'days').endOf('day')],
            'Last 7 Days' : [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month'  : [moment().startOf('month'), moment().endOf('month')],
            'Last Month'  : [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        opens        : 'right',
        buttonClasses: ['btn', 'btn-sm'],
        applyClass   : 'btn-primary',
        cancelClass  : 'btn-default',
        separator    : ' to ',
        locale: {
            applyLabel      : 'Submit',
            cancelLabel     : 'Cancel',
            fromLabel       : 'From',
            toLabel         : 'To',
            customRangeLabel: 'Custom',
            daysOfWeek      : ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr','Sa'],
            monthNames      : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            firstDay        : 1,
        },

        onSelect: function(){
            all_tables[get_current_table()].fnDraw();

        }
    }, function(start, end, label) {
        start_time = start.valueOf();
        end_time   = end.valueOf();

        if (label === 'Custom'){
            $('#reportrange_logs').html('From '  + start.format('HH:mm a <b>MMMM D, YYYY</b>') + ' To ' + end.format('HH:mm a <b>MMMM D, YYYY</b>'));
        } else {
            $('#reportrange_logs').html(label);
        }
    }).on('hide.daterangepicker', function(){
        all_tables[get_current_table()].fnDraw();
    })

    var static_url     = $('#static_url').val();
    var selected       = [];
    var all_tables     = [];
    var jquery_builder = null;
    var table_logs;

    var data_table = {
        'access': {
            // All the columns on the database
            'columns': "_id,time,src_ip,user,http_method,requested_uri,http_code,size,referer,user_agent,bytes_received,bytes_sent,time_elapsed,incoming_protocol,reputation,threshold,score,owasp_top10,reasons",
            'order'  : [[1, 'desc']],
            'filters': {
                'src_ip'           : 'string',
                'country'          : 'string',
                'user'             : 'string',
                'http_method'      : 'string',
                'requested_uri'    : 'string',
                'http_code'        : 'integer',
                'size'             : 'integer',
                'referer'          : 'string',
                'user_agent'       : 'string',
                'bytes_received'   : 'integer',
                'bytes_sent'       : 'integer',
                'time_elapsed'     : 'double',
                'incoming_protocol': 'string',
                'reputation'       : 'string',
                'threshold'        : 'integer',
                'score'            : 'integer',
                'owasp_top10'      : 'string',
                'reasons'          : 'string'
            },

            // Columns definition in the datatable
            'aoColumnsDefs': [
                // data & name: name of the columns, aTargets: num of td
                {'data': 'info', 'name': 'info', 'defaultContent': "", 'bVisible': true, 'aTargets': [0], 'sWidth': "1%", "sClass": "center", "bSortable": false},
                {'data': 'time', 'name': 'time', 'defaultContent': "", 'bVisible': true, 'aTargets': [1], 'sWidth': "13%", mRender: function(data, type, row){
                    if (type === 'sort')
                        return data;

                    try{
                        return $.format.toBrowserTimeZone(data);
                    } catch(err){
                        return data;
                    }
                }},
                {'data': 'src_ip', 'name': 'src_ip', 'defaultContent': "", 'bVisible': true, 'aTargets': [2], 'sWidth': "9%", "mRender": function(data, type, row){
                    try{
                        var country = row['country'].toLowerCase();
                        if (country === undefined)
                            return data;

                        if (country=="-") return String.format("<b>?</b>  ", static_url, country) + data;
                        return String.format("<img src='{0}{1}.png'/>", static_url, country) + data;
                    } catch (err){
                        return data;
                    }
                }},
                {'data': 'user', 'name': 'user', 'defaultContent': "", 'bVisible': true, 'aTargets': [3], 'sWidth': "10%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'http_method', 'name': 'http_method', 'defaultContent': "", 'bVisible': true, 'aTargets': [4], 'sWidth': "2.5%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'requested_uri', 'name': 'requested_uri', 'defaultContent': "", 'bVisible': true, 'aTargets': [5], 'sWidth': "40%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'http_code', 'name': 'http_code', 'defaultContent': "", 'bVisible': true, 'aTargets': [6], 'sWidth': "2.5%"},
                {'data': 'size', 'name': 'size', 'bVisible': true, 'defaultContent': "", 'aTargets': [7], 'sWidth': "2.5%"},
                {'data': 'referer', 'name': 'referer', 'bVisible': false, 'defaultContent': "", 'aTargets': [8], 'sWidth': "5%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'user_agent', 'name': 'user_agent', 'bVisible': true, 'defaultContent': "", 'aTargets': [9], 'sWidth': "15%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'bytes_received', 'name': 'bytes_received', 'bVisible': false, 'defaultContent': "", 'aTargets': [10], 'sWidth': "1%"},
                {'data': 'bytes_sent', 'name': 'bytes_sent', 'bVisible': false, 'defaultContent': "", 'aTargets': [11], 'sWidth': "1%"},
                {'data': 'time_elapsed', 'name': 'time_elapsed', 'bVisible': false, 'defaultContent': "", 'aTargets': [12], 'sWidth': "1%"},
                {'data': 'incoming_protocol', 'name': 'incoming_protocol', 'bVisible': true, 'defaultContent': "", 'aTargets': [13], 'sWidth': "2.5%", "mRender": function(data){ return encodeURI(data); }},
                {'data': 'reputation', 'name': 'reputation', 'bVisible': true, 'defaultContent': "", 'aTargets': [14], 'sWidth': "10%", "mRender": function(data, type, row){
                    if (data !== "-") {
                        data = data.split(",");
                        var value = "";

                        for (var rep of data){
                            if (rep !== "-")
                                value += String.format("<label class='label label-danger tags {0}'>{0}</label>", rep);
                        }

                        return value;
                    }
                }},
                {'data': 'threshold', 'name': 'threshold', 'bVisible': true, 'defaultContent': "", 'aTargets': [15], 'sWidth': "1%"},
                {'data': 'score', 'name': 'score', 'bVisible': true, 'defaultContent': "", 'aTargets': [16], 'sWidth': "1%"},
                {'data': 'owasp_top10', 'name': 'owasp_top10', 'bVisible': false, 'defaultContent': "", 'aTargets': [17], 'sWidth': "2.5%", "mRender": function(data){
                    return data.replace(/[[\]"\\]/g, "");
                }},
                {'data': 'reasons', 'name': 'reasons', 'bVisible': false, 'defaultContent': "", 'aTargets': [18], 'sWidth': "2.5%", "mRender": function(data){
                    return data.replace(/[[\]"\\]/g, "");
                }},

            ],
        },


        'packet_filter': {
            // All the columns on the database
            'columns': "_id,date,src_ip,src_port,dst_ip,dst_port,action,direction,interface,info",
            'order'  : [[1, 'desc']],

            'filters': {
                'time'           : 'string',
                'src_ip'         : 'string',
                'src_port'       : 'integer',
                'dst_ip'         : 'string',
                'dst_port'       : 'integer',
                'action'         : 'string',
                'direction'      : 'string',
                'interface'      : 'string',
                'time_elapsed'   : 'integer',
                'info'       : 'string',
            },

            // Columns definition in the datatable
            'aoColumnsDefs': [
                // data & name: name of the columns, aTargets: num of td
                {'data': 'info', 'name': 'info', 'defaultContent': "", 'bVisible': true, 'aTargets': [0], 'sWidth': "1%", "sClass": "center", "bSortable": false},
                {'data': 'time', 'name': 'time', 'defaultContent': "", 'bVisible': true, 'aTargets': [1], 'sWidth': "13%"},
                {'data': 'src_ip', 'name': 'src_ip', 'defaultContent': "", 'bVisible': true, 'aTargets': [2], 'sWidth': "9%", "mRender": function(data, type, row){
                    try{
                        var ctx = "";
                        var country = row['country'].toLowerCase();
                        if (country=="-") return String.format("<b>?</b>  ", static_url, country) + data;
                        return String.format("<img src='{0}{1}.png'/>", static_url, country) + data + ctx;
                    } catch (err){
                        return data;
                    }
                }},
                {'data': 'src_port', 'name': 'src_port', 'defaultContent': "", 'bVisible': true, 'aTargets': [3], 'sWidth': "5%"},
                {'data': 'dst_ip', 'name': 'dst_ip', 'defaultContent': "", 'bVisible': true, 'aTargets': [4], 'sWidth': "9%"},
                {'data': 'dst_port', 'name': 'dst_port', 'defaultContent': "", 'bVisible': true, 'aTargets': [5], 'sWidth': "5%"},
                {'data': 'action', 'name': 'action', 'defaultContent': "", 'bVisible': true, 'aTargets': [6], 'sWidth': "5%"},
                {'data': 'direction', 'name': 'direction', 'defaultContent': "", 'bVisible': true, 'aTargets': [7], 'sWidth': "5%"},
                {'data': 'interface', 'name': 'interface', 'defaultContent': "", 'bVisible': true, 'aTargets': [8], 'sWidth': "5%"},
                {'data': 'info_pf', 'name': 'info_pf', 'defaultContent': "", 'bVisible': true, 'aTargets': [9], 'sWidth': "30%"},
            ],
        },

        'vulture': {
            // All the columns on the database
            'columns': "_id,log_level,time,log_name,filename,message",
            'order'  : [[2, 'desc']],
            'filters': {
                'log_level': 'string',
                'time'     : 'string',
                'filename' : 'integer',
                'message'  : 'string',
                'log_name' : 'string',
            },

            // Columns definition in the datatable
            'aoColumnsDefs': [
                // data & name: name of the columns, aTargets: num of td
                {'data': 'info', 'name': 'info', 'defaultContent': "", 'bVisible': true, 'aTargets': [0], 'sWidth': "1%", "sClass": "center", "bSortable": false},
                {'data': 'log_level', 'name': 'log_level', 'defaultContent': "", 'bVisible': true, 'aTargets': [1], 'sWidth': "5%"},
                {'data': 'time', 'name': 'time', 'defaultContent': "", 'bVisible': true, 'aTargets': [2], 'sWidth': "13%"},
                {'data': 'log_name', 'name': 'log_name', 'defaultContent': "", 'bVisible': true, 'aTargets': [3], 'sWidth': "10%"},
                {'data': 'filename', 'name': 'filename', 'bVisible': true, 'defaultContent': "", 'aTargets': [4], 'sWidth': "10%"},
                {'data': 'message', 'name': 'message', 'bVisible': true, 'defaultContent': "", 'aTargets': [5], 'sWidth': "71%"},
            ],
        },

        'diagnostic': {
            // All the columns on the database
            'columns': "_id,log_level,node_name,test_module,traceback,filename,test_name,time,message",
            'order'  : [[7, 'desc']],
            'filters': {
                'log_level'  : 'string',
                'time'       : 'string',
                'test_module': 'string',
                'message'    : 'string',
                'node_name'  : 'string',
                'test_name'  : 'string',
            },

            // Columns definition in the datatable
            'aoColumnsDefs': [
                // data & name: name of the columns, aTargets: num of td
                {'data': 'info', 'name': 'info', 'defaultContent': "", 'bVisible': true, 'aTargets': [0], 'sWidth': "1%", "sClass": "center", "bSortable": false},
                {'data': 'log_level', 'name': 'log_level', 'defaultContent': "", 'bVisible': true, 'aTargets': [1], 'sWidth': "5%"},
                {'data': 'node_name', 'name': 'node_name', 'defaultContent': "", 'bVisible': true, 'aTargets': [2], 'sWidth': "6%"},
                {'data': 'test_module', 'name': 'test_module', 'bVisible': true, 'defaultContent': "", 'aTargets': [3], 'sWidth': "20%"},
                {'data': 'traceback', 'name': 'traceback', 'bVisible': false, 'defaultContent': "", 'aTargets': [4]},
                {'data': 'filename', 'name': 'filename', 'bVisible': false, 'defaultContent': "", 'aTargets': [5]},
                {'data': 'test_name', 'name': 'test_name', 'bVisible': false, 'defaultContent': "", 'aTargets': [6]},
                {'data': 'time', 'name': 'time', 'defaultContent': "", 'bVisible': true, 'aTargets': [7], 'sWidth': "13%"},
                {'data': 'message', 'name': 'message', 'bVisible': true, 'defaultContent': "", 'aTargets': [8], 'sWidth': "55%"},
            ],
        }
    }

    $('.resize-font').on('click', function(){
        var type        = $(this).data('type');
        var size        = parseInt($('.table_logs tbody td').css('fontSize'));
        var size_detail = parseInt($('#jf-formattedJSON').css('fontSize'));

        switch (type) {
            case 'smaller':
                var font        = size - 1 + "px";
                var font_detail = size_detail - 1 + "px";

                $('.table_logs tbody td').css({'fontSize': font});
                $('#jf-formattedJSON').css({'fontSize': font_detail});
                break;

            case 'bigger':
                var font        = size + 1 + "px";
                var font_detail = size_detail + 1 + "px";

                $('.table_logs tbody td').css({'fontSize': font});
                $('#jf-formattedJSON').css({'fontSize': font_detail});
                break;

            case 'origin':
                $('.table_logs tbody td').css({'fontSize': "10px"});
                $('#jf-formattedJSON').css({'fontSize': "12px"});
                break;
        }
    })

    function get_current_table(){
        // Return the index of the current table
        if ($('#data_select').val() === 'waf')
            var type_table = "access";
        else if ($('#data_select').val() === 'packet_filter')
            var type_table = 'packet_filter';
        else if ($('#data_select').val() === 'vulture')
            var type_table = 'vulture';
        else if ($('#data_select').val() === 'diagnostic')
            var type_table = 'diagnostic';

        for (var x=0; x<all_tables.length; x++){
            if (all_tables[x].data('name') === type_table)
                return x;
        }

        return false;
    }

    $('.selected').on('click', function(){
        $(this).removeAttr('selected');
    })

    // Reinit datatable if the app has change
    $('#type_select').on('change', function(){
        init_control();
        $('#btn-reset').click();
        $('#btn-execute').click();
    });

    function rules_preview(){
        var sql = $('#querybuilder').queryBuilder('getSQL', false).sql;

        if (sql === "")
            sql = "None"

        var text = String.format("Query: {0}", sql)
        $('.preview_rules').val(text);
    }

    function init_config(){
        /// CHECK IF CONFIGURATION SAVED
        var columns_to_hide = sessionStorage.getItem('columns');
        if (columns_to_hide !== null){
            columns_to_hide = JSON.parse(columns_to_hide);
            for (var i in columns_to_hide)
                $('#'+columns_to_hide[i]).prop('checked', false);
        }

        $('.display_column').each(function(e){
            var iCol = $(this).data('column');

            if (!$(this).is(':checked')){
                data_table["access"]['aoColumnsDefs'][iCol]['bVisible'] = false;

            } else if (data_table["access"]['aoColumnsDefs'][iCol]['bVisible'] === false){
                data_table["access"]['aoColumnsDefs'][iCol]['bVisible'] = false;
                $(this).prop('checked', false);

            } else {
                data_table["access"]['aoColumnsDefs'][iCol]['bVisible'] = true;
            }
        })

        var config = sessionStorage.getItem('config');
        if (config !== null){
            config = JSON.parse(config)
            $('#hide_search_modal').prop('checked', config['hide_search_modal']);
            $('#show_detail_right').prop('checked', config['show_detail_right']);
        }
    }

    function init_control(){
        if ($('#data_select').val() === 'waf'){
            if ($('#app_select').val() === null || "access" === "") return;
            // Init the datatable
            // Permit to have infinite table and load them when a certain type of logs is selected
            var type_table = "access";
        } else if ($('#data_select').val() === 'packet_filter'){
            var type_table = 'packet_filter';
        } else if ($('#data_select').val() === 'vulture'){
            var type_table = 'vulture';
        } else if ($('#data_select').val() === 'diagnostic'){
            var type_table = 'diagnostic';
        }


        $('.row_table_logs').hide();
        $('#row_table_logs_'+type_table).show();

        // Remove all options in the filter select control
        $('#column_filter').find('option').remove();

        // Add options of the selected table in the filter select control
        var display_column = "";
        var columns_toggle = "";
        var all_columns    = data_table[type_table]['columns'].split(',');
        var aoColumns      = data_table[type_table]['aoColumnsDefs'];
        for (var i in all_columns){
            if (all_columns[i] !== '_id'){
                var show = true;
                for (var j in aoColumns){
                    if (aoColumns[j].name === all_columns[i])
                        show = aoColumns[j].bVisible;
                }

                var checked = ""
                if (show)
                    checked = "checked='checked'"

                display_column += String.format("<div class='col-sm-4'><div class='form-group'><span class='col-sm-6'>{0}</span><div class='col-sm-6'><div class='toggle-switch toggle-switch-primary'><label><input class='form-control display_column' value='{0}' data-column='{1}' id='{0}' {2} type='checkbox'/><div class='toggle-switch-inner'></div></label></div></div></div></div>", all_columns[i], i++, checked);
            }
        }

        $('#column_display').html(display_column);

        $('.display_column').on('change', function(){
            if ($(this).is(':checked'))
                all_tables[get_current_table()].fnSetColumnVis($(this).attr('data-column'), true);
            else
                all_tables[get_current_table()].fnSetColumnVis($(this).attr('data-column'), false);
        })

        if (jquery_builder !== null){
            // Reinit query builder
            rules_preview();
            $('#querybuilder').queryBuilder('destroy');
        }

        var app_selected = $('#app_select').val();
        // Prepare operators for query builder
        if (app_selected !== null){
            if ($('#app_select').val().split('|')[1] === 'elasticsearch'){
                var operators = ['equal', 'not_equal', 'less', 'less_or_equal', 'greater', 'greater_or_equal', 'between', 'in'];
            } else if ($('#app_select').val().split('|')[1] === 'mongodb'){
                var operators = ['equal', 'not_equal', 'in', 'not_in', 'less', 'less_or_equal', 'greater', 'greater_or_equal', 'between', 'not_between', 'begins_with', 'not_begins_with', 'contains', 'not_contains', 'ends_with', 'not_ends_with', 'is_empty', 'is_not_empty', 'is_null', 'is_not_null'];
            }
        }

        // Create filters for query builder
        var filters = [];
        $.each(data_table[type_table]['filters'], function(key, value){
            filters.push({
                'id'   : key,
                'label': key,
                'type' : value
            })
        })

        // Initialize query builder
        jquery_builder = $('#querybuilder').queryBuilder({
            filters       : filters,
            operators     : operators,
            allow_empty   : true,
            display_errors: false,
            icons         : {
                add_group   : 'fa fa-plus-square',
                add_rule    : 'fa fa-plus-circle',
                remove_group: 'fa fa-trash fa-2x',
                remove_rule : 'fa fa-trash fa-2x',
                error       : 'fa fa-exclamation-triangle',
            }
        });

        var switchery = new Switchery($('.js-switch'));
    }

    $('#btn-reset').on('click', reset_search);
    $('#btn-reset-2').on('click', reset_search);
    function reset_search(){
      $('#querybuilder').queryBuilder('reset');
      rules_preview();
      $('#save_filter').hide();
      $("#query_builder_filter").select2('val', '');
      $('#btn-add-dataset').hide();

      if (all_tables[get_current_table()] !== undefined)
          all_tables[get_current_table()].fnDraw();
    }

    $('#btn-execute').on('click', execute_search);
    $('#btn-execute-2').on('click', execute_search);
    function execute_search(){
        if (all_tables[get_current_table()] === undefined)
            init_table();

        if ($('#hide_search_modal').is(':checked'))
            $('#modal_search').modal('hide');

        rules_preview();
        all_tables[get_current_table()].fnDraw();
        $('#save_filter').show();

        $('#btn-export').show();
    }

    $('#btn-save-search').on('click', function(e){
        var result = $('#querybuilder').queryBuilder('getRules');
        var name   = $('#filter_name').val();

        if (result['condition'] === undefined){
            $('#alert_search_error').html("<p><i class='fa fa-times-circle'></i>&nbsp;&nbsp;Please build some search query before saving.</p>");
            $('#alert_search_error').show()

            setTimeout(function(){
                $('#alert_search_error').hide();
            }, 2000)
            return;
        }

        if (name === ""){
            $('#alert_search_error').html("<p><i class='fa fa-times-circle'></i>&nbsp;&nbsp;Please name the search before saving.</p>");
            $('#alert_search_error').show()

            setTimeout(function(){
                $('#alert_search_error').hide();
            }, 2000)
            return
        }

        var filter_id = null;
        if ($('#query_builder_filter').val() !== null)
            filter_id = $('#query_builder_filter').val().split('|')[0];

        var type_logs = "";
        if ($('#data_select').val() === 'waf')
            type_logs = "access";
        else if ($('#data_select').val() === 'packet_filter')
            type_logs = 'packet_filter';
        else if ($('#data_select').val() === 'vulture')
            type_logs = 'vulture';
        else if ($('#data_select').val() === 'diagnostic')
            type_logs = 'diagnostic';

        $.post(
            '/logs/savefilter/',
            {
                'filter_id': filter_id,
                'type_logs': type_logs,
                'filter'   : JSON.stringify(result),
                'name'     : name,
            },

            function(data){
                $('#alert_search_success').html('<p><i class="fa fa-check-circle"></i>&nbsp;&nbsp;Search saved</p>');
                $('#alert_search_success').show();
                $('#filter_name').val('');
                $('#save_filter').hide();

                if (filter_id !== null){
                    // Filter was updated
                    $('#access_filter option').each(function(){
                        if ($(this).val().split('|')[0] === filter_id)
                            $(this).remove();
                    })
                }
                $('#query_builder_filter').append(new Option(name, data['id']+"|"+JSON.stringify(result)));

                setTimeout(function(){
                    $('#alert_search_success').hide();
                }, 2000)
            }
        )
    });

    $('#btn-del-search').on('click', function(){
        var filter_id = $('#query_builder_filter').val().split('|')[0];
        $.post(
            '/logs/delfilter/',
            {'filter_id': filter_id},

            function(data){
                if (data['status'] === true){
                    $('#alert_search_success').html('<p><i class="fa fa-check-circle"></i>&nbsp;&nbsp;Search deleted.</p>');
                    $('#alert_search_success').show();
                    $('#query_builder_filter').select2("val", "");
                    $('#filter_name').val('');
                    $('#save_filter').hide();
                    $('#btn-execute').click();
                    setTimeout(function(){
                        $('#alert_search_success').hide();
                    }, 2000)
                }
            }
        )
    })

    /// Initialize the datatable
    function init_table(){
        var type_data = $('#data_select').val();
        init_control();
        init_config();

        if (type_data === 'waf'){
            var type_table = "access";
            // If table is alwready initialized or no app to select, return
            if (get_current_table() !== false || $('#app_select').val() === null)
                return;
        } else if (type_data === 'packet_filter'){
            var type_table = 'packet_filter';
            if (get_current_table() !== false)
                return;
        } else if ($('#data_select').val() === 'vulture'){
            var type_table = 'vulture';
            if (get_current_table() !== false)
                return;
        } else if ($('#data_select').val() === 'diagnostic'){
            var type_table = 'diagnostic';
            if (get_current_table() !== false)
                return;
        }


        /// DATATABLE settings
        settings = {
            "sDom": '<p<"top">t<"bottom"prli>',
            "oLanguage": {
                "sLengthMenu": '_MENU_',
                "oPaginate"  :{
                    "sNext"    : '',
                    "sPrevious": ''
                }
            },
            "bAutoWidth"    : true,
            "bServerSide"   : true,
            "bfilter"       : false,
            'iDisplayLength': 35,
            "order"         : data_table[type_table]['order'],
            "aLengthMenu"   : [[35, 50, 100, 150, 200], [35, 50, 100, 150, 200]],
            "bProcessing"   : true,
            'aaSorting'     : [[1, 'desc']],
            "aoColumnDefs"  : data_table[type_table]['aoColumnsDefs'],
            'sAjaxSource'   : '/logs/get',
            "sServerMethod" : "POST",
            "fnServerData": function(sSource, aoData, fnCallback){
                // Add several data
                aoData.push({'name': 'type_data', 'value': type_data})

                if (type_data === 'waf'){
                    aoData.push({'name': 'type_logs', 'value': "access"});
                    aoData.push({'name': 'app_id', 'value': $('#app_select').val().split('|')[0]});
                    var type_repo = $('#app_select').val().split('|')[1];

                } else if (type_data === 'packet_filter'){
                    aoData.push({'name': 'type_logs', 'value': 'packet_filter'});
                    aoData.push({'name': 'node', 'value': $('#node_select_pf').val().split('|')[0]});
                    var type_repo = $('#node_select_pf').val().split('|')[1];
                } else if (type_data === 'vulture'){
                    aoData.push({'name': 'type_logs', 'value': 'vulture'});
                    var type_repo = $('#repo_vulture').val();
                } else if (type_data === 'diagnostic'){
                    aoData.push({'name': 'type_logs', 'value': 'diagnostic'});
                    var type_repo = $('#repo_vulture').val();
                }

                var startDate = moment(reportrange.data('daterangepicker').startDate).format();
                var endDate   = moment(reportrange.data('daterangepicker').endDate).format();

                aoData.push({'name': 'startDate', 'value': startDate});
                aoData.push({'name': 'endDate', 'value': endDate});
                aoData.push({'name': 'columns', 'value': data_table[type_table]['columns']});

                if (type_repo === 'elasticsearch'){
                    var rules = $('#querybuilder').queryBuilder('getESBool');
                    aoData.push({'name': 'rules', 'value': JSON.stringify(rules)});
                } else if (type_repo === 'mongodb'){
                    var rules = $('#querybuilder').queryBuilder('getMongo');
                    aoData.push({'name': 'rules', 'value': JSON.stringify(rules)});
                }

                rules_preview();

                $.ajax({
                    "type"   : "POST",
                    "url"    : sSource,
                    "data"   : aoData,
                    "success": function(data, callback){
                        if (typeof(data) === 'string'){
                            window.location.href = window.location.href;
                        }
                        else if (typeof(data.aaData) === 'string') {
                            new PNotify({
                                title: 'Error',
                                text: data.aaData,
                                type: 'error',
                                styling: 'bootstrap3',
                                nonblock: {
                                    nonblock: true
                                }
                            });
                        } else {
                            fnCallback(data)

                            if ($('#data_select').val() === 'waf' && data.iTotalDisplayRecords > 0) {
                                $('#btn-add-dataset').show();
                            } else {
                                $('#btn-add-dataset').hide();
                            }

                        }
                    }
                })
            },
            "fnCreatedRow": function( nRow, aData, iDataIndex ) {

                if (type_data === 'vulture' || type_data === 'diagnostic'){
                    var couleur = {

                        'CRITICAL': {
                            'backgroundColor': '#d50000',
                            'color': '#fff !important',
                        },

                        'ERROR': {
                            'backgroundColor': '#ef5350',
                            'color': '#fff !important',
                        },

                        'WARNING': {
                            'backgroundColor': '#ffa726',
                            'color': '#fff !important',
                        },

                        'INFO': {
                            'backgroundColor': 'rgba(25, 123, 25, 0.62)',
                            'color': '#fff !important',
                        },

                        'DEBUG': {
                            'backgroundColor': '#003399',
                            'color': '#fff !important',
                        },

                        'NOTICE': {
                            'backgroundColor': '#993300',
                            'color': '#fff !important',
                        }
                    }

                    $($(nRow).find('td')[0]).css(couleur[aData['log_level']]);
                    $($(nRow).find('td')[1]).css(couleur[aData['log_level']]);

                    if (type_data === 'vulture')
                        $($(nRow).find('td')[5]).css({'textAlign': 'left'});
                    else if (type_data === 'diagnostic')
                        $($(nRow).find('td')[4]).css({'textAlign': 'left'});
                }

                $(nRow).click(function(e){

                    if ($('#show_detail_right').is(':checked')){
                        $('.table_logs tbody tr').removeClass('selected');
                        $('.table_logs tbody tr td').removeClass('row_selected');
                        $(this).addClass('selected');
                        $(nRow).find('td').each(function(){
                            $(this).addClass('row_selected');
                        })
                    } else {
                        if ($(this).hasClass('selected')){
                            $(this).removeClass('selected');
                            $(this).css('color', '#39454C !important');
                            $(nRow).find('td').each(function(){
                                $(this).removeClass('row_selected');
                            })
                        } else {
                            $(this).addClass('selected');
                            $(nRow).find('td').each(function(){
                                $(this).addClass('row_selected');
                            })
                        }
                    }

                    fnFormatDetails(iDataIndex, nRow);
                })
            }
        }

        var table = $('#table_logs_'+type_table).dataTable(settings)
        all_tables.push(table);
    }

    // Right click on security datatable show secondary menu
    $.contextMenu({
        // define which elements trigger this menu
        selector: "#table_logs_access tbody tr",
        autoHide: true,
        items: {
            wlbl: {name: 'Add to Blacklist / Whitelist', callback: function(key, opt){
                $(this).click();
                setTimeout(function(){
                    $('#add_wlbl').click();
                }, 200);
            }},
            find: {name: 'Find related rules', callback: function(key, opt){
                find_rules(this);
            }},
            pfbl: {name: 'Add this IP to Blacklist', callback: function(key, opt){
                $(this).click();
                add_packetfilter_rule(this);
            }}
        }
        // there's more, have a look at the demos and docs...
    });

    $.contextMenu({
        // define which elements trigger this menu
        selector: "#table_logs_packet_filter tbody tr",
        autoHide: true,
        items: {
            pfbl: {name: 'Add this IP to Blacklist', callback: function(key, opt){
                $(this).click();
                add_packetfilter_rule(this);
            }}
        }
    });

    function add_packetfilter_rule(tr){
        var src_ip = all_tables[get_current_table()].fnGetData(tr)['src_ip'];

        $.post(
            '/logs/blacklist_pf/',
            {'src_ip': src_ip,},

            function(response){
                if (response['status']){
                    new PNotify({
                        title: 'Success',
                        text: "Rule successfully created !",
                        type: 'success',
                        styling: 'bootstrap3',
                        nonblock: {
                            nonblock: true
                        }
                    });
                    $('#pf_reload').show();
                } else {
                    new PNotify({
                        title: 'Error',
                        text: response['reason'],
                        type: 'error',
                        styling: 'bootstrap3',
                        nonblock: {
                            nonblock: true
                        }
                    });
                }
            }
        )
    }

    function find_rules(tr){
        // Fetch all related rules from database
        var log_id = all_tables[get_current_table()].fnGetData(tr)['_id'];
        $('#table_edit_bl > tbody').empty();

        $.post(
            '/firewall/modsec_rules/get_rules_wl_bl/',
            {
                'app_id'   : $('#app_select').val().split('|')[0],
                'log_id'   : log_id,
                'type_logs': "access"
            },

            function(data){
                try{
                    var rules = JSON.parse(data['rules']);
                    // No rules found
                    if (!rules.length){
                        $('#error_no_rules').show();
                        setTimeout(function(){
                            $('#error_no_rules').hide();
                        }, 5000)
                        return;
                    }

                    // Foreach rule, create a line in table
                    for (var i in rules){
                        var rule = rules[i].split('|');
                        var html = String.format("<tr id='{0}'><td class='content'>{1}</td><td><a href='#' class='editrule' data-id='{0}'><span class='fa fa-edit'></span></a><a class='delrule' style='color:#EDEDED;' href='#' data-id='{0}'><i class='fa fa-trash fa-2x'></i></a></td></tr>", rule[0], rule[1]);
                        $('#table_edit_bl > tbody').append(html);
                    }

                    $('#modal_wlbl_edit').modal('show');

                    // Bind edit button
                    $('.editrule').on('click', function(){
                        var id = $(this).data('id');
                        $('#update_rule').show();
                        $('#id_rule').val(id);
                        $('#content_rule').val($('#'+id).find("td").text())
                    })

                    // Bind del button
                    $('.delrule').on('click', function(){
                        var id = $(this).data('id');
                        var url = "/firewall/modsec_rules/delete/"+id;

                        if (confirm("Confirm delete")){
                            $.post(
                                url,
                                {
                                    'confirm': 'yes',
                                    'json': true
                                },

                                function(data){
                                    if (data['status'] === true){
                                        $('#'+id).remove();

                                        // Remove the rule from table
                                        if ($('#table_edit_bl > tbody > tr').length === 0)
                                            $('#modal_wlbl_edit').modal('hide');

                                        // Show application reload button
                                        $('#app_reload').attr('href', "/management/reloadapp/" + $('#app_select').val().split('|')[0]);
                                        $('#app_reload').show();
                                    }
                                }
                            )
                        }
                    })

                } catch (Exception){
                    $('#error_no_rules').show();
                    setTimeout(function(){
                        $('#error_no_rules').hide();
                    }, 5000)
                }

            }
        )
    }

    function fnFormatDetails (nTr, nRow){
        /*  Function when click on a line in datatable
            Show the right panel visualisation
        */

        /// Create the undertable
        var aData          = all_tables[get_current_table()].fnGetData(nTr);
        var type_table     = "access";
        var formated_right = $('#show_detail_right').is(':checked');

        var template_line = "<span class='detail_info large'><span class='key'>{0}</span>=<span class='value'>{1}</span></span>";

        if (!formated_right){
            var sOut = "";
            var sEnd = [];
            $.each(aData, function(key, value){
                if (key !== 'info' && key !== '_id' && key !== 'time' && !key.match('^request_headers') && !key.match('^response_headers') && !key.match('^auditLogTrailer')){
                    sOut += String.format(template_line, key, value);
                } else if (key === 'time'){
                    var date = $.format.toBrowserTimeZone(value);
                    sOut += String.format(template_line, key, date);
                }else if (key.match('^request_headers')){
                    var request = JSON.parse(value);
                    var temp = "";
                    $.each(request, function(key2, value2){
                        temp += String.format(template_line, key2, value2);
                    })

                    sEnd.push(temp);
                } else if (key.match('^response_headers')){
                    var response = JSON.parse(value);
                    var temp = "";
                    $.each(response, function(key2, value2){
                        temp += String.format(template_line, key2, value2);
                    })

                    sEnd.push(temp);
                } else if (key.match('^auditLogTrailer')){
                    var auditLogTrailer = JSON.parse(value);
                    var temp = "";
                    $.each(auditLogTrailer, function(key2, value2){
                        temp += String.format(template_line, key2, value2);
                    })

                    sEnd.push(temp);
                }
            });

            sOut += "<br/>" + sEnd.join('<br/>');
            var i = $(nRow).find('i');
            if (all_tables[get_current_table()].fnIsOpen(nTr)){
                all_tables[get_current_table()].fnClose(nTr);
                $(nRow).children('td').css({'color': "#EDEDED"});
                $(i[0]).show();
                $(i[1]).hide();

            } else {
                all_tables[get_current_table()].fnOpen(nTr, sOut, 'details');
                $(nRow).children('td').css({'color': "#FFC312"});
                $(i[0]).hide();
                $(i[1]).show();
            }

        } else {
            var request_headers_user_agent;

            var request_headers_host;
            switch(all_tables[get_current_table()].data('name')){
                case "access":
                    $('#div_access').removeClass('col-xs-12');
                    $('#div_access').addClass('col-xs-9');

                    $('#access_details_logs').show();
                    $('#access_details_logs_data').jsonFrill({toolbar : false}, JSON.stringify(aData));

                    break;

                case "packet_filter":
                    $('#div_packet_filter').removeClass('col-xs-12');
                    $('#div_packet_filter').addClass('col-xs-9');
                    $('#packet_filter_details_logs').show();
                    $('#packet_filter_details_logs_data').jsonFrill({toolbar: false}, JSON.stringify(aData));

                    break;

                case 'vulture':
                    $('#div_vulture').removeClass('col-xs-12');
                    $('#div_vulture').addClass('col-xs-9');
                    $('#vulture_details_logs').show();
                    $('#vulture_details_logs_data').jsonFrill({toolbar: false}, JSON.stringify(aData));

                    break;

                case 'diagnostic':
                    $('#div_diagnostic').removeClass('col-xs-12');
                    $('#div_diagnostic').addClass('col-xs-9');
                    $('#diagnostic_details_logs').show();
                    $('#diagnostic_details_logs_data').jsonFrill({toolbar: false}, JSON.stringify(aData));

                    break;
            }
        }

        if (all_tables[get_current_table()].data('name') === 'access'){
            $('body').append('<a id="add_wlbl" style="display:none;" class="add_wlbl" data-id="'+aData['_id']+'">BlackList / WhiteList</a>')

            var data = {
                'network': [
                    'remote_addr='+aData['src_ip'],
                    'request_protocol='+aData['incoming_protocol'],
                ],
                'request': [
                    'http_method='+aData['http_method'],
                    'request_uri='+aData['requested_uri'],
                ],

                'request_data_post': [],
                'request_data_get' : [],
            };

            // Preparing Data GET
            try{
                var data_get = aData['requested_uri_full'].split('?')[1].split('&');
            } catch (Exception){
                var data_get = [];
            }

            for (var row in data_get)
                data['request_data_get'].push(data_get[row]);

            // Bind Blacklist / Whitelist button
            $('.add_wlbl').on('click', function(){
                $('.table_rule tbody').html('');
                $('.enable_all_rule').prop('checked', false);
                $('#modal_wlbl .modal-dialog').css('width', '90%');
                $('#modal_wlbl').modal('show');

                prepare_rules(data);
                createRules();
            })
        }



        $('.detail_info').on('click', function(){
            var rules = $('#querybuilder').queryBuilder('getRules');
            var rule  = null;

            if ($('#show_detail_right').is(':checked')){
                var key   = $(this).find('.key').text();
                var value = $(this).find('.value').text();
            } else {
                var key   = $(this).text().split('=')[0];
                var value = $(this).text().split('=')[1];
            }

            if ($('#data_select').val() === 'waf')
                var type_table = "access";
            else
                var type_table = $('#data_select').val();

            $.each(data_table[type_table]['filters'], function(k, type){
                if (key === k){
                    var operator = type === 'string' ? 'equal' : 'equal';
                    rule  = {
                        "condition": "AND",
                        'rules': [{
                            'id'      : key,
                            'field'   : key,
                            'input'   : type,
                            'operator': operator,
                            'value'   : value
                        }]
                    }
                }
            })

            if (jQuery.isEmptyObject(rules))
                rules = rule;
            else
                rules['rules'].push(rule)

            $('#querybuilder').queryBuilder('setRules', rules);
            rules_preview();
        });
    }

    $('.addline').bind('click', add_line);
    function add_line(data, id_table){
        /* Add a rule in rules datatable
        */
        // 0: id_table
        // 1: checked
        // 2: boolean
        // 3: value
        // 4: control
        // 5: field
        // 6: action
        // 7: delete
        var tr_str = "<tr class='line_{0}'><td><input type='checkbox' class='enable_{0} enable_rule' {1}/></td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>THEN</td></td><td>{6}</td><td>{7}</td></tr>";
        var boolean = "<select class='form-control boolean_{0} enable_rule'><option value=''>If</option><option value='!'>If Not</option></select>";
        var control = "<select class='form-control control_{0} enable_rule'><option value='@beginsWith'>is found at the beginning in</option><option selected='selected' value='@contains'>is found anywhere in</option><option value='@containsWord'>(with word boundaries) is found anywhere in</option><option value='@ipMatch'>Match IPAddress (v4 & v6)</option><option value='@endsWith'>is found at the end in</option><option value='@eq'>is equal to</option><option value='@ge'>is greater than or equal to</option><option value='@gt'>is greater than</option><option value='@le'>is less or equal than</option><option value='@lt'>is less than</option></select>";
        var action_input = "<select class='form-control action_{0} enable_rule'><option value='deny'>Blacklist</option><option value='allow'>Whitelist</option></select>";
        var value_input  = "<input type='text' class='form-control value_{0} enable_rule' value='{1}'/>"
        var field_input  = "<input type='text' class='form-control field_{0} enable_rule' value='{1}' {2}/>"
        var delete_input = "<a href='#' class='del_{0} del_rule enable_rule' data-id='{0}'><i class='fa fa-trash-o'></i></a>"

        var field   = "";
        var value   = "";
        var checked = "checked='checked'";
        var readonly = "";

        if (typeof(data) === 'string'){
            // Initialisation of the table, fields are set
            field   = data.split('=')[0].toUpperCase();
            value   = data.split('=')[1];
            checked = "";

        } else {
            var id_table = $(this).data('id');
        }

        if (id_table === 'request_data_get' || id_table === 'request_data_post'){
            control = "<select class='form-control control_{0} enable_rule'><option value='@beginsWith'>is found at the beginning in</option><option selected='selected' value='@contains'>is found anywhere in</option><option value='@containsWord'>(with word boundaries) is found anywhere in</option><option value='@endsWith'>is found at the end in</option><option value='@eq'>is equal to</option><option value='@ge'>is greater than or equal to</option><option value='@gt'>is greater than</option><option value='@le'>is less or equal than</option><option value='@lt'>is less than</option></select>";
            field = field.toLowerCase();

        } else if (id_table === 'network' || id_table === 'request'){
            readonly = "readonly='readonly'";
        }

        var table    = '#table_' + id_table;
        boolean      = String.format(boolean, id_table);
        control      = String.format(control, id_table);
        value_input  = String.format(value_input, id_table, value);
        field_input  = String.format(field_input, id_table, field, readonly);
        delete_input = String.format(delete_input, id_table);


        $(table + " tbody").append(String.format(tr_str, id_table, checked, boolean, value_input, control, field_input, action_input, delete_input));
        $('.enable_rule').on('change', enable_rule);
        $('.del_rule').on('click', del_rule);
    }

    function prepare_rules(data){
        // Construct all table with values
        for (var row in data['network'])
            add_line(data['network'][row], 'network');

        for (var row in data['request'])
            add_line(data['request'][row], 'request');

        for (var row in data['request_data_post'])
            add_line(data['request_data_post'][row], 'request_data_post');

        for (var row in data['request_data_get'])
            add_line(data['request_data_get'][row], 'request_data_get');

        for (var row in JSON.parse(data['request_headers']))
            add_line(String.format("{0}={1}", row.toUpperCase(), JSON.parse(data['request_headers'])[row]), 'request_headers');
    }

    function createRules(){
        // Build a rule from data in table
        var rule      = 'SecRule {0} "{1}{2} {3}" "id:{id},{4},{5},msg:\'{6}\'"\n';
        var rule_data = 'SecRule {0}{1} "{2}{3} {4}" "id:{id},{5},{6},msg:\'{7}\'"\n';
        var rules_bl  = new Array();
        var rules_wl  = new Array();

        var msg = {
            'deny' : 'BLACKLIST',
            'allow': 'WHITELIST'
        }

        var log_mode = null;
        var table_id = ['network', 'request', 'request_data_get'];
        var app_id   = $('#app_select').val().toString().split('|')[0];
        for (var x=0; x<logging_control.length; x++){
            for (var key in logging_control[x]){
                if (key === app_id)
                    log_mode = logging_control[x][key];
            }
        }

        if (log_mode === null){
            // No modsec policy for this app
            PNotify.removeAll();
            new PNotify({
                title: 'Error',
                text: 'No ModSec Policy found for this application.',
                type: 'error',
                styling: 'bootstrap3',
                nonblock: {
                    nonblock: true
                }
            });
            $('#add_rule').hide();
            return;
        }

        $('#add_rule').show();
        for (row in table_id){
            // Foreach table
            var table        = table_id[row];
            var length_table = $('#table_'+table+" tbody tr").length;

            $('#table_'+table+" tbody tr").each(function(){
                var td = $(this).children('td');

                var enable = $(td[0]).children()[0];
                if ($(enable).is(':checked')){
                    var boolean = $($(td[1]).children()[0]).val();
                    var value   = $($(td[2]).children()[0]).val();
                    var control = $($(td[3]).children()[0]).val();
                    var field   = $($(td[4]).children()[0]).val().toUpperCase();
                    var action  = $($(td[6]).children()[0]).val();

                    if (value !== ""){
                        if (table === 'request_data_get'){
                            if (field !== '') field = ":"+field;
                            var temp_rule = String.format(rule_data, 'ARGS_GET', field, boolean, control, value, action, log_mode, msg[action]);

                            if (action === 'deny') rules_bl.push(temp_rule);
                            else rules_wl.push(temp_rule)


                        } else {
                            var temp_rule = String.format(rule, field, boolean, control, value, action, log_mode, msg[action]);
                            if (action === 'deny'){
                                rules_bl.push(temp_rule);
                            } else {
                                rules_wl.push(temp_rule)
                            }
                        }
                    }
                }
            })
        }

        $('#preview_bl').text('');
        $('#preview_wl').text('');
        if (rules_bl.length >= 1)
            $('#preview_bl').text(rules_bl.join(""));

        if (rules_wl.length >= 1)
            $('#preview_wl').text(rules_wl.join(""));
    };

    $('#add_rule').on('click', function(){
        // Add the rules to the database
        if ($('#preview_bl').text() === "" && $('#preview_wl').text() === ""){
            new PNotify({
                title: 'Error',
                text: 'Please build rules before saving.',
                type: 'error',
                styling: 'bootstrap3',
                nonblock: {
                    nonblock: true
                }
            });
            return;
        }

        var app_id = $('#app_select').val().split('|')[0];
        $.post(
            '/firewall/modsec_rules/add_rules_wl_bl/',
            {
                'app_id'   : app_id,
                'blacklist': $('#preview_bl').text(),
                'whitelist': $('#preview_wl').text(),
            },

            function(data){
                if (data['done'] === true){
                    new PNotify({
                        title: 'Success',
                        text: 'Rules created !',
                        type: 'success',
                        styling: 'bootstrap3',
                        nonblock: {
                            nonblock: true
                        }
                    });

                    setTimeout(function(){
                        $('#preview').html('');
                        $('#modal_wlbl').modal('hide');
                        $('#app_reload').attr('href', "/management/reloadapp/" + $('#app_select').val().split('|')[0]);
                        $('#app_reload').show();
                    }, 1000);
                }
            }
        )
    });

    $('.del_rule').on('click', del_rule);
    function del_rule(){
        $($(this).parents('tr')).remove();
        createRules();
    }

    $('.enable_all_rule').on('change', function(){
        var id = $(this).data('id');
        if ($(this).is(':checked')){
            $('.enable_'+id).prop('checked', true);
            $('.enable_'+id).trigger('change');
        } else {
            $('.enable_'+id).prop('checked', false);
            $('.enable_'+id).trigger('change');
        }
    })

    $('.enable_rule').on('change', enable_rule);
    function enable_rule(){
        var line  = $(this).parents('tr');
        var td    = $(line).children()[0];
        var input = $(td).children()[0];
        $(input).attr('checked', 'checked');
        createRules();
    }

    $('#real_time').on('click', function(){
        // Hide or show reportrange/pagination controls and ajax loader information
        if ($(this).data('active')){
            $(this).removeClass('btn-warning').addClass('btn-default');
            $('#spinner_ajax').removeClass('fa-pulse');
            $('#reportrange_logs').prop('disabled', false);
            $(this).data('active', false);
        } else {
            $(this).removeClass('btn-default').addClass('btn-warning');
            $('#spinner_ajax').addClass('fa-pulse');
            $('#reportrange_logs').prop('disabled', true);
            $(this).data('active', true);
        }
    });

    setInterval(function(){
        // REAL TIME ! Every 2 secs
        if ($('#real_time').data('active')){
            all_tables[get_current_table()].fnDraw();
        }
    }, 2000);

    $('#table_logs_length select').addClass('form-control');

    $('.wlbl').on('change', change_wlbl);
    change_wlbl();
    function change_wlbl(){
        $('.wlbl').each(function(){
            if ($(this).is(':checked'))
                $('#add_rule').val('Add to '+$(this).data('val'));
        })
    }

    $('#update_rule_btn').on('click', function(){
        /* Update the content of a rule
        */
        var id = $('#id_rule').val();
        var content = $('#content_rule').val();

        $.ajax({
              type: "POST",
              url: "/firewall/modsec_rules/editfile/" + id,
              cache: false,
              data: JSON.stringify({content: content}),
              dataType: "json",
              contentType: "application/json",
              success: function(data){
                if (data['status'] === 'OK'){
                    $($('#'+id).find("td")[0]).text(content);
                    $('#content_rule').val('');
                    $('#id_rule').val('');
                    $('#update_rule').hide();

                    $('#app_reload').attr('href', "/management/reloadapp/" + $('#app_select').val().split('|')[0]);
                    $('#app_reload').show();
                }
              }
         });
    })

    $('#cancel_rule_btn').on('click', function(){
        $('#content_rule').val('');
        $('#id_rule').val('');
        $('#update_rule').hide();
    });

    $('#query_builder_filter').on('change', function(){
        // Select a saved search
        var data = $('#query_builder_filter').val();
        if (data === null){
            $('#btn-reset').click();
            return;
        }

        var rules = data.split('|')[1];
        rules = JSON.parse(rules);
        $('#querybuilder').queryBuilder('setRules', rules);
        $('#filter_name').val(data.text)
        $('#btn-del-search').show();

    });

    $('#btn-add-dataset').on('click', function(){
        var type_repo    = $('#app_select').val().split('|')[1];
        var type_select  = "access";
        var app_id       = $('#app_select').val().split('|')[0];
        var current_date = new Date()
        var app_name     = $('#app_select').val().split('|')[2];

        if (type_repo === 'elasticsearch'){
            var search = $('#querybuilder').queryBuilder('getESBool');
        } else if (type_repo === 'mongodb'){
            var search = $('#querybuilder').queryBuilder('getMongo');
        }

        var date = {
            'startDate':moment(reportrange.data('daterangepicker').startDate).format(),
            'endDate': moment(reportrange.data('daterangepicker').endDate).format()
        };

        $.post(
            '/dataset/add/',
            {
                'app_id'      : app_id,
                'dataset_name': current_date.getFullYear().toString()+"-"+(current_date.getMonth()+1).toString()+"-"+current_date.getDate().toString()+"-"+app_name,
                'type_select' : type_select,
                'search'      : JSON.stringify(search),
                'date'        : JSON.stringify(date),
            },

            function(data){
                if (data['status'] === true){
                    $('#btn-add-dataset').hide();

                    new PNotify({
                        title: 'Success',
                        text: 'Dataset successfully created !',
                        type: 'success',
                        styling: 'bootstrap3',
                        nonblock: {
                            nonblock: true
                        }
                    });

                }
            }
        )
    });

    $('#btn-save-config').on('click', function(){
        //Save configuration
        var columns_to_hide = [];
        $('.display_column').each(function(){
            if (!$(this).is(':checked'))
                columns_to_hide.push($(this).val());
        })

        var config = {
            'hide_search_modal': $('#hide_search_modal').is(':checked'),
            'show_detail_right': $('#show_detail_right').is(':checked'),
        }

        sessionStorage.setItem('columns', JSON.stringify(columns_to_hide));
        sessionStorage.setItem('config', JSON.stringify(config));

        $('#config_success').show();
        setTimeout(function(){
            $('#config_success').hide();
            $('#modal_config').modal('hide');
        }, 2000);
    })

    $('#type_select').select2({
        minimumResultsForSearch: Infinity,
    });
    $('#data_select').select2({
        minimumResultsForSearch: Infinity,
    });

    $('#node_select_pf').select2({
        minimumResultsForSearch: Infinity,
    });
    $('#app_select').select2();

    $('#app_select').on('change', function(){
        all_tables[get_current_table()].fnDraw();
    })

    $('#data_select').on('change', function(){
        if ($(this).val() === 'waf'){
            $('.waf_select').show();
            $('.node_select_pf').hide();
        } else if ($(this).val() === 'packet_filter'){
            $('.waf_select').hide();
            $('.node_select_pf').show();
        } else if ($(this).val() === 'vulture'){
            $('.waf_select').hide();
            $('.node_select_pf').hide();
        } else if ($(this).val() === 'diagnostic'){
            $('.waf_select').hide();
            $('.node_select_pf').hide();
        }

        init_control();
        init_table();
    })

    $('#node_select_pf').on('change', function(){
        all_tables[get_current_table()].fnDraw();
    })

    $('#query_builder_filter').select2({
        ajax: {
            url     : '/logs/getfilter/',
            type    : 'POST',
            dataType: 'json',
            cache   : true,
            data: function(params){
                var type_logs = "";
                if ($('#data_select').val() === 'waf')
                    type_logs = "access";
                else if ($('#data_select').val() === 'packet_filter')
                    type_logs = 'packet_filter';
                else if ($('#data_select').val() === 'diagnostic')
                    type_logs = 'diagnostic';
                else if ($('#data_select').val() === 'vulture')
                    type_logs = 'vulture';

                var term = params.terms;
                if (term === undefined)
                    term = "";

                var x = {
                    'search'   : term,
                    'type_logs': type_logs
                }

                return x;
            },
            results: function(data, page){
                return data
            }
        },
        // minimumResultsForSearch: Infinity,
        placeholder: "Select a saved search",
        allowClear: true
    }).on('change', function(e){
        $('#save_filter').show();
        rules_preview();
    })

    $('.btn-open-panel').on('click', function(){
        if ($(this).data('open')){
            $('#'+$(this).data('panel')).hide();
            $(this).html("<i class='fa fa-chevron-up'></i>");
            $(this).data('open', false);
        } else {
            $('#'+$(this).data('panel')).show();
            $(this).html("<i class='fa fa-chevron-down'></i>");
            $(this).data('open', true);
        }
    });

    $('.close_detail').on('click', function(){
        $('#div_access').removeClass('col-xs-9');
        $('#div_access').addClass('col-xs-12');
        $('#div_packet_filter').removeClass('col-xs-9');
        $('#div_packet_filter').addClass('col-xs-12');
        $('#div_vulture').removeClass('col-xs-9');
        $('#div_vulture').addClass('col-xs-12');
        $('#div_diagnostic').removeClass('col-xs-9');
        $('#div_diagnostic').addClass('col-xs-12');

        $('#access_details_logs').hide();
        $('#packet_filter_details_logs').hide();
        $('#vulture_details_logs').hide();
        $('#diagnostic_details_logs').hide();
    })

    $('#btn-export').on('click', function(){
        if ($('#data_select').val() === 'waf'){
            var params = {
             'app_id'   : $('#app_select').val().split('|')[0],
             'type_repo': $('#app_select').val().split('|')[1],
             'app_name' : $('#app_select').val().split('|')[2],
             'type_logs': "access",
             'type_data': 'waf',
            }

        } else if ($('#data_select').val() === 'packet_filter'){
            var params = {
                'type_logs': 'packet_filter',
                'node'     : $('#node_select_pf').val().split('|')[0],
                'type_repo': $('#node_select_pf').val().split('|')[1],
                'type_data': 'packet_filter',
            }

        } else if ($('#data_select').val() === 'vulture'){
            var params = {
                'type_logs': 'vulture',
                'type_data': 'vulture',
                'type_repo': $('#repo_vulture').val(),
            }
        } else if ($('#data_select').val() === 'diagnostic'){
            var params = {
                'type_logs': 'diagnostic',
                'type_data': 'diagnostic',
                'type_repo': 'mongodb',
            }
        }

        if (params['type_repo'] === 'elasticsearch')
            params['rules'] = JSON.stringify($('#querybuilder').queryBuilder('getESBool'));
        else if (params['type_repo'] === 'mongodb')
            params['rules'] = JSON.stringify($('#querybuilder').queryBuilder('getMongo'));

        params['date'] = JSON.stringify({
            'startDate':moment(reportrange.data('daterangepicker').startDate).format(),
            'endDate': moment(reportrange.data('daterangepicker').endDate).format()
        });

        $.post(
            '/logs/export/',
            params,

            function(response){
                if (response['status']){
                    window.location.href = '/logs/export/';
                } else {
                    new PNotify({
                        title: 'Error',
                        text: response['reason'],
                        type: 'error',
                        styling: 'bootstrap3',
                        nonblock: {
                            nonblock: true
                        }
                    });
                }
            }
        )
    })

    if ($('#data_select').val() === 'waf'){
        $('.waf_select').show();
        $('.node_select_pf').hide();
    } else if ($('#data_select').val() === 'packet_filter'){
        $('.waf_select').hide();
        $('.node_select_pf').show();
    } else if ($('#data_select').val() === 'vulture'){
        $('.waf_select').hide();
        $('.node_select_pf').hide();
    } else if ($('#data_select').val() === 'diagnostic'){
        $('.waf_select').hide();
        $('.node_select_pf').hide();
    }

    init_table();

    $("#pf_reload").click(function(e) {
        var url = "/services/pf/restart/";

        var btn = this;

        $($(btn).find('i')[0]).addClass('fa-spin');
        e.preventDefault();
        $.ajax({
            url: url,
            type: 'GET',
            success: function(data){
                $($(btn).find('i')[0]).removeClass('fa-spin');
                new PNotify({
                    title: 'Success',
                    text: 'Packet Filter successfully restart !',
                    type: 'success',
                    styling: 'bootstrap3',
                    nonblock: {
                        nonblock: true
                    }
                });
                $('#pf_reload').hide();
            },
            error: function(data) {
                $($(btn).find('i')[0]).removeClass('fa-spin');
                new PNotify({
                    title: 'Error',
                    text: 'An error occurred',
                    type: 'error',
                    styling: 'bootstrap3',
                    nonblock: {
                        nonblock: true
                    }
                });

                $('#pf_reload').hide();
            }
        });
    });
});
