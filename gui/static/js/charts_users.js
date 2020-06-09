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

  	function load_charts(){
  		var charts = {
  			'users_chart': {
  				'chart': echarts.init(document.getElementById("users_chart")),
  				'options': {
  				    title : {
  				        text : 'Number of user sessions',
  				        subtext : 'by node'
  				    },
  				    tooltip : {
  				        trigger: 'item',
  				    },
              calculable: false,
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

  				    }],
  				    animation: true,
  				    series : []
  				}
  			}
  		}

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
            
  					$.each(response['results'], function(node, data){
  						var data_formatted = [];
  						for (var i in data)
  							data_formatted.push([new Date(data[i][0]), data[i][1]])

  						var serie = {
							name     : node,
							type     : 'line',
							smooth   : true,
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
              },
							data     : data_formatted,
							tooltip  : {
							trigger  : 'axis',
							formatter: function (params){
								return String.format("{0}/{1}/{2}", date.getFullYear(), date.getMonth()+1, date.getDate());
							  },
							}
  						}

  						values['options'].xAxis[0]['splitNumber'] = 5;
  						values['options'].legend['data'].push(node);
  						values['options'].series.push(serie);
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