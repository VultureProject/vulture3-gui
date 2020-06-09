$(function() {

    function getDateFomat(startDate, endDate) {
        if (endDate.diff(startDate, 'hours', true) <= 2) {
            return "YYYY/MM/DD HH:mm"
        } else if (endDate.diff(startDate, 'days', true) <= 2) {
            return "YYYY/MM/DD HH:mm"
        } else if (endDate.diff(startDate, 'days', true) <= 62) {
            return "YYYY/MM/DD"
        } else {
            return "YYYY/MM"
        }
    }

    $('#app_select').select2({
        placeholder: 'Select an application',
    });

    $('#app_select').on('change', function() {
        fetch_data();
    });

    let dateformat = getDateFomat(moment().startOf('day'), moment());

    $('#all_apps').on('click', function() {
        const all_options = [];
        $('#app_select > option').each(function() {
            all_options.push($(this).val());
        })

        $('#app_select').val(all_options).trigger('change.select2');
        fetch_data();
    });

    $('#no_apps').on('click', function() {
        $('#app_select').val('data', null).trigger('change.select2');
        fetch_data();
    })

    const daterange_input = $('input[name="daterange"]').daterangepicker({
        format: 'MM/DD/YYYY HH:mm:ss',
        minDate: '01/01/1970',
        maxDate: '24/05/2020',
        startDate: moment().startOf('day'),
        endDate: moment(),
        showDropdowns: true,
        showWeekNumbers: true,
        timePicker: true,
        timePickerIncrement: 1,
        timePicker12Hour: true,
        ranges: {
            'Last 10 minutes': [moment().subtract(10, 'minutes'), moment()],
            'Last Hour': [moment().subtract(1, 'hour'), moment()],
            'Today': [moment().startOf('day'), moment()],
            'Yesterday': [moment().subtract(1, 'days').startOf('day'), moment().subtract(1, 'days').endOf('day')],
            'Last 7 Days': [moment().subtract(6, 'days').startOf('day'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days').startOf('day'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        opens: 'right',
        buttonClasses: ['btn', 'btn-sm'],
        applyClass: 'btn-primary',
        cancelClass: 'btn-default',
        separator: ' to ',
        locale: {
            applyLabel: 'Submit',
            cancelLabel: 'Cancel',
            fromLabel: 'From',
            toLabel: 'To',
            customRangeLabel: 'Custom',
            daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
            monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            firstDay: 1,
        },

        onSelect: function() {
            $("#daterange_input").val([start.valueOf(), end.valueOf()]);
            dateformat = getDateFomat(moment(start), moment(end));
            fetch_data();
        }
    }, function(start, end, label) {
        if (label === 'Custom') {
            $('#reportrange_logs').html('From ' + start.format('HH:mm a <b>MMMM D, YYYY</b>') + ' To ' + end.format('HH:mm a <b>MMMM D, YYYY</b>'));
        } else {
            $('#reportrange_logs').html(label);
        }
        dateformat = getDateFomat(moment(start), moment(end));
        fetch_data();
    });

    /// Initialize the datatable
    function init_table() {
        $('.row_table_logs').hide();
        $('#row_table_static_requests').show();


        /// DATATABLE settings
        const settings = {
            "sDom": '<p<"top">t<"bottom"rli>',
            "oLanguage": {
                "sLengthMenu": '_MENU_',
                "oPaginate": {
                    "sNext": '',
                    "sPrevious": ''
                }
            },
            "bfilter": false,
            'iDisplayLength': 10,
            "aLengthMenu": [
                [10, 50, 100],
                [10, 50, 100]
            ],
            'aaSorting': [
                [0, 'asc']
            ],
            "aoColumns": [
                // data & name: name of the columns, aTargets: num of td
                {
                    'defaultContent': "",
                    'bVisible': true,
                    'aTargets': [0],
                    'sWidth': "2%",
                    "sClass": "center"
                },
                {
                    'defaultContent': "",
                    'bVisible': true,
                    'aTargets': [1],
                    'sWidth': "40%"
                },
                {
                    'defaultContent': "",
                    'bVisible': true,
                    'aTargets': [2],
                    'sWidth': "15%"
                },
                {
                    'defaultContent': "",
                    'bVisible': true,
                    'aTargets': [3],
                    'sWidth': "10%"
                }
            ],
            "data": []
        }

        $('#table_static_requests').DataTable(settings);

    }

    $('.resize-font').on('click', function(ev) {
        ev.preventDefault()
        const type = $(this).data('type');
        const size = parseInt($('.table_static_requests tbody td').css('fontSize'));
        const size_detail = parseInt($('#jf-formattedJSON').css('fontSize'));

        switch (type) {
            case 'smaller':
                var font = size - 1 + "px";
                var font_detail = size_detail - 1 + "px";

                $('.table_static_requests tbody td').css({
                    'fontSize': font
                });
                $('#jf-formattedJSON').css({
                    'fontSize': font_detail
                });
                break;

            case 'bigger':
                var font = size + 1 + "px";
                var font_detail = size_detail + 1 + "px";

                $('.table_static_requests tbody td').css({
                    'fontSize': font
                });
                $('#jf-formattedJSON').css({
                    'fontSize': font_detail
                });
                break;

            case 'origin':
                $('.table_static_requests tbody td').css({
                    'fontSize': "10px"
                });
                $('#jf-formattedJSON').css({
                    'fontSize': "12px"
                });
                break;
        }
    })


    init_table();

    const noDataGraphic = {
        type: 'group',
        top: 'middle',
        left: 'center',
        width: 5,
        height: 5,
        z: 150,
        invisible: false,
        children: [{
                type: 'image',
                z: 90,
                left: 'center',
                top: 0,
                style: {
                    width: 50,
                    height: 50,
                    image: '/static/img/warning.png'
                },
            },
            {
                type: 'text',
                z: 100,
                left: 'center',
                top: 60,
                style: {
                    text: ["No data available",
                        "for this date range"
                    ].join("\n"),
                    textAlign: 'center',
                    font: 'bold 17px arial, sans-serif',
                    fill: '#FFA726',
                    lineWidth: 2,
                    shadowBlur: 8,
                    shadowOffsetX: 3,
                    shadowOffsetY: 3,
                    shadowColor: 'rgba(0,0,0,0.3)',
                },
            }
        ]
    };

    const charts = {
        'request_count': {
            'chart': echarts.init(document.getElementById('request_count')),
            'options': {
                title: {
                    text: 'Number of hits by status code',
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            type: 'solid',
                            color: '#4488bb',
                            width: 2
                        }
                    },
                    formatter: function(params) {
                        let text = moment(new Date(params[0].name)).format(dateformat)
                        for (serie of params) {
                            text += '<br /><span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + serie.color + ';"></span> code ' + serie.seriesName + ': ' + serie.value[1] + ' hits';
                        }
                        return text;
                    }
                },
                xAxis: {
                    type: 'time',
                    splitNumber: 5,
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format(dateformat);
                        }
                    }
                },
                yAxis: {
                    type: 'value'
                },
                color: ['#2f4554', '#61a0a8', '#d48265', '#91c7ae', '#ca8622', '#749f83', '#bda29a', '#6e7074', '#546570', '#c4ccd3']
            }
        },
        'http_code': {
            'chart': echarts.init(document.getElementById('http_code')),
            'options': {
                title: {
                    text: 'HTTP status codes',
                    x: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ' : ' + params.value + ' hits (' + params.percent + '%)'
                    }
                },
                series: [{
                    name: 'HTTP status codes',
                    type: 'pie',
                    radius: '55%',
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }],
                color: ['#2f4554', '#61a0a8', '#d48265', '#91c7ae', '#ca8622', '#749f83', '#bda29a', '#6e7074', '#546570', '#c4ccd3']
            }
        },
        'browser_UA': {
            'chart': echarts.init(document.getElementById('browser_UA')),
            'options': {
                title: {
                    text: 'Browsers',
                    x: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ' : ' + params.value + ' hits (' + params.percent + '%)'
                    }
                },
                series: [{
                    name: 'Browsers',
                    type: 'pie',
                    radius: '55%',
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            }
        },
        'os_UA': {
            'chart': echarts.init(document.getElementById('os_UA')),
            'options': {
                title: {
                    text: 'Operating Systems',
                    x: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ' : ' + params.value + ' hits (' + params.percent + '%)'
                    }
                },
                series: [{
                    name: 'OS',
                    type: 'pie',
                    radius: '55%',
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            }
        },
        'http_method': {
            'chart': echarts.init(document.getElementById('http_method')),
            'options': {
                title: {
                    text: 'HTTP methods',
                    x: 'center'
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ' : ' + params.value + ' hits (' + params.percent + '%)'
                    }
                },
                series: [{
                    name: 'HTTP methods',
                    type: 'pie',
                    radius: '55%',
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            }
        },
        'average_breceived': {
            'chart': echarts.init(document.getElementById('average_breceived')),
            'options': {
                title: {
                    text: 'Average bytes received per request',
                    subtext: 'in kiloBytes',
                    subtextStyle: {
                        color: "#39454c",
                        fontSize: 14
                    },
                    x: 'center'
                },
                tooltip: {
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            type: 'solid',
                            color: '#4488bb',
                            width: 2
                        }
                    }
                },
                calculable: false,
                xAxis: {
                    type: 'time',
                    splitNumber: 5,
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format(dateformat);
                        }
                    }
                },
                yAxis: {
                    type: 'value'
                },
                animation: true,
                series: [{
                    name: 'requests',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    hoverAnimation: false,
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default',
                                color: '#ff9d13'

                            }
                        }
                    },
                    lineStyle: {
                        normal: {
                            color: '#ff7011'
                        }
                    }
                }]
            }
        },
        'average_bsent': {
            'chart': echarts.init(document.getElementById('average_bsent')),
            'options': {
                title: {
                    text: 'Average bytes sent per request',
                    subtext: 'in kiloBytes',
                    subtextStyle: {
                        color: "#39454c",
                        fontSize: 14
                    },
                    x: 'center'
                },
                tooltip: {
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            type: 'solid',
                            color: '#4488bb',
                            width: 2
                        }
                    }
                },
                calculable: false,
                xAxis: {
                    type: 'time',
                    splitNumber: 5,
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format(dateformat);
                        }
                    }
                },
                yAxis: {
                    type: 'value'
                },
                animation: true,
                series: [{
                    name: 'requests',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    hoverAnimation: false,
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default',
                                color: '#ff9d13'

                            }
                        }
                    },
                    lineStyle: {
                        normal: {
                            color: '#ff7011'
                        }
                    }
                }]
            }
        },
        'average_time': {
            'chart': echarts.init(document.getElementById('average_time')),
            'options': {
                title: {
                    text: 'Average time elapsed per request',
                    subtext: 'in microseconds',
                    subtextStyle: {
                        color: "#39454c",
                        fontSize: 14
                    },
                    x: 'center'
                },
                tooltip: {
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            type: 'solid',
                            color: '#4488bb',
                            width: 2
                        }
                    }
                },
                calculable: false,
                xAxis: {
                    type: 'time',
                    splitNumber: 5,
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format(dateformat);
                        }
                    }
                },
                yAxis: {
                    type: 'value'
                },
                animation: true,
                series: [{
                    name: 'requests',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    hoverAnimation: false,
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default',
                                color: '#ff9d13'

                            }
                        }
                    },
                    lineStyle: {
                        normal: {
                            color: '#ff7011'
                        }
                    }
                }]
            }
        }
    }

    for (const chart_name of Object.keys(charts)) {
        const values = charts[chart_name];
        values.chart.setOption(values.options);
        values.chart.setOption({
            graphic: noDataGraphic
        });
    }

    function fetch_data() {
        const apps = $("#app_select").val();
        const date = {
            'startDate': daterange_input.data('daterangepicker').startDate,
            'endDate': daterange_input.data('daterangepicker').endDate
        };

        $(".fa-spinner").show("fast");


        $.post(
            '/reporting/data/', {
                'apps': JSON.stringify(apps),
                'daterange': JSON.stringify(date),
                'reporting_type': "access"
            },

            function(response) {
                if (typeof(response) === 'string') {
                    window.location.href = window.location.href;
                    return;
                }

                if (typeof(response.results) === 'string'){
                    let errorGraphic = $.extend(true, {}, noDataGraphic);
                    errorGraphic.children[1].style.text = response.results;

                    for (const chart_name of Object.keys(charts)) {
                        const values = charts[chart_name];
                        values.chart.clear()
                        values.chart.setOption(values.options);
                        values.chart.setOption({
                            graphic: errorGraphic
                        });
                    }

                    $(".fa-spinner").hide();
                    return;
                }

                if (!jQuery.isEmptyObject(response.errors)) {
                    for (const err of response.errors){
                        new PNotify({
                            title: 'Error',
                            text: err,
                            type: 'error',
                            styling: 'bootstrap3',
                            nonblock: {
                                nonblock: true
                            }
                        });
                    }
                }

                for (const result of Object.keys(response.results)) {
                    const values = response.results[result];

                    let options = {
                        graphic: $.extend(true, {}, noDataGraphic)
                    };

                    if (!jQuery.isEmptyObject(values)) {
                        let errorGraphicInvisible = true;

                        if (result.startsWith("average")) {
                            const data = [];
                            for (const item of values) {
                                const date = new Date(item.name);

                                let divisor = result.startsWith("average_b") ? 1024 : 1000;
                                data.push({
                                    name: date.toString(),
                                    value: [date, item.value / divisor]
                                });

                            }
                            options.series = [{
                                data: data
                            }];

                        } else if (result === 'request_count') {

                            const legend = [];
                            const httpData = [];
                            options.series = [];
                            options.legend = {
                                data: []
                            }

                            for (const key of Object.keys(values)) {
                                const data = [];
                                let sum = 0;
                                const color = key === '403' ? '#c23531' : undefined;
                                for (const item of values[key]) {
                                    const date = new Date(item.name);
                                    data.push({
                                        name: date.toString(),
                                        value: [date, item.value],
                                        itemStyle: {
                                            normal: {
                                                color: color
                                            }
                                        }
                                    });
                                    sum += item.value;
                                }

                                options.series.push({
                                    type: 'line',
                                    name: key,
                                    data: data,
                                    smooth: true,
                                    lineStyle: {
                                        normal: {
                                            color: color
                                        }
                                    },
                                    itemStyle: {
                                        normal: {
                                            color: color
                                        }
                                    }
                                });
                                httpData.push({
                                    name: key,
                                    value: sum,
                                    itemStyle: {
                                        normal: {
                                            color: color
                                        }
                                    }
                                });
                                legend.push({
                                    name: key,
                                    itemStyle: {
                                        normal: {
                                            color: color
                                        }
                                    }
                                });
                            }

                            options.legend.data = legend;

                            charts["http_code"].chart.clear();
                            charts["http_code"].chart.setOption(charts["http_code"].options);
                            charts["http_code"].chart.setOption({
                                series: [{
                                    data: httpData
                                }]
                            });

                        } else if (['browser_UA', 'os_UA'].includes(result)) {
                            if (typeof(values) === 'string'){
                                options.graphic.children[1].style.text = values;
                                errorGraphicInvisible = false;
                            } else {
                                const data = [];
                                for (const key of Object.keys(values)) {
                                    data.push({
                                        name: key,
                                        value: values[key]
                                    })
                                }
                                options.series = [{
                                    data: data
                                }];
                            }
                        } else if (result === 'static_requests') {
                            let i = 1;
                            $('#table_static_requests').dataTable().fnClearTable();
                            for (const item of values) {
                                $('#table_static_requests').dataTable().fnAddData([i, item.name.uri, item.name.app, item.value]);
                                i++;
                            }

                        } else {
                            const data = [];
                            for (const item of values) {
                                data.push({
                                    name: item.name,
                                    value: item.value
                                })
                            }
                            options.series = [{
                                data: data
                            }];
                        }

                        for (const children of options.graphic.children) {
                            children.invisible = errorGraphicInvisible;
                        }

                    } else {
                        for (const children of options.graphic.children) {
                            children.invisible = false;
                        }

                        if (result === "request_count") {
                            var option = {
                                graphic: noDataGraphic
                            };
                            for (const children of option.graphic.children) {
                                children.invisible = false;
                            }

                            charts["http_code"].chart.clear();
                            charts["http_code"].chart.setOption(option);

                        } else if (result === "static_requests") {
                            $('#table_static_requests').dataTable().fnClearTable();
                        }

                    }

                    if (result !== "static_requests") {
                        charts[result].chart.clear();
                        charts[result].chart.setOption(charts[result].options);
                        charts[result].chart.setOption(options);
                    }


                }
                $(".fa-spinner").hide();
            }
        )

    }

    if ($('#app_select')[0].options.length <= 0) {
        new PNotify({
            title: 'Error',
            text: "No data repository available",
            type: 'error',
            styling: 'bootstrap3',
            nonblock: {
                nonblock: true
            }
        });
        $('input[name="daterange"]').daterangepicker();
        $(".fa-spinner").hide();
    } else {
        fetch_data();
    }

});
