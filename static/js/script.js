/* global $ */

/* eslint-env jquery */
$('document').ready(function () {

$(function() {
    $('#btnSignUp').click(function() {
 
        $.ajax({
            url: '/signUp',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                alert(response);
            },
            error: function(error) {
                console.log(error);
                alert(error);
            }
        });
    });
});
    
});