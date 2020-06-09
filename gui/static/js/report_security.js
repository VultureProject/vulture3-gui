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

    const charts = {
        'request_count': {
            'chart': echarts.init(document.getElementById('requests_chart')),
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
                    },
                    splitLine: {
                        show: true
                    }
                },
                yAxis: {
                    type: 'value'
                },
                color: ['#2f4554', '#61a0a8', '#d48265', '#91c7ae', '#ca8622', '#749f83', '#bda29a', '#6e7074', '#546570', '#c4ccd3']
            }
        },
        'average_score': {
            'chart': echarts.init(document.getElementById('average_score')),
            'options': {
                title: {
                    text: 'Average score by status code',
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
                            text += '<br /><span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + serie.color + ';"></span> code ' + serie.seriesName + ': ' + serie.value[1];
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
                    },
                    splitLine: {
                        show: true
                    }
                },
                yAxis: {
                    type: 'value'
                },
                color: ['#2f4554', '#61a0a8', '#d48265', '#91c7ae', '#ca8622', '#749f83', '#bda29a', '#6e7074', '#546570', '#c4ccd3']
            }
        },
        'security_radar': {
            'chart': echarts.init(document.getElementById("security_radar")),
            'options': option = {
                title: {
                    text: 'Distribution of blocked requests',
                    x: 'center'
                },
                radar: {
                    name: {
                        textStyle: {
                            color: '#fff',
                            backgroundColor: '#999',
                            borderRadius: 3,
                            padding: [3, 5]
                        }
                    },
                    center: ['50%', '55%']
                }
            }
        },
        'owasp_top10': {
            'chart': echarts.init(document.getElementById("owasp_top10")),
            'options': option = {
                title: {
                    text: 'OWASP Top 10 Requests'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        let text = params[0].name
                        for (serie of params) {
                            text += '<br /><span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + serie.color + ';"></span> code ' + serie.seriesName + ': ' + serie.value + ' hits';
                        }
                        return text;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: ['A1 - Injection ', 'A2 - Broken AUthentication and Session Management', 'A3 - Cross-Site-Scripting (XSS)',
                        'A4 - Insecure Direct Obkect References', 'A5 - Security Misconfiguguration', 'A6 - Sensitive Data Exposure',
                        'A7 - Missing Function Level Access Control', 'A8 - Cross-Site-Request Forgery (CSRF)', 'A9 - Using Compnents with Known Vulnerabilities',
                        'A10 - Unvalidated Redirects and Forwards'
                    ],
                    axisLabel: {
                        formatter: function(params) {
                            return params.split(' ')[0];
                        }
                    },
                    axisTick: {
                        alignWithLabel: true
                    },
                    splitLine: {
                        show: true
                    }
                },
                yAxis: {
                    type: 'value'
                },
                color: ['#2f4554', '#61a0a8', '#d48265', '#91c7ae', '#ca8622', '#749f83', '#bda29a', '#6e7074', '#546570', '#c4ccd3']
            }
        },
        'blocked_requests': {
            'chart': echarts.init(document.getElementById("blocked_requests")),
            'options': option = {
                title: {
                    text: 'Number of blocked requests',
                    subtext: 'by attack category',
                    subtextStyle: {
                        color: "#39454c",
                        fontSize: 14
                    },
                    x: 'center'
                },
                color: ['#FFC312'],
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        return params[0].name + '<br /><span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params[0].color + ';"></span>' + params[0].seriesName + ': ' + params[0].value;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    axisTick: {
                        alignWithLabel: true
                    }
                },
                yAxis: {
                    type: 'value'
                },
                series: {
                    name: 'blocked_requests',
                    type: 'bar',
                    barWidth: '60%'
                }
            }
        },
        'reputation_tags': {
            'chart': echarts.init(document.getElementById("reputation_chart")),
            'options': option = {
                title: [{
                    text: ["Reputation tags",
                        "(Click on pie section to display detailed reputation per Ip)"
                    ].join("\n"),
                    subtext: 'hits per tag',
                    subtextStyle: {
                        color: "#39454c",
                        fontSize: 14
                    },
                    x: '20%',
                    textAlign: 'center',

                }, {
                    text: 'IP list reputation',
                    x: '68%',
                    textAlign: 'center',

                }],
                tooltip: {
                    trigger: 'item'
                },
                grid: [{
                    top: 80,
                    width: '55%',
                    bottom: '25%',
                    left: '40%',
                    containLabel: true
                }],
                yAxis: {
                    type: 'value',
                    splitLine: {
                        show: false
                    }
                },
                xAxis: {
                    type: 'category',
                    axisLabel: {
                        interval: 0,
                        rotate: 30
                    },
                    splitLine: {
                        show: false
                    }
                },
                series: [{
                    type: 'bar',
                    stack: 'chart',
                    z: 3,
                    tooltip: {
                        formatter: function(params) {
                            return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ': ' + params.value + ' hits';
                        }
                    }
                }, {
                    type: 'pie',
                    tooltip: {
                        formatter: function(params) {
                            return '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + params.color + ';"></span>' + params.name + ' : ' + params.value + ' hits (' + params.percent + '%)'
                        }
                    },
                    radius: [0, '55%'],
                    center: ['20%', '50%']
                }]
            }
        }
    }

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

    function setNoDataGraphic(chart_name) {
        if (chart_name === 'reputation_tags') {
            var graphic = [$.extend(true, {}, noDataGraphic), $.extend(true, {}, noDataGraphic)];
            graphic[0].left = "15.5%";
            graphic[1].left = "63.5%";

            return graphic
        } else {
            return [noDataGraphic]
        }
    }

    for (const chart_name of Object.keys(charts)) {
        const values = charts[chart_name];
        values.chart.setOption(values.options);
        const graphic = setNoDataGraphic(chart_name)
        values.chart.setOption({
            graphic: graphic
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
                'reporting_type': "security"
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
                        graphic: setNoDataGraphic(result)
                    };

                    if (!jQuery.isEmptyObject(values)) {
                        if (result === 'owasp_top10') {
                            options.series = [];
                            options.legend = {
                                data: []
                            }

                            const legend = [];
                            for (const serie of values) {
                                const data = [];
                                for (const key of Object.keys(serie.value)) {
                                    data.push({
                                        name: key,
                                        value: serie.value[key]
                                    });
                                }

                                options.series.push({
                                    type: 'bar',
                                    name: serie.name,
                                    data: data,
                                    smooth: true,
                                    itemStyle: {
                                        normal: {
                                            color: serie.name === 403 ? '#c23531' : undefined
                                        }
                                    }
                                });
                                legend.push(serie.name.toString());
                            }

                            options.legend.data = legend.sort();


                            if (result === "blocked_requests") {
                                options.xAxis = {
                                    data: options.series[0].data.map(item => item.name)
                                };
                            }

                        } else if (['blocked_requests', 'security_radar'].includes(result)) {
                            const data = [];
                            const names = [];
                            for (const key of Object.keys(values)) {
                                data.push(values[key]);
                                names.push(key);
                            }

                            options.series = [{
                                data: data
                            }];

                            if (result === "blocked_requests") {
                                options.xAxis = [{
                                    data: names
                                }];
                            } else if (result === "security_radar") {
                                maxIndicator = Math.max(...data);
                                indicators = [];
                                for (const key of Object.keys(values)) {
                                    indicators.push({
                                        name: key,
                                        max: maxIndicator
                                    });
                                }

                                options.radar = {};
                                options.radar.indicator = indicators;
                                options.series = [{
                                    name: 'Security Performance',
                                    type: 'radar',
                                    data: [{
                                        value: data,
                                        itemStyle: {
                                            normal: {
                                                areaStyle: {
                                                    type: 'default'
                                                }
                                            }
                                        },
                                        name: 'Security Performance with WAF'
                                    }]
                                }];
                            }
                        } else if (['request_count', 'average_score'].includes(result)) {
                            const legend = [];
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
                                    const value = result === 'average_score' ? item.value.toFixed(2) : item.value;
                                    data.push({
                                        name: date.toString(),
                                        value: [date, value],
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
                                legend.push({
                                    name: key,
                                    itemStyle: {
                                        normal: {
                                            color: color
                                        }
                                    }
                                });
                                options.legend.data = legend;
                            }

                        } else if (result === 'reputation_tags') {
                            const data = [];
                            reputationJson = values;
                            for (const key of Object.keys(reputationJson)) {
                                data.push({
                                    name: key,
                                    value: reputationJson[key].value
                                })
                            };
                            const firstTag = Object.keys(reputationJson)[0];
                            options.title = [{}, {
                                text: 'IP list reputation for ' + firstTag + ' tag'
                            }]
                            options.xAxis = [{
                                data: reputationJson[firstTag].ips.map(ip => {
                                    return ip.ip
                                })
                            }];
                            options.series = [{
                                data: reputationJson[firstTag].ips.map(ip => {
                                    return ip.value
                                })
                            }, {
                                data: data
                            }];

                        }

                        options.graphic.forEach(graphic => {
                            graphic.children.forEach(children => {
                                children.invisible = true;
                            });
                        });


                    } else {
                        options.graphic.forEach(graphic => {
                            graphic.children.forEach(children => {
                                children.invisible = false;
                            });
                        });
                    }

                    charts[result].chart.clear();
                    charts[result].chart.setOption(charts[result].options);
                    charts[result].chart.setOption(options);

                    if (result === "reputation_tags") {
                        const chart = charts[result].chart;
                        chart.on('click', function(params) {
                            if (params.seriesType === 'pie') {
                                const selectedTag = params.name;

                                chart.setOption({
                                    title: [{}, {
                                        text: 'IP list reputation for ' + selectedTag + ' tag'
                                    }],
                                    xAxis: [{
                                        data: reputationJson[selectedTag].ips.map(function(ip) {
                                            return ip.ip
                                        })
                                    }],
                                    series: [{
                                        data: reputationJson[selectedTag].ips.map(function(ip) {
                                            return ip.value
                                        }),
                                        itemStyle: {
                                            normal: {
                                                color: params.color
                                            }
                                        }
                                    }, {}]
                                });
                            }
                        });
                    }
                }
                $(".fa-spinner").hide();
            });

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
