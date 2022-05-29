/*
 * Javascript file to implement client side usability for 
 * Operating Systems Desing exercises.
 */
 var api_server_address = "http://34.141.27.32:5001/"
 var msg_router_server_address = "http://34.141.27.32:5002/"

 var get_current_sensor_data = function() {
    $.getJSON( api_server_address+"device_state", function( data ) {
        $.each(data, function( index, item ) {
          $("#"+item.room).data(item.type, item.value);
          if (item.type === "outdoor-mode") {
              if (item.value == "1") {
                  $("#"+item.room).css("background-color", "#39c918");
              } else {
                  $("#"+item.room).css("background-color", "#b6d1ed");
              }
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

$("#blind_active").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"blind-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#blind_value").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"blind-level",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#indoor_light_active").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"indoor-light-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#indoor_light_value").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"indoor-light-level",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#outdoor_light_active").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"outdoor-light-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#outdoor_light_value").change(function() {
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: api_server_address+"device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"outdoor-light-level",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

function paint_facade(){
     let letter = document.querySelector("input").value;
     let A = [1,2,6,4,5,10,13,28,33,38];
     let B = [7,8,9,12,13,14,27,28,29,32,33,34,40,5,20,25];
     let C = [28,29,30,15,25,20,13,14,18,19,23,24]
     let D = [12,17,18,22,23,27,28,14,19,24,29,40,5,13,7,8,9,32,33,34]
     let E = [7,8,9,10,12,13,14,15,22,23,24,25,27,28,29,30,32,33,34,35]
     let F = [7,8,9,10,12,13,14,15,22,23,24,25,27,28,29,30,32,33,34,35,37,38,39,40]
     let G = [7,8,9,10,12,13,14,15,17,18,19,20,22,27,28,29,32,33,34]
     let H = [2,3,4,7,8,9,12,13,14,22,23,24,27,28,29,32,33,34,37,38,39]
     let I = [6,7,9,10,11,12,14,15,16,17,19,20,21,22,24,25,26,27,29,30,31,32,34,35]
     let matrix = [A,B,C,D,E,F,G,H,I]
     let letters = "abcdefghijklmnopqrstuvwxyz"
     let index = letters.indexOf(letter.toLowerCase())
    if (index == 0 && letter.toUpperCase() != "A"){
         for (var i = 1; i < 41; i++) {
            document.getElementById("Room" + i).style.background = "#b6d1ed";
         }
         return
     }
     console.log(index)
    console.log(letter)
     for (var i = 1; i < 41; i++) {
         if (matrix[index].includes(i) == false) {
             document.getElementById("Room" + i).style.background = "red";
         }
         else{
             document.getElementById("Room" + i).style.background = "#b6d1ed";
         }
     }

}

$("#rooms").on("click", "td", function() {
    $("#room_id").text($( this ).attr("id") || "");
    $("#temperature_value").text($( this ).data("temperature") || "");
    $("#presence_value").text($( this ).data("presence") || "0");
    $("#air_conditioner_mode").val($( this ).data("air-mode"));
    $("#air_conditioner_value").text($( this ).data("air-level") || "");
    $("#indoor_light_active").val($( this ).data("indoor-mode"));
    $("#indoor_light_value").val($( this ).data("indoor-level"));
    $("#outdoor_light_active").val($( this ).data("outdoor-mode"));
    $("#outdoor_light_value").val($( this ).data("outdoor-level"));
    $("#blind_active").val($( this ).data("blind-mode"));
    $("#blind_value").val($( this ).data("blind-level"));

});

draw_rooms()
setInterval(get_current_sensor_data,2000)
