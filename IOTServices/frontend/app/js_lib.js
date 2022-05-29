/*
 * Javascript file to implement client side usability for 
 * Operating Systems Desing exercises.
 */
 var api_server_address = "http://34.141.18.88:5001/"

 var get_current_sensor_data = function() {
    $.getJSON( api_server_address+"device_state", function( data ) {
        $.each(data, function( index, item ) {
          $("#"+item.room).data(item.type, item.value);
          if (item.type === "outdoor-status" && item.value === "1") {
              $("#"+item.room).css("background-color", "#39c918");
          }
      });
    });
}

var draw_rooms = function() {
    $("#rooms").empty()
    var room_index = 1;
    for (var i = 0; i < 8; i++) {
        $("#rooms").append("<tr id='floor"+i+"'></tr>")
        for (var j = 0; j < 5; j++) {
            $("#floor"+i).append("\
                <td \
                data-bs-toggle='modal' \
                data-bs-target='#room_modal' \
                class='room_cell'\
                id='Room"+room_index+"'\
                > \
                Room "+room_index+"\
                </td>"
                )
            room_index++
        }
    }
}

$("#air_conditioner_mode").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"air-conditioner-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#rooms").on("click", "td", function() {
    $("#room_id").text($( this ).attr("id") || "");
    $("#temperature_value").text($( this ).data("temperature") || "");
    $("#presence_value").text($( this ).data("presence") || "0");
    $("#air_conditioner_mode").val($( this ).data("air-conditioner-mode"));
    $("#air_conditioner_value").text($( this ).data("air-conditioner-level") || "");
    $("#indoor_light_active").val($( this ).data("indoor-mode"));
    $("#indoor_light_value").val($( this ).data("indoor-level"));
    $("#outdoor_light_active").val($( this ).data("outdoor-mode"));
    $("#outdoor_light_value").val($( this ).data("outdoor-level"));
    $("#blind_active").val($( this ).data("blind-mode"));
    $("#blind_value").val($( this ).data("blind-level"));

});

draw_rooms()
setInterval(get_current_sensor_data,5000)
