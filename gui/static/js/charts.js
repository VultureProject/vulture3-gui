$(function(){
	String.format = function() {
        // The string containing the format items (e.g. "{0}")
        // will and always has to be the first argument.
        var str = arguments[0];

        // start with the second argument (i = 1)
        for (var i = 1; i < arguments.length; i++) {
            // "gm" = RegEx options for Global search (more than one instance)
            // and for Multiline search
            var regEx = new RegExp("\\{" + (i - 1) + "\\}", "gm");
            str = str.replace(regEx, arguments[i]);
        }

        return str;
    }

    var last_date = null;

	var first_charts = {
		'cpu_chart': {
			'chart'  : echarts.init(document.getElementById("cpu_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'CPU usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'axis'
			    },
			    toolbox: {
			        show : false
			    },
			    calculable : false,
			    legend : {data : []},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
					type       : 'time',
					splitNumber: 31,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		},

		'memory_chart': {
			'chart'  : echarts.init(document.getElementById("memory_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Memory usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {data : []},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		},

		'process_chart': {
			'chart'  : echarts.init(document.getElementById("process_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Number of process over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {data : []},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value}'
		            },
			    }],
			    animation: true,
			    series : []
			}
		},
		'redis_chart': {
			'chart'  : echarts.init(document.getElementById("redis_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Redis memory usage',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {data : []},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: function(value) {
							return Math.round((value/(1024*1024)))+" MB";
						}
		            },
			    }],
			    animation: true,
			    series : []
			}
		}
	}

	var secondary_charts = {
		'root_chart': {
			'chart'  : echarts.init(document.getElementById("root_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Root disk usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {
					data : [],
					left: '50%'
				},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		},

		'var_chart': {
			'chart'  : echarts.init(document.getElementById("var_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Var disk usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {
					data : [],
					left: '50%'
				},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		},

		'home_chart': {
			'chart'  : echarts.init(document.getElementById("home_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'Home usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {
					data : [],
					left: '45%'
				},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		},

		'swap_chart': {
			'chart'  : echarts.init(document.getElementById("swap_chart")),
			'init'   : false,
			'options': {
			    title : {
			        text : 'SWAP usage evolution over time',
			        subtext : 'by node'
			    },
			    tooltip : {
			        trigger: 'item',
			    },
			    calculable : false,
			    toolbox: {
			        show : false
			    },
			    legend : {
					data : [],
					left: '45%'
				},
			    grid: {
			        y2: 80
			    },
			    xAxis : [{
			        type : 'time',
			        splitNumber: 0,
			    }],
			    yAxis : [{
			    	type : 'value',
			    	axisLabel : {
		                formatter: '{value} %'
		            },
		            min: 0,
		            max: 100,
			    }],
			    animation: true,
			    series : []
			}
		}
	}

	var areaColors = ["#c67300" , "#ff9d13", "#ffb246", "#ffd7a0", "#fff5e7"];

	function load_charts(charts){

		$.each(charts, function(chart_name, values){
			data = {
				'chart': chart_name
			}

			$.post(
				"/monitor/data/",
				data,

				function(response){
					if (typeof(response) === 'string'){
						window.location.href = window.location.href;
						return;
					}

					values['options'].series = [];
					values['options'].legend['data'] = [];

					if (values['init']){
						values['chart'].getOption();
						values['chart'].setSeries([]);
						values['chart'].clear();
					}

					var nodeCount = 0;

					$.each(response['results'], function(node, data){
						var color = areaColors[nodeCount % areaColors.length]
						var data_formatted = [];
						for (var i in data) {
							data_formatted.push({
								value: [new Date(Date.parse(data[i][0]+"+0000")), data[i][1]],
								itemStyle: {
									normal: {
										color: color
									}
								}
							});
						}

						var serie = {
							name     : node,
							type     : 'line',
							smooth   : true,
							itemStyle: {
		                        normal: {
		                            areaStyle: {
		                                type: 'default',
		                                color: color

		                            },
									color: color
		                        }
		                    },
		                    lineStyle: {
		                        normal: {
		                            color: '#ff7011'
		                        }
		                    },
							data: data_formatted,
							tooltip  : {
                                trigger: 'axis',
                            }
					    }

					    values['options'].xAxis[0]['splitNumber'] = 5;
					    values['options'].legend['data'].push(node);
						values['options'].series.push(serie);
						nodeCount++;
					})

					values['chart'].setOption(values['options']);
					values['chart'].hideLoading();
                    values['chart'].resize()
                    values['init'] = true;
				}
			)
		})
	}


	function init_charts(){
		load_charts(first_charts);
		setTimeout(function(){
			load_charts(secondary_charts)
		}, 2000);
	}

	init_charts()
	setInterval(function(){
		init_charts();
	}, 60000);
})
