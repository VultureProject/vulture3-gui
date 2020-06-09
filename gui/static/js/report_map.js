$(function(){
	const country = {
		"BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria",
		"BA": "Bosnia and Herzegovina", "BB": "Barbados", "WF": "Wallis and Futuna", "BL": "Saint Barth\u00e9lemy",
		"BM": "Bermuda", "BN": "Brunei", "BO": "Bolivia", "BH": "Bahrain",
		"BI": "Burundi", "BJ": "Benin", "BT": "Bhutan", "JM": "Jamaica", "BV": "Bouvet Island", "BW": "Botswana",
		"WS": "Samoa", "BQ": "Bonaire, Sint Eustatius and Saba", "BR": "Brazil", "BS": "The Bahamas", "JE": "Jersey",
		"BY": "Belarus", "BZ": "Belize", "RU": "Russia", "RW": "Rwanda", "RS": "Republic of Serbia", "TL": "East Timor",
		"RE": "R\u00e9union", "TM": "Turkmenistan", "TJ": "Tajikistan", "RO": "Romania", "TK": "Tokelau",
		"GW": "Guinea Bissau", "GU": "Guam", "GT": "Guatemala", "GS": "South Georgia and the South Sandwich Islands",
		"GR": "Greece", "GQ": "Equatorial Guinea", "GP": "Guadeloupe", "JP": "Japan", "GY": "Guyana", "GG": "Guernsey",
		"GF": "French Guiana", "GE": "Georgia", "GD": "Grenada", "GB": "United Kingdom", "GA": "Gabon", "SV": "El Salvador",
		"GN": "Guinea", "GM": "Gambia", "GL": "Greenland", "GI": "Gibraltar", "GH": "Ghana", "OM": "Oman", "TN": "Tunisia",
		"JO": "Jordan", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary", "HK": "Hong Kong", "HN": "Honduras",
		"HM": "Heard Island and McDonald Islands", "VE": "Venezuela", "PR": "Puerto Rico",
		"PS": "West Bank", "PW": "Palau", "PT": "Portugal", "SJ": "Svalbard and Jan Mayen", "PY": "Paraguay",
		"IQ": "Iraq", "PA": "Panama", "PF": "French Polynesia", "PG": "Papua New Guinea", "PE": "Peru", "PK": "Pakistan",
		"PH": "Philippines", "PN": "Pitcairn", "PL": "Poland", "PM": "Saint Pierre and Miquelon", "ZM": "Zambia",
		"EH": "Western Sahara", "EE": "Estonia", "EG": "Egypt", "ZA": "South Africa", "EC": "Ecuador", "IT": "Italy",
		"VN": "Vietnam", "SB": "Solomon Islands", "ET": "Ethiopia", "SO": "Somalia", "ZW": "Zimbabwe",
		"SA": "Saudi Arabia", "ES": "Spain", "ER": "Eritrea", "ME": "Montenegro", "MD": "Moldova",
		"MG": "Madagascar", "MF": "Saint Martin (French part)", "MA": "Morocco", "MC": "Monaco", "UZ": "Uzbekistan",
		"MM": "Myanmar", "ML": "Mali", "MO": "Macao", "MN": "Mongolia", "MH": "Marshall Islands",
		"MK": "Macedonia", "MU": "Mauritius", "MT": "Malta", "MW": "Malawi", "MV": "Maldives",
		"MQ": "Martinique", "MP": "Northern Mariana Islands", "MS": "Montserrat", "MR": "Mauritania",
		"IM": "Isle of Man", "UG": "Uganda", "TZ": "United Republic of Tanzania", "MY": "Malaysia", "MX": "Mexico",
		"IL": "Israel", "FR": "France", "IO": "British Indian Ocean Territory",
		"SH": "Saint Helena, Ascension and Tristan da Cunha", "FI": "Finland", "FJ": "Fiji",
		"FK": "Falkland Islands", "FM": "Micronesia, Federated States of", "FO": "Faroe Islands",
		"NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway", "NA": "Namibia", "VU": "Vanuatu", "NC": "New Caledonia",
		"NE": "Niger", "NF": "Norfolk Island", "NG": "Nigeria", "NZ": "New Zealand", "NP": "Nepal", "NR": "Nauru",
		"NU": "Niue", "CK": "Cook Islands", "CI": "Ivory Coast", "CH": "Switzerland", "CO": "Colombia",
		"CN": "China", "CM": "Cameroon", "CL": "Chile", "CC": "Cocos (Keeling) Islands", "CA": "Canada",
		"CG": "Republic of the Congo", "CF": "Central African Republic", "CD": "Democratic Republic of the Congo",
		"CZ": "Czech Republic", "CY": "Northern Cyprus", "CX": "Christmas Island", "CR": "Costa Rica",
		"CW": "Cura\u00e7ao", "CV": "Cabo Verde", "CU": "Cuba", "SZ": "Swaziland", "SY": "Syria",
		"SX": "Sint Maarten (Dutch part)", "KG": "Kyrgyzstan", "KE": "Kenya", "SS": "South Sudan", "SR": "Suriname",
		"KI": "Kiribati", "KH": "Cambodia", "KN": "Saint Kitts and Nevis", "KM": "Comoros", "ST": "Sao Tome and Principe",
		"SK": "Slovakia", "KR": "South Korea", "SI": "Slovenia", "KP": "North Korea", "KW": "Kuwait",
		"SN": "Senegal", "SM": "San Marino", "SL": "Sierra Leone", "SC": "Seychelles", "KZ": "Kazakhstan",
		"KY": "Cayman Islands", "SG": "Singapore", "SE": "Sweden", "SD": "Sudan", "DO": "Dominican Republic",
		"DM": "Dominica", "DJ": "Djibouti", "DK": "Denmark", "VG": "Virgin Islands, British", "DE": "Germany",
		"YE": "Yemen", "DZ": "Algeria", "US": "United States of America", "UY": "Uruguay", "YT": "Mayotte",
		"UM": "United States Minor Outlying Islands", "LB": "Lebanon", "LC": "Saint Lucia",
		"LA": "Laos", "TV": "Tuvalu", "TW": "Taiwan, Province of China", "TT": "Trinidad and Tobago", "TR": "Turkey",
		"LK": "Sri Lanka", "LI": "Liechtenstein", "LV": "Latvia", "TO": "Tonga", "LT": "Lithuania", "LU": "Luxembourg",
		"LR": "Liberia", "LS": "Lesotho", "TH": "Thailand", "TF": "French Southern and Antarctic Lands", "TG": "Togo",
		"TD": "Chad", "TC": "Turks and Caicos Islands", "LY": "Libya", "VA": "Holy See (Vatican City State)",
		"VC": "Saint Vincent and the Grenadines", "AE": "United Arab Emirates", "AD": "Andorra",
		"AG": "Antigua and Barbuda", "AF": "Afghanistan", "AI": "Anguilla", "VI": "Virgin Islands, U.S.", "IS": "Iceland",
		"IR": "Iran", "AM": "Armenia", "AL": "Albania", "AO": "Angola", "AQ": "Antarctica", "AS": "American Samoa",
		"AR": "Argentina", "AU": "Australia", "AT": "Austria", "AW": "Aruba", "IN": "India", "AX": "\u00c5land Islands",
		"AZ": "Azerbaijan", "IE": "Ireland", "ID": "Indonesia", "UA": "Ukraine", "QA": "Qatar", "MZ": "Mozambique",
		"XK": "Kosovo"
	}

	const theme = {
		color: [
			'#26B99A', '#34495E', '#BDC3C7', '#3498DB',
			'#9B59B6', '#8abb6f', '#759c6a', '#bfd3b7'
		],

		title: {
			itemGap: 8,
			textStyle: {
				fontWeight: 'normal',
				color: '#408829'
			}
		},

		toolbox: {
			color: ['#408829', '#408829', '#408829', '#408829']
		},

		tooltip: {
			backgroundColor: 'rgba(0,0,0,0.5)',
			axisPointer: {
				type: 'line',
				lineStyle: {
					color: '#408829',
					type: 'dashed'
				},
				crossStyle: {
					color: '#408829'
				},
				shadowStyle: {
					color: 'rgba(200,200,200,0.3)'
				}
			}
		},

		dataZoom: {
			dataBackgroundColor: '#eee',
			fillerColor: 'rgba(64,136,41,0.2)',
			handleColor: '#408829'
		},
		grid: {
			borderWidth: 0
		},

		categoryAxis: {
			axisLine: {
				lineStyle: {
					color: '#408829'
				}
			},
			splitLine: {
				lineStyle: {
					color: ['#eee']
				}
			}
		},

		valueAxis: {
			axisLine: {
				lineStyle: {
					color: '#408829'
				}
			},
			splitArea: {
				show: true,
				areaStyle: {
					color: ['rgba(250,250,250,0.1)', 'rgba(200,200,200,0.1)']
				}
			},
			splitLine: {
				lineStyle: {
					color: ['#eee']
				}
			}
		},
		timeline: {
			lineStyle: {
				color: '#408829'
			},
			controlStyle: {
				normal: {color: '#408829'},
				emphasis: {color: '#408829'}
			}
		},

		k: {
			itemStyle: {
				normal: {
					color: '#68a54a',
					color0: '#a9cba2',
					lineStyle: {
						width: 1,
						color: '#408829',
						color0: '#86b379'
					}
				}
			}
		},
		map: {
			itemStyle: {
				normal: {
					areaStyle: {
						color: '#ddd'
					},
					label: {
						textStyle: {
							color: '#c12e34'
						}
					}
				},
				emphasis: {
					areaStyle: {
						color: '#99d2dd'
					},
					label: {
						textStyle: {
							color: '#c12e34'
						}
					}
				}
			}
		},
		textStyle: {
			fontFamily: 'Arial, Verdana, sans-serif'
		}
	};

	$('#app_select').select2({
		placeholder: 'Select an application',
		// allowClear: true
	});
	$('#tags_select').select2({
		placeholder: 'Select a tags',
		// allowClear: true
	});
	$('#status_code').select2({
		placeholder: 'Select a status code',
		// allowClear: true
	});

	$('#all_tags').on('click', function(){
		const all_options = [];
        $('#tags_select > option').each(function(){
            all_options.push($(this).val());
        })

        $('#tags_select').val(all_options).trigger('change.select2');
        geo_ip();
	});

	$('#all_apps').on('click', function(){
		const all_options = [];
        $('#app_select > option').each(function(){
            all_options.push($(this).val());
        })

        $('#app_select').val(all_options).trigger('change.select2');
        geo_ip();
	});

	$('#no_apps').on('click', function(){
		$('#app_select').val('data', null).trigger('change.select2');
		geo_ip();
	})

	$('#no_tags').on('click', function(){
		$('#tags_select').val('data', null).trigger('change.select2');
		geo_ip();
	})

	const chart_map = echarts.init(document.getElementById('chart_map'), theme);

	function geo_ip(){
		const apps  = $('#app_select').val();
		const codes = $('#status_code').val()
		const tags  = $('#tags_select').val()

		$.post(
			'/reporting/map/',
			{
				'tags'   : JSON.stringify(tags),
				'codes'  : JSON.stringify(codes),
				'apps_id': JSON.stringify(apps)
			},

			function(response){
				if (typeof(response) === "string"){
					window.location.href = window.location.href;
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

				const options = {
					title: {
						text: 'Web Traffic for the last 10 minutes (number of hits, only geo-localized hits are shown)',
						x: 'center',
						y: 'top'
					},
					tooltip: {
						trigger: 'item',
						formatter: function(params) {
							if (params.value === "-")
								params.value = 0;

							return params.name + ": " + params.value;
						}
					},
					visualMap: {
				        min: 0,
				        max: response['max'],
				        text:['High','Low'],
				        realtime: true,
				        calculable: true,
				        inRange: {
				            color: ['#E94825', '#E96B2E', '#E8A442', '#E5D257']
				        }
    				},
					series: [{
						name: 'Real time hits',
						type: 'map',
						mapType: 'world',
						roam: 'scale',
						itemStyle: {
							emphasis: {
								label: {
									show: true
								}
							}
						},
						data: []

					}]
				};

				if (jQuery.isEmptyObject(response.results) || typeof(response.results) === 'string'){
					options.visualMap = undefined;
					const errmsg = typeof(response.results) === 'string' ? response.results : ["No data available",
					"for the last 10 minutes"].join("\n");
                    options.graphic = {
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
				                    text: errmsg,
				                    textAlign: 'center',
				                    font: 'bold 17px arial, sans-serif',
				                    fill: '#FFA726'
				                }
							}
				        ]
					}
                } else {
					const data = []

					for (const result_key of Object.keys(response.results)) {
						data.push({
							'name': country[result_key],
							'value': response.results[result_key]
						});
				    }

					options.series[0].data = data;
				}
				chart_map.clear();
				chart_map.setOption(options);
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
    } else {
		$('.reload_map').on('select2:select', function(){
			geo_ip();
		})

		geo_ip();
		setInterval(function(){
			geo_ip();
		}, 2000);
    }
})
