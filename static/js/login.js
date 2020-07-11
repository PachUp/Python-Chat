$(document).ready(function(){
toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": true,
    "progressBar": true,
    "positionClass": "toast-top-right",
    "preventDuplicates": false,
    "showDuration": "300",
    "hideDuration": "1000",
    "timeOut": "5000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
    }
    $("#button-id").click(function(){
        var res = grecaptcha.getResponse();
        console.log(res.length);
        if(res.length != 0){ //It should be an empty string 
            var data = $("form").serialize();
            if ($('#autoSizingCheck').is(':checked')){
                data = data + "&CheckBox=" + "True" // maybe change in the future(that's why I have the +), option is disabled for now
            }
            else{
                data = data + "&CheckBox=" + "True" // maybe change in the future(that's why I have the +), option is disabled for now
            }
            console.log(data);
            $.ajax({
                type: "POST",
                url: 'login',
                data: data,
                success: function(res){
                    console.log(res)
                    if(res=="username"){
                        grecaptcha.reset();
                        toastr["error"]("This username is not in my database.", "This username doesn't exist")
                    } 
                    else if(res=="password"){
                        grecaptcha.reset();
                        toastr["error"]("Not the right password. Please try again.", "Wrong password")
                        
                    }
                    else{
                        if(res =="email"){
                            grecaptcha.reset();
                            toastr["error"]("email error", "email error")
                        }
                        else if(res=="Great"){
                            $("#pass-wrong").html("great");
                            $("#user-wrong").html("great");
                            toastr["success"]("Login you in!", "Success!")
                            $(location).attr("href", "")
                        }
                    }
                }
            });
        }
        else{
            toastr["error"]("You have to check the captcha box to make sure that you are a human", "Please check the captcha box")
        }
    });
});