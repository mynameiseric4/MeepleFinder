let get_input_coefficients = function() {
    let game1 = $("input#game1").val()
    let game2 = $("input#game2").val()
    let game3 = $("input#game3").val()
    return {'game1': game1.toString(),
            'game2': game2.toString(),
            'game3': game3.toString()}
};

let send_coefficient_json = function(coefficients) {
    $.ajax({
        url: '/predict',
        contentType: "application/json; charset=utf-8",
        type: 'POST',
        success: function (data) {
            display_solutions(data);
        },
        data: JSON.stringify(coefficients)
    });
};

let display_solutions = function(solutions) {
    $("span#prediction").html(solutions)
};


$(document).ready(function() {

    $("button#predict").click(function() {
        let coefficients = get_input_coefficients();
        send_coefficient_json(coefficients);
    })

})
