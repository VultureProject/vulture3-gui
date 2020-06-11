$(function() {
    var mainrules = {
        '2'   : ['Big request', ''],
        '10'   : ['Uncommon hex encoding', '%00'],
        '17'   : ['Libinjection SQL', ''],
        '18'   : ['Libinjection XSS', '&ltscript&gt'],
        '1000': ['sql keywords', new RegExp('select|union|update|delete|insert|table|from|ascii|hex|unhex|drop', 'g')],
        '1001': ['double quote', '&quot;'],
        '1002': ['0x, possible hex encoding', '0x'],
        '1003': ['mysql comment (/*)', '/*'],
        '1004': ['mysql comment (*/)', '*/'],
        '1005': ['mysql keyword (|)', '|'],
        '1006': ['mysql keyword (&&)', '&&'],
        '1007': ['mysql comment (--)', '--'],
        '1008': ['semicolon', ';'],
        '1009': ['equal sign in var', '&#61;'],
        '1010': ['open parenthesis', '('],
        '1011': ['close parenthesis', ')'],
        '1013': ['simple quote', "'"],
        '1015': ['comma', ','],
        '1016': ['mysql comment (#)', '&#35;'],
        '1017': ['double arobase (@@)', '@@'],

        '1100': ['http:// scheme', 'http://'],
        '1101': ['https:// scheme', 'https://'],
        '1102': ['ftp:// scheme', 'ftp://'],
        '1103': ['php:// scheme', 'php://'],
        '1104': ['sftp:// scheme', 'sftp://'],
        '1105': ['zlib:// scheme', 'zlib://'],
        '1106': ['data:// scheme', 'data://'],
        '1107': ['glob:// scheme', 'glob://'],
        '1108': ['phar:// scheme', 'phar://'],
        '1109': ['file:// scheme', 'file://'],
        '1110': ['gopher:// scheme', 'gopher://'],

        '1200': ['..', 'double dot'],
        '1202': ['unix file probe', '/etc/passwd'],
        '1203': ['windows path', 'c:\\\\'],
        '1204': ['cmd probe', 'cmd.exe'],
        '1205': ['backslash', '\\'],

        '1302': ['html open tag', '&lt;'],
        '1303': ['html close tag', '&gt;'],
        '1310': ['open square backet ([)', '['],
        '1311': ['close square bracket (])', ']'],
        '1312': ['tilde (~)', '~'],
        '1314': ['grave accent (`)', '`'],
        '1315': ['double encoding', new RegExp('%[2|3].', 'g')],

        '1400': ['utf7/8 encoding', '&#'],
        '1401': ['M$ encoding', '%u'],

        '1500': ['asp/php file upload', new RegExp('\.ph|\.asp|\.ht', 'g')]
    };

    function escapeHtml(string) {
        if (!string) return "";
        return string.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/"/g, '&quot;')
            .replace(/>/g, '&gt;')
            .replace(/#/g, '&#35;')
            .replace(/=/g, '&#61;');
    }

    function highlight(data, rule_id) {
        var description = rule_id + ": " + mainrules[rule_id][0];
        var pattern = mainrules[rule_id][1];
        if (pattern instanceof RegExp) {
            var match, matches = [];
            while ((match = pattern.exec(data)) !== null) {
                matches.unshift([match.index, match[0].length]);
            }
            for (var ii = 0; ii < matches.length; ii++) {
                var p = matches[ii][0];
                var len = matches[ii][1];
                data = data.substr(0, p + len) + '</span>' + data.substr(p + len);
                data = data.substr(0, p) + '<span class="pattern" data-toggle="tooltip" title="' + description + '">' + data.substr(p);
            }
            return data;
        } else if( pattern != "" && pattern != undefined ) {
            var indexes = [];
            for (var position = data.toLowerCase().indexOf(pattern); position !== -1; position = data.indexOf(pattern, position + pattern.length)) {
                indexes.unshift(position);
            }
            for (var iii = 0; iii < indexes.length; iii++) {
                var pos = indexes[iii];
                data = data.substr(0, pos + pattern.length) + '</span>' + data.substr(pos + pattern.length);
                data = data.substr(0, pos) + '<span class="pattern" data-toggle="tooltip" title="' + description + '">' + data.substr(pos);
            }
            return data;
        }
    }

    function mk_cell(zone) {
        return function(data, type, row) {
            var res = "";
            var entries = arrangeVar(row);
            for (var i = 0; i < entries.length; i++) {
                var ent = entries[i];
                if (ent.zone === zone) {
                    var val = escapeHtml(ent.content);
                    for (var k = 0; k < ent.ids.length; k++) {
                        var rule_id = ent.ids[k];
                        try {
                            val = highlight(val, rule_id);
                        }catch(err) {
                            console.log("Undefined rule id : "+rule_id);
                        }
                    }
                    if (ent.effective_zone !== "HEADERS" && ent.zone !== "URL") {
                        res += escapeHtml(ent.var_name) + " = ";
                    }
                    res += val + "<br>";
                } else if (ent.zone === zone + "|NAME") {
                    var variable = escapeHtml(ent.var_name);
                    for (var kk = 0; kk < ent.ids.length; kk++) {
                        var id = ent.ids[kk];
                        variable = highlight(variable, id);
                    }
                    res += variable + " = " + escapeHtml(ent.content) + "<br>";
                }
            }
            return res;
        }
    }

    var datasetCollectionName = $('.dataset').attr('id');

    var settings = {
        "sDom": '<p<"top">t<"bottom"prli>',
        'sPaginationType': 'bootstrap',
        "oLanguage": {
            "sLengthMenu": '_MENU_',
            "oPaginate":{
                "sNext": '',
                "sPrevious": ''
            }
        },
        "bAutoWidth"    : true,
        "aoColumnDefs"  : [
            {'data': 'check', 'name': 'check', 'defaultContent': "", 'aTargets': [0], 'sWidth': "0.05%", "bSortable": false, "mRender": function(data) {
                return "<input class='select_logs' type='checkbox' class='form-control'>";
            }},
            {'data': 'time', 'bVisible': true, 'className': "cell-shrink", 'aTargets': [1], 'sWidth': "20%", "mRender": function(data) {
                return new Date(data * 1e3);
            }},
            {'data': 'unparsed_uri', 'bVisible': true, 'className': "cell-shrink", 'aTargets': [2], 'sWidth': "20%", "mRender": escapeHtml},
            {'bVisible': true, 'className': "cell-shrink", 'aTargets': [3], 'sWidth': "20%", "mRender": mk_cell("URL")},
            {'bVisible': true, 'className': "cell-shrink", 'aTargets': [4], 'sWidth': "20%", "mRender": mk_cell("HEADERS")},
            {'bVisible': true, 'className': "cell-shrink", 'aTargets': [5], 'sWidth': "20%", "mRender": mk_cell("ARGS")},
            {'bVisible': true, 'className': "cell-shrink", 'aTargets': [6], 'sWidth': "20%", "mRender": mk_cell("BODY")}
        ],
        "createdRow": function(row, data, dataIndex) {
            if (data['whitelisted'] === "false") {
                $(row).addClass('not-whitelisted-row');
            } else {
                $(row).addClass('whitelisted-row');
            }
        },
        "drawCallback": function() {
            $('[data-toggle="tooltip"]').tooltip();
            $('.select_logs').click(function(event) {
                event.stopPropagation();
            });
            $(".fa-spinner").hide();
        },
        "bfilter"       : false,
        'iDisplayLength': 10,
        'iDisplayLength': 10,
        "aLengthMenu": [
            [10, 50, 100],
            [10, 50, 100]
        ],
        "bProcessing"   : true,
        'aaSorting'     : [[1, 'desc']],
        'sAjaxSource'   : '/dataset/get_learning',
        "fnServerData": function(sSource, aoData, fnCallback) {
            $(".fa-spinner").show("fast");
            aoData.push({'name': 'dataset_collection_name', 'value': datasetCollectionName});
            $.ajax({
                "type"    : "POST",
                "url"     : sSource,
                "data"    : aoData,
                "success" : fnCallback
            })
        }
    };

    var $table_dataset = $('#table_dataset');
    var table = $table_dataset.dataTable(settings);

    $('#checkall').change(function () {
        $('.select_logs').prop('checked', this.checked);
    });

    $('#remove_logs').on('click', function () {
        var to_remove = [];
        var to_remove_els = [];
        $('.select_logs').each(function () {
            if ($(this).is(':checked')) {
                var el = $(this).closest("tr");
                var oid = table.fnGetData(el)['_id'];
                to_remove.push(oid);
                to_remove_els.push(el);
            }
        });

        $.post('/dataset/logs/remove_learning', {
                'dataset_collection_name': datasetCollectionName,
                'to_remove': JSON.stringify(to_remove)
            }, function (data) {
                if (data['status'] === true){
                    for(el of to_remove_els){
                        table.fnDeleteRow(el);
                    }
                } else {
                    new PNotify({
                        title: 'Error',
                        text: '<a style="color: white; text-decoration: underline;">Failed to delete rule(s) \n' + data['message'],
                        type: 'error',
                        styling: 'bootstrap3',
                        buttons: {
                            closer: true,
                            sticker: false
                        }
                    });
                }
            });
    });

    $.contextMenu({
        selector: "#table_dataset tbody tr",
        autoHide: false,
        items: {
            wl: {name: 'Whitelist', callback: function(key, opt){
                showWLWin(this);
            }}
        }
    });

    $table_dataset.find('tbody').on('click', 'tr', function () {
        showWLWin(this);
    });

    function regexify(str) {
        var rx = str.replace(/\(/g, "\\(");
        rx = rx.replace(/\)/g, "\\)")
            .replace(/{/g, "\\{")
            .replace(/}/g, "\\}")
            .replace(/\[/g, "\\[")
            .replace(/]/g, "\\]")
            .replace(/\./g, "\\.")
            .replace(/\*/g, "\\*")
            .replace(/\+/g, "\\+")
            .replace(/\?/g, "\\?")
            .replace(/-/g, "\\-")
            .replace(/&/g, "\\&")
            .replace(/\|/g, "\\|")
            .replace(/</g, "\\<")
            .replace(/>/g, "\\>")
            .replace(/\^/g, "\\^")
            .replace(/\$/g, "\\$")

            .replace(/(\d+)/g, "\\d+");
        return rx;
    }

    function arrangeVar(obj) {
        var entries = [];
        for (var ridx = 0; ridx < 10; ridx++) {
            if (!obj.hasOwnProperty('id' + ridx + '_0'))
                break;

            var entry = {ids: []};
            for (var ridx2 = 0; ridx2 < 10; ridx2++) {
                if (!obj.hasOwnProperty('id' + ridx + '_' + ridx2))
                    break;
                entry.ids.push(obj['id' + ridx + '_' + ridx2]);
            }
            entry.zone = obj['zone' + ridx];
            entry.effective_zone = entry.zone;
            entry.target_name = false;
            if (entry.zone.endsWith("|NAME")) {
                entry.target_name = true;
                entry.effective_zone = entry.zone.substring(0, entry.zone.length - 5);
            }
            entry.var_name = obj['var_name' + ridx];
            entry.content = obj['content' + ridx];
            entries.push(entry);
        }

        return entries;
    }

    var logId;
    var proposed_wl;

    function showWLWin(el) {
        var aData = table.fnGetData(el);
        logId = aData['_id'];
        proposed_wl = [];
        var url = aData['uri'];
        var url_rx = regexify(url);

        var entries = arrangeVar(aData);

        for (var i = 0; i < entries.length; i++) {
            var ent = entries[i];
            var inf = {wls: [], index: i, selected_index: 0};
            var descript = "";
            for (var rule_idx = 0; rule_idx < ent.ids.length; rule_idx++) {
                try {
                    var rid = ent.ids[rule_idx];
                    descript += rid + " (" + mainrules[rid][0] + ")";
                    if (rule_idx < ent.ids.length - 1) {
                        descript += ", ";
                    }
                }catch(err) {
                    console.log("Undefined rule id : "+rid);
                }
            }
            if (ent.zone.startsWith("ARGS") || ent.zone.startsWith("BODY") || ent.zone.startsWith("HEADERS")) {
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:' + ent.zone + '";',
                    explanation: "Allow rule " + descript + " for all " + (ent.target_name ? "keys" : "variables") + " in " + ent.effective_zone + " (Permissive)"});
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:$' + ent.effective_zone + '_VAR:' + ent.var_name + (ent.target_name ? "|NAME" : '') + '";',
                    explanation: "Allow rule " + descript + " in " + (ent.target_name ? "key" : "var") + " '" + ent.var_name + "' (Permissive)"});
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:$URL:' + url + '|$' + ent.effective_zone + '_VAR:' + ent.var_name + (ent.target_name ? "|NAME" : '') + '";',
                    explanation: "Allow rule " + descript + " in " + (ent.target_name ? "key" : "var") + " '" + ent.var_name + "' on URL '" + url + "' (Strict)"});
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:$URL_X:' + url_rx + '|$' + ent.effective_zone + '_VAR:' + ent.var_name + (ent.target_name ? "|NAME" : '') + '";',
                    explanation: "Allow rule " + descript + " in " + (ent.target_name ? "key" : "var") + " '" + ent.var_name + "' on URL matching regex '" + url_rx + "' (Strict)"});
            } else { // URL
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:$URL:' + url + '|URL";',
                    explanation: "Allow rule " + descript + " on URL '" + url + "'"});
                inf.wls.push({wl: 'BasicRule wl:' + ent.ids.join() + ' "mz:$URL_X:' + url_rx + '|URL";',
                    explanation: "Allow rule " + descript + " on URL matching regex '" + url_rx + "'"});
            }
            proposed_wl.push(inf);
        }

        var $wl_proposal = $("#wl-proposal");

        for (var j = 0; j < proposed_wl.length; j++) {
            var info = proposed_wl[j];
            var curr_ent = entries[j];
            var $wl_wrapper = $('<div class="wl-wrapper"></div>').appendTo($wl_proposal);
            var eq_sign = ' = ';
            if (curr_ent.zone === "URL")
                eq_sign = '';
            $('<div class="wl-header"><span class="wl-zone">' + curr_ent.effective_zone + '</span> ' + escapeHtml(curr_ent.var_name) + eq_sign + escapeHtml(curr_ent.content) + '</div>').appendTo($wl_wrapper);
            var $row = $('<div class="row"></div>').appendTo($wl_wrapper);
            $('<div class="col-sm-1 wl-checkbox-div"><input type="checkbox" class="wl-checkbox"></div>').appendTo($row);
            var $col_middle = $('<div class="col-sm-6"></div>').appendTo($row);
            var $select = $('<select class="proposed-wl-explanation"></select>').appendTo($col_middle);
            for (var wli = 0; wli < info.wls.length; wli++) {
                var wlx = info.wls[wli];
                $('<option>' + escapeHtml(wlx.explanation) + '</option>').appendTo($select);
            }
            var $wl_whitelist = $('<div class="col-sm-5 proposed-wl-whitelist">' + escapeHtml(proposed_wl[j].wls[0].wl) + '</div>').appendTo($row);
            $wl_whitelist.hide();
        }

        $(".proposed-wl-explanation").each(function(index) {
            $(this).change(function() {
                var $wl = $(".proposed-wl-whitelist:eq(" + index + ")");
                var selected_index = $(this).find("option:selected").index();
                $wl.text(proposed_wl[index].wls[selected_index].wl);
                proposed_wl[index].selected_index = selected_index;
            })
        });

        var $wl_checkbox = $('.wl-checkbox');

        $wl_checkbox.change(function () {
            $("#add_wl").prop('disabled', $('.wl-checkbox:checked').length <= 0);
        });

        $wl_checkbox.each(function (index) {
            $(this).change(function () {
                $(".proposed-wl-whitelist:eq(" + index + ")").toggle();
            });
        });

        var modalWL = $('#modal_wl');
        modalWL.find('.modal-dialog').css('width', '95%');
        modalWL.modal('show');
        modalWL.draggable({handle: ".modal-header"});
        modalWL.on('hidden.bs.modal', function () {
            $wl_proposal.empty();
            $("#add_wl").prop('disabled', true);
        });
    }

    $("#add_wl").click(function() {
        var whitelists = [];
        $('.wl-checkbox').each(function(index) {
            if (this.checked) {
                var selected_index = proposed_wl[index].selected_index;
                whitelists.push(proposed_wl[index].wls[selected_index].wl);
            }
        });
        console.log(whitelists);
        $.post("/dataset/add_wl/" + datasetCollectionName, {id: logId, wls: JSON.stringify(whitelists)}, function(data, status) {
            $('#modal_wl').modal("hide");
            if (data['status'] === true) {
                new PNotify({
                    title: 'Success',
                    text: '<a style="color: white; text-decoration: underline;" href="/firewall/modsec_rules/">Rule successfully added</a>',
                    type: 'success',
                    styling: 'bootstrap3',
                    buttons: {
                        closer: true,
                        sticker: false
                    }
                });
                table._fnAjaxUpdate();
            } else {
                new PNotify({
                    title: 'Error',
                    text: '<a style="color: white; text-decoration: underline;">Failed to add rule \n' + data['message'] + '/a>',
                    type: 'error',
                    styling: 'bootstrap3',
                    buttons: {
                        closer: true,
                        sticker: false
                    }
                });
            }
        });
    });
});
