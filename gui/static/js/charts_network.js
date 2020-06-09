$(function(){
	String.format = function() {
        // The string containing the format items (e.g. "{0}")
        // will and always has to be the first argument.
        var str = arguments[0];

        // start with the second argument (i = 1)
        for (var i=1; i<arguments.length; i++) {
            // "gm" = RegEx options for Global search (more than one instance)
            // and for Multiline search
            var regEx = new RegExp("\\{" + (i - 1) + "\\}", "gm");
            str = str.replace(regEx, arguments[i]);
        }

        return str;
    }

  	function load_charts(){
  		var charts = {
  			'bytes_recv_chart': {
				'chart': echarts.init(document.getElementById("bytes_recv_chart")),
				'options': {
				    title : {
				        text : 'Bytes recv evolution over time',
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
			                formatter: function(params){
			                	var value = params/1024;
			                	return String.format("{0} kB", parseInt(value))
			                }
			            },
						min: 0,
				    }],
				    animation: true,
				    series : []
				}
			},

			'bytes_sent_chart': {
				'chart': echarts.init(document.getElementById("bytes_sent_chart")),
				'options': {
				    title : {
				        text : 'Bytes sent evolution over time',
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
			                formatter: function(params){
			                	var value = params/1024;
			                	return String.format("{0} kB", parseInt(value))
			                }
			            },
						min: 0,
				    }],
				    animation: true,
				    series : []
				}
			},

			'dropin_chart': {
				'chart': echarts.init(document.getElementById("dropin_chart")),
				'options': {
				    title : {
				        text : 'Incoming packet dropped',
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
			                formatter: '{value} packets'
			            }
				    }],
				    animation: true,
				    series : []
				}
			},

			'errin_chart': {
				'chart': echarts.init(document.getElementById("errin_chart")),
				'options': {
				    title : {
				        text : 'Number of error while receiving',
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
						left: '42%'
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
			                formatter: '{value} packets'
			            }
				    }],
				    animation: true,
				    series : []
				}
			},

			'errout_chart': {
				'chart': echarts.init(document.getElementById("errout_chart")),
				'options': {
				    title : {
				        text : 'Number of error while sending',
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
						left: '42%'
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
			                formatter: '{value} packets'
			            }
				    }],
				    animation: true,
				    series : []
				}
			},
			'pf_state_entries_chart': {
				'chart': echarts.init(document.getElementById("pf_state_entries")),
				'options': {
				    title : {
				        text : 'Number of entries in the firewall state table',
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
			                formatter: '{value} entries'
			            }
				    }],
				    animation: true,
				    series : []
				}
			},
  		}

		var areaColors = ["#c67300" , "#ff9d13", "#ffb246", "#ffd7a0", "#fff5e7"];

  		$.each(charts, function(chart_name, values){
  			data = {
  				'chart': chart_name
  			}

  			$.post(
  				'/monitor/data/',
  				data,

  				function(response){
  					if (typeof(response) === 'string'){
						window.location.href = window.location.href;
						return;
					}
					var nodeCount = 0;
  					$.each(response['results'], function(node, data){
						var color = areaColors[nodeCount % areaColors.length]
  						var data_formatted = [];
  						for (var i in data) {
  							data_formatted.push({
								value: [new Date(data[i][0]), data[i][1]],
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
								trigger  : 'axis',
								formatter: function (params) {
									return params;
                                },
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
  				}
  			)
  		})
  	}

	load_charts();
	setInterval(function(){
		load_charts();
	}, 60000);
})
