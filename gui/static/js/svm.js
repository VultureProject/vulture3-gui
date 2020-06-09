//---------------------------------------------------------------
var theme = {

    // backgroundColor: 'rgba(0,0,0,0)',

    color: ['#ff7f50', '#87cefa', '#da70d6', '#32cd32', '#6495ed',
        '#ff69b4', '#ba55d3', '#cd5c5c', '#ffa500', '#40e0d0',
        '#1e90ff', '#ff6347', '#7b68ee', '#00fa9a', '#ffd700',
        '#6699FF', '#ff6666', '#3cb371', '#b8860b', '#30e0e0'
    ],


    title: {
        x: 'left',
        y: 'top',
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: '#617079',
        borderWidth: 0,
        padding: 5,
        itemGap: 10,
        textStyle: {
            fontSize: 20,
            fontWeight: 'normal',
            color: '#FFC312'
        },
        subtextStyle: {
            color: '#21accb'
        }
    },


    legend: {
        orient: 'horizontal',
        x: 'center',
        y: 'top',
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: '#ccc',
        borderWidth: 0,
        itemWidth: 20,
        textStyle: {
            color: '#333'
        }
    },

    grid: {
        show: true,
        backgroundColor: '#557582',
        borderWidth: 1,
        borderColor: '#626F76'
    },

    valueAxis: {
        position: 'left',
        nameLocation: 'end',
        nameTextStyle: {},
        boundaryGap: [0, 0],
        splitNumber: 5,
        axisLine: {
            show: true,
            lineStyle: {
                color: '#21accb',
                width: 2,
                type: 'solid'
            }
        },
        axisTick: {
            show: true,
            length: 5,
            lineStyle: {
                color: '#21accb',
                width: 1
            }
        },
        axisLabel: {
            show: true,
            rotate: 0,
            margin: 8,
            textStyle: {
                color: '#FFC312'
            }
        },
        splitLine: {
            show: true,
            lineStyle: {
                color: ['#21accb'],
                width: 1,
                type: 'solid'
            }
        }
    },

    timeAxis: {
        position: 'left',
        nameLocation: 'end',
        nameTextStyle: {},
        boundaryGap: [0, 0],
        splitNumber: 5,
        axisLine: {
            show: true,
            lineStyle: {
                color: '#21accb',
                width: 2,
                type: 'solid'
            }
        },
        axisTick: {
            show: true,
            length: 5,
            lineStyle: {
                color: '#21accb',
                width: 1
            }
        },
        axisLabel: {
            show: true,
            rotate: 0,
            margin: 8,
            textStyle: {
                color: '#FFC312'
            }
        },
        splitLine: {
            show: true,
            lineStyle: {
                color: ['#21accb'],
                width: 1,
                type: 'solid'
            }
        }
    },

    textStyle: {
        decoration: 'none',
        fontFamily: 'Arial, Verdana, sans-serif',
        fontFamily2: '微软雅黑',
        fontSize: 12,
        fontStyle: 'normal',
        fontWeight: 'normal'
    },

    symbolList: [
        'circle', 'rectangle', 'triangle', 'diamond',
        'emptyCircle', 'emptyRectangle', 'emptyTriangle', 'emptyDiamond'
    ],
    loadingText: 'Loading...',

    calculable: false,
    calculableColor: 'rgba(255,165,0,0.6)',
    calculableHolderColor: '#ccc',
    nameConnector: ' & ',
    valueConnector: ' : ',
    animation: true,
    animationThreshold: 2500,
    addDataAnimation: true,
    animationDuration: 2000,
    animationEasing: 'ExponentialOut'

};

//------------------------------------------------------------------------------------

var dataset_id = $('#dataset_id').val();

// INITIALISATION
if ($('#svm').val() === 'charts') {
    bytes_received_vs_code(dataset_id);
    //bytes_sent_vs_code(dataset_id);
    uri_analysis(dataset_id);
    uri_analysis_2(dataset_id);
    req_per_min_per_ip(dataset_id);
    req_per_min_per_user(dataset_id);
    ratiochart(dataset_id);
}

function ratiochart(dataset_id) {
    $.post(
        '/dataset/print_graph',

        {
            'dataset_id': dataset_id,
            'algo_used': "Ratio"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            for (i = 0; i < circle.length; i++) {
                ser.push({
                    name: i,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[i]
                });
            }

            var chart_ratio = echarts.init(document.getElementById('chart_ratio'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_ratio.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                // REAL TIME ! Every 2 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "Ratio"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_ratio.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_ratio.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_ratio.resize();
                }
            }, 5000);

            var contour = data['contour'];
            // Set the option for the chart

            var option = {
                title: {
                    text: 'Ratio data received / sent'
                },
                xAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}\nhttp_code'
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value} bytes'
                    }
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_ratio.setOption(option);
            // Remove the loading message

            chart_ratio.hideLoading();
        }
    )
}

function bytes_received_vs_code(dataset_id) {
    $.post(
        '/dataset/print_graph',

        {
            'dataset_id': dataset_id,
            'algo_used': "HTTPcode_bytes_received"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            for (i = 0; i < circle.length; i++) {
                ser.push({
                    name: i,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[i]
                });
            }

            var chart_bytes_received = echarts.init(document.getElementById('chart_bytes_received'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_bytes_received.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                // REAL TIME ! Every 2 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "HTTPcode_bytes_received"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_bytes_received.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_bytes_received.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_bytes_received.resize();
                }
            }, 5000);

            var contour = data['contour'];
            // Set the option for the chart

            var option = {
                title: {
                    text: 'Data received / HTTP status code'
                },
                xAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}\nhttp_code'
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value} bytes'
                    }
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_bytes_received.setOption(option);
            // Remove the loading message

            chart_bytes_received.hideLoading();
        }
    )
}

function bytes_sent_vs_code(dataset_id) {
    $.post(
        '/dataset/print_graph',

        {
            'dataset_id': dataset_id,
            'algo_used': "HTTPcode_bytes_sent"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            for (var i = 0; i < circle.length; i++) {
                ser.push({
                    name: i,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[i]
                });
            }

            var chart_bytes_sent = echarts.init(document.getElementById('chart_bytes_sent'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_bytes_sent.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                // REAL TIME ! Every 2 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "HTTPcode_bytes_sent"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_bytes_sent.addData(0, realtime_data['data'][i], true, true);
                                } else {
                                    chart_bytes_sent.addData(1, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_bytes_sent.resize();
                }
            }, 5000);

            var contour = data['contour'];
            // Set the option for the chart

            var option = {
                title: {
                    text: 'Request length / HTTP status code'
                },
                xAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}\nhttp_code'
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value} bytes'
                    }
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_bytes_sent.setOption(option);
            // Remove the loading message

            chart_bytes_sent.hideLoading();
        }
    )
}

function uri_analysis(dataset_id) {
    $.post(
        '/dataset/print_graph', {
            'dataset_id': dataset_id,
            'algo_used': "Levenstein"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            for (var i = 0; i < circle.length; i++) {
                ser.push({
                    name: i,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[i]
                });
            }

            var chart_uri_analysis = echarts.init(document.getElementById('chart_uri_analysis'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_uri_analysis.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                // REAL TIME ! Every 2 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "Levenstein"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_uri_analysis.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_uri_analysis.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_uri_analysis.resize();
                }
            }, 5000);


            var contour = data['contour'];
            // Set the option for the chart
            var option = {
                title: {
                    text: "Average levenshtein distance uri / Length uri part (splitted by /)"
                },
                xAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}'
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}'
                    }
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_uri_analysis.setOption(option);
            // Remove the loading message

            chart_uri_analysis.hideLoading();
        }
    )
}

function uri_analysis_2(dataset_id) {
    $.post(
        '/dataset/print_graph', {
            'dataset_id': dataset_id,
            'algo_used': "Levenstein2"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            for (var i = 0; i < circle.length; i++) {
                ser.push({
                    name: i,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[i]
                });
            }

            var chart_uri_analysis_2 = echarts.init(document.getElementById('chart_uri_analysis_2'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_uri_analysis_2.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                // REAL TIME ! Every 2 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "Levenstein2"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_uri_analysis_2.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_uri_analysis_2.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_uri_analysis_2.resize();
                }
            }, 5000);

            var contour = data['contour'];
            // Set the option for the chart
            var option = {
                title: {
                    text: 'Average levenshtein distance uri / Length uri'
                },
                xAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}'
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value}'
                    }
                }],
                series: ser
            };


            // Load data into the ECharts instance
            chart_uri_analysis_2.setOption(option);
            // Remove the loading message

            chart_uri_analysis_2.hideLoading();
        }
    )
}

function req_per_min_per_ip(dataset_id) {
    $.post(
        '/dataset/print_graph', {
            'dataset_id': dataset_id,
            'algo_used': "Req_per_min_per_ip"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            var minimum = new Date;
            var maximum = "";
            for (var j = 0; j < circle.length; j++) {
                ser.push({
                    name: j,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[j]
                });
                for (var i = 0; i < circle[j].length; i++) {
                    var totalSec = circle[j][i][0] * 864;
                    var hours = parseInt(totalSec / 3600) % 24;
                    var minutes = parseInt(totalSec / 60) % 60;
                    var seconds = parseInt(totalSec % 60);
                    var newDate = new Date;
                    newDate.setHours(hours, minutes, seconds, 0);
                    circle[j][i][0] = newDate;
                    if (newDate < minimum) {
                        minimum = newDate;
                    }
                    if (newDate > maximum) {
                        maximum = newDate;
                    }
                }
            }
            var chart_req_per_ip = echarts.init(document.getElementById('chart_req_per_ip'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_req_per_ip.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                //REAL TIME ! Every 60 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "Req_per_min_per_ip"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                var totalSec = realtime_data['data'][i][0] * 864;
                                var hours = parseInt(totalSec / 3600) % 24;
                                var minutes = parseInt(totalSec / 60) % 60;
                                var seconds = parseInt(totalSec % 60);
                                var newDate = new Date;
                                newDate.setHours(hours, minutes, seconds, 0);
                                realtime_data['data'][i][0] = newDate;
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_req_per_ip.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_req_per_ip.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_req_per_ip.resize();
                }
            }, 60000);


            var contour = data['contour'];
            // Set the option for the chart
            var option = {
                title: {
                    text: 'Trafic evolution over day per IP'
                },
                xAxis: [{
                    type: 'time',
                    scale: true,
                    splitNumber: 10,
                    min: minimum,
                    max: maximum,
                    axisTick: {
                        interval: 10
                    },
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format("MM/DD HH:mm")
                        }
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value} req/IP'
                    },
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_req_per_ip.setOption(option);
            // Remove the loading message

            chart_req_per_ip.hideLoading();
        }
    )
}

function req_per_min_per_user(dataset_id) {
    $.post(
        '/dataset/print_graph', {
            'dataset_id': dataset_id,
            'algo_used': "Req_per_min_per_user"
        },

        function(data) {
            var ser = [];
            ser.push({
                name: 'suspicious',
                type: 'scatter',
                data: []
            });
            ser.push({
                name: 'valid',
                type: 'scatter',
                data: []
            });
            var circle = data['contour'];
            var minimum = new Date;
            var maximum = "";
            for (var j = 0; j < circle.length; j++) {
                ser.push({
                    name: j,
                    type: 'line',
                    itemStyle: {
                        normal: {
                            areaStyle: {
                                type: 'default'
                            }
                        }
                    },
                    smooth: true,
                    data: circle[j]
                });
                for (var i = 0; i < circle[j].length; i++) {
                    var totalSec = circle[j][i][0] * 864; //convert date on 24h (from 0-100) in a Date object
                    var hours = parseInt(totalSec / 3600) % 24;
                    var minutes = parseInt(totalSec / 60) % 60;
                    var seconds = parseInt(totalSec % 60);
                    var newDate = new Date;
                    newDate.setHours(hours, minutes, seconds, 0);
                    circle[j][i][0] = newDate;
                    if (newDate < minimum) {
                        minimum = newDate;
                    }
                    if (newDate > maximum) {
                        maximum = newDate;
                    }
                }
            }
            var chart_req_per_user = echarts.init(document.getElementById('chart_req_per_user'), theme);
            // Show a loading circle and a message to ask for waiting
            chart_req_per_user.showLoading({
                text: "Loading charts... Please wait"
            });

            clearInterval(resizechart);
            var resizechart = setInterval(function() {
                //REAL TIME ! Every 60 secs
                if ($('#real_time').prop('checked')) {
                    // instructions
                    $.post(
                        '/dataset/graph_realtime', {
                            'dataset_id': dataset_id,
                            'algo_used': "Req_per_min_per_user"
                        },
                        function(realtime_data) {
                            for (i = 0; i < realtime_data['data'].length; i++) {
                                var totalSec = realtime_data['data'][i][0] * 864;
                                var hours = parseInt(totalSec / 3600) % 24;
                                var minutes = parseInt(totalSec / 60) % 60;
                                var seconds = parseInt(totalSec % 60);
                                var newDate = new Date;
                                newDate.setHours(hours, minutes, seconds, 0);
                                realtime_data['data'][i][0] = newDate;
                                if (realtime_data['anomaly'][i] > 0) {
                                    chart_req_per_user.addData(1, realtime_data['data'][i], true, true);
                                } else {
                                    chart_req_per_user.addData(0, realtime_data['data'][i], true, true);
                                }
                            }
                        }
                    );
                    chart_req_per_user.resize();
                }
            }, 60000);


            var contour = data['contour'];
            // Set the option for the chart
            var option = {
                title: {
                    text: 'Trafic evolution over day per user'
                },
                xAxis: [{
                    type: 'time',
                    scale: true,
                    splitNumber: 10,
                    min: minimum,
                    max: maximum,
                    axisTick: {
                        interval: 10
                    },
                    axisLabel: {
                        formatter: function(params) {
                            return moment(new Date(params)).format("MM/DD HH:mm")
                        }
                    }
                }],
                yAxis: [{
                    type: 'value',
                    scale: true,
                    axisLabel: {
                        formatter: '{value} req/user'
                    }
                }],
                series: ser
            };

            // Load data into the ECharts instance
            chart_req_per_user.setOption(option);
            // Remove the loading message

            chart_req_per_user.hideLoading();
        }
    )
}


$('#real_time').on('change', function() {
    // Hide or show reportrange/pagination controls and ajax loader information
    if ($(this).prop('checked')) {
        $('#wait_ajax').show()
    } else {
        $('#wait_ajax').hide()
    }
});
