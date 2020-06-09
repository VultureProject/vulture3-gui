$('.config_svm').on('click', function(){
    $('#modal_config_svm').modal('show');
    var info = $(this).data('value').split("/")
    var dataset_id = info[0]
    var nb_logs = parseFloat(info[1])

    $("#dataset_id").val(dataset_id);

    $("#Req_per_min_per_user").val(1/(nb_logs));
    $("#Req_per_min_per_IP").val(1/(nb_logs));
    $("#HTTP_code_bytes_sent").val(1/(nb_logs));
    $("#HTTP_code_bytes_received").val(1/(nb_logs));
    $("#Levenstein").val(1/(nb_logs));
    $("#Ratio").val(1/(nb_logs));
});


$('#btn-save-config').on('click', function(){
    var dataset_id = $('#dataset_id').val()

    $.post(
        '/dataset/build/'+dataset_id,
        {
            'Req_per_min_per_user'    : $('#Req_per_min_per_user').val(), 
            'Req_per_min_per_IP'      : $('#Req_per_min_per_IP').val(),
            'HTTP_code_bytes_sent'    : $('#HTTP_code_bytes_sent').val(), 
            'HTTP_code_bytes_received': $('#HTTP_code_bytes_received').val(), 
            'Levenstein'              : $('#Levenstein').val(),
            'Ratio'                   : $('#Ratio').val()
        },
        function(data){
            if (data['status']){
                $('#svm_'+dataset_id+" .state").hide();
                $('#svm_'+dataset_id+" .wait_ajax_dataset").show();
                $('#svm_'+dataset_id).data('status', "False");
            }
        })
    }
)


var interval = setInterval(function(){
    $('.svm_built').each(function(){
        var line = $(this);
        if ($(line).data('status') === 'False'){
            $.post(
                '/dataset/status',
                {
                    'dataset_id': $(line).data('id'),
                    'type': 'svm_built'
                },

                function(response){
                    if (response['status']){
                        setTimeout(function(){
                            window.location.href = window.location.href;
                        }, 2000)
                    }
                }
            )
        }
    })

    $('.dataset_built').each(function(){
        var line = $(this);
        if ($(line).data('status') === 'False'){
            $.post(
                '/dataset/status',
                {
                    'dataset_id': $(line).data('id'),
                    'type': 'built'
                },

                function(response){
                    if (response['status'])
                        window.location.href = window.location.href;
                }
            )
        }
    })
}, 2000)