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
        "timeOut": "6500",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
      }
    var room = "Main"
    console.log("http://" + document.domain + ":" + location.port)
    console.log(typeof(location.port))
    /*
    if(location.port == ""){
        location.port = "80"
    }
    */
    var socket = io("http://" + document.domain + ":" + location.port);
    socket.on('connect', function() {
        socket.send("Connected!")
        socket.emit("join", {"room" : "Main"})
    });
    socket.on('disconnect', function(){
        socket.emit("disconnect")
    });
    socket.on("message", function(obj){ // add connected handler
        console.log(obj)
        if(obj["server"] != "yes"){
        msg = addNewlines(obj["msg"])
        username = obj["user"]
        }
        else{
            msg = addNewlines(obj["msg"]) // not really needed but it's fine
            username = "Server"
        }
        console.log("recived")
        console.log(msg)
        console.log(username)
        var entites = "";
        $(entites).html(msg)
        console.log(entites)
        var create_msg = `<li class="d-flex justify-content-between mb-4">
                        <div class="chat-body white p-3 ml-2 z-depth-1">
                            <div class="header">
                                <strong class="primary-font">`+ username +`</strong>
                                <small class="pull-right text-muted"><i class="far fa-clock"></i>` + obj["time"] + `</small>
                            </div>
                            <hr class="w-100">
                            <p id="new-msg">` + 
                                msg
                                +
                                `
                            </p>
                        </div>
                    </li>`
        $("#messages").append(create_msg)
    });
    socket.on("room-add", function(data){
        if(data["msg"] == "an unexpected error has occurred, please choose a different password"){
        toastr["error"](data["msg"], "error")
        }
        else if(data["msg"] == "Room already exists"){
        toastr["error"]("it seems like the room already exists", "Can't create the room")
        }
        else{
        console.log(data["password"])
        if(data["password"] == ""){
            $(".public-dropdown").append('<a class="dropdown-item this-is-navbar room">' +data["room"] + '</a>')
            $(".all-rooms-dropdown").append('<a class="dropdown-item this-is-navbar room">' +data["room"] + '</a>')
        }
        else{
            $(".private-dropdown").append('<a class="dropdown-item this-is-navbar room">' +data["room"] + '</a>')
            $(".all-rooms-dropdown").append('<a class="dropdown-item this-is-navbar room">' +data["room"] + '</a>')
        }
        toastr["success"]("Your room has successfully created", "Room created")
        new_room = data["room"]
        toastr["success"]("You have joined" + new_room, "Room created")
        $(document).ready(function(){
            socket.emit('leave', {"room" : room})
            socket.emit("join", {"room" : new_room})
        });
        room = new_room
        $("#modalAddRoom .close").click()
        $("#messages").html("");
        }
    });
    $("#input").keydown(function(e){
        if(e.keyCode == 13){ // 13 is the enter key
        sendMessage()
        $("#input").val("")
        }
    });
    $("#send").click(function(){
        console.log("clicked")
        sendMessage()
        $("#input").val("")
    });
    var new_room = ""
    var room_pass = "" // randomize 
    $(".dropdown-menu").on('click', '.room', function(event){ // I have to use the .on method because .click doesn't work when data is appended
        console.log("Room clicked") 
        new_room = $(event.target).text() // check if it exists in the database
        event.preventDefault()
        console.log(new_room);
        if(room == new_room){
            toastr["error"]("You are already in the room", "Can't join the room")
        }
        else{
            $.ajax({
            type: "POST",
            url: "/validate",
            data: new_room,
            success: function(pass){
                room_pass = pass; // pass is the room password
                if(pass != "False"){ 
                    console.log("opening")
                    $("#password-validation").modal("toggle");
                }
                else{
                console.log("no password")
                $("#messages").html("");
                socket.emit('leave', {"room" : room})
                socket.emit("join", {"room" : new_room})
                var room_msg = "You have joined " + new_room
                toastr["success"](room_msg, "Room joined")
                room = new_room
                }
            }
            });
        }
    });
    
    $("#room-password-btn").click(function(){
        console.log("Execute")
        user_password = $("#room-password-val").val()
        console.log(user_password)
        console.log(room_pass)
        if(user_password == room_pass){
        $("#messages").html("");
        $("#password-validation .close").click()
        toastr["success"]("Entering you into the room!", "Corrent password")
        console.log("Joining a room")
        socket.emit('leave', {"room" : room})
        socket.emit("join", {"room" : new_room})
        room = new_room
        }
        else{
        toastr["error"]("Sorry, you have entered the wrong password. Try again.", "Wrong password")
        }
    });
    
    $('#password-validation').on('shown.bs.modal', function () {
        $('#room-password-val').trigger('focus');
    });
    
    $("#new-room").click(function(){
        var created_room = $("#new-room-input").val();
        $("#new-room-input").val("");
        console.log($('#room-password-check').is(':checked'))
        if($('#room-password-check').is(':checked')){
        password = $("#room-password").val()
        } 
        else{
        password = ""
        }
        socket.emit('room-add', {"name" : created_room, "room password" : password})
        /*
        socket.emit('leave', {"room" : room})
        socket.emit("join", {"room" : created_room})
        var room_msg = "You have joined " + created_room
        toastr["success"](room_msg, "Room joined")
        */
    });
    $("#modalAddFriend").on('shown.bs.modal', function () {
        $('#friend-username-val').trigger('focus');
    });
    $("#friend-btn").click(function(){
        console.log("clicked")
        var input_username = $("#friend-username-val").val()
        console.log(input_username)
        socket.emit("friend-add", {"username" : input_username})
    });
    socket.on("friend-add", function(msg){
        if(msg == "Friend request sent!"){
        toastr["success"]("The friend request sent successfully!", msg)
        }
        else{
        toastr["error"](msg, msg)
        }
    });
    var $dropDownItems = $('.notifi-drop').children();
    $dropDownItems.on('click', function() {
        if(this.textContent == "Reject"){
        var index = $dropDownItems.index(this) - 1
        var text = $dropDownItems.eq(index).text()
        console.log(index)
        for(var i = $dropDownItems.index(this) - 1; i <= $dropDownItems.index(this)+3; i++){
            $dropDownItems.eq(i).remove()
            console.log( $dropDownItems.eq(i).text())
        }
        socket.emit("friend-request-handler", {"type" : "Reject", "notification" : text})
        console.log(text)
        }
        else if(this.textContent == "Accept"){
        var index = $dropDownItems.index(this) - 3
        var text = $dropDownItems.eq(index).text()
        console.log(index)
        for(var i = $dropDownItems.index(this) - 3; i <= $dropDownItems.index(this)+ 1; i++){
            $dropDownItems.eq(i).remove()
            console.log( $dropDownItems.eq(i).text())
        }
        console.log(text)
        socket.emit("friend-request-handler", {"type" : "Accept", "notification" : text})
        }
        console.log('index: ', $dropDownItems.index(this), 'text: ', this.textContent)
    });
    socket.on("friend-request-handler", function(data){
        msg = data["msg"]
        if(msg != "Error"){
        notification = data["notification"]
        var notifi_length = $("#notification-length").text()
        $("#notification-length").text(notifi_length - 1)
        if(data["type"] == "Accept"){ // could be if it's undefined I guess
        socket.emit("add-friend-requester-live", {"accepted from" : "{{username}}", "requester" : data["name"]})
        addFriendToList(data["name"])
        }
        toastr["success"](msg, msg)
        }
        else{
        toastr["error"]("There was a problem. Please try again.", msg)
        }
    });
    $(".friend-div").on('click', '.friend-username' , function(){
        var friend = $(this).text()
        console.log(room)
        entered_room = room;
        socket.emit("friends-dm", friend)
        socket.emit("dm-history", friend)
        socket.on("dm-history", function(data){
        if(data == "the dm was not found in the db"){
        toastr["error"](data,data)
        }
        else{
        var sent_user = data["user"] // array
        var user_msg = data["msg"] // array same length
        var msg_time = data["time"] // array same length
        console.log("in")
        if(entered_room != room){
            for(var i = 0; i<user_msg.length; i++){
            $("#messages").append(`
            <li class="d-flex justify-content-between mb-4">
                <div class="chat-body white p-3 ml-2 z-depth-1">
                <div class="header">
                    <strong class="primary-font">` + sent_user[i] +`</strong>
                    <small class="pull-right text-muted"><i class="far fa-clock"></i>` + msg_time[i] + `</small>
                </div>
                    <hr class="w-100">
                    <p>`
                    + user_msg[i] +
                    `</p>
                </div>
            </li>
            `)
            }
            console.log("in")
            console.log( data["friend"])
            $('.friend-name > #' + data["friend"]).html(user_msg[user_msg.length - 1]);
        }
        }
        });
    });
    socket.on("friends-dm", function(data){
        if(room == data){
        toastr["error"]("You are already in this dm", "You are already in this dm")
        }
        else if(data=="Friend not found"){
        toastr["error"]("Make sure you are not logged in to 2 diffrent users/this is your actual friend", "An unexpected error")
        }
        else{
        $("#messages").html("");
        toastr["success"]("Going to the dm's", "dm")
        socket.emit('leave', {"room" : room, "dm" : "True"})
        socket.emit("join", {"room" : data, "dm" : "True"})
        $("#messages").animate({ scrollTop: $('#messages').prop("scrollHeight")}, 500);
        room = data;
        }
    }); 
    socket.on("get-dm-data", function(data){
        console.log("recived")
        friend_name = data["friend"] // potentiality too.
        potentiality_other_friend = data["you"] // to the other user the user who sent the message is "you" and he is the friend
        date = data["date"]
        last_msg = data["last message"]
        /*
        console.log("dm data")
        console.log("{{username}}")
        console.log(data["friend"])
        console.log(data["you"])
        */
        console.log("{{username}}" == data["friend"])
        console.log("{{username}}" == data["you"])
        if("{{username}}" == data["friend"]){ // I have to identify the user first. The user could just inspect the elements and he could see this info.
        $("#friend-" + potentiality_other_friend + " .date:first").html(date)
        $("#friend-" + potentiality_other_friend + " .last-message:first").html(last_msg)
        }
        else if("{{username}}" == data["you"]){
        $("#friend-" + friend_name + " .date:first").html(date)
        $("#friend-" + friend_name + " .last-message:first").html(last_msg)
        }
    });
    socket.on("add-friend-requester-live", function(data){
        console.log("add-friend-requester-live")
        if(data["friend"] == "{{username}}"){
        console.log(data["accepted from"])
        addFriendToList(data["accepted from"]);
        toastr["success"]("Your friend request was accepted from " + data["accepted from"], "Friend request")
        }
    });
    function addNewlines(str) {
    var result = '';
    while (str.length > 0) {
        result = result + str.substring(0, 120) + '\n';
        str = str.substring(120);
    }
    return result;
    }
    function htmlEntities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function sendMessage(){
    var inp = $("#input").val();
    inp = htmlEntities(inp);
    socket.send({"message" : inp, "room" : room})
    $("#messages").animate({ scrollTop: $('#messages').prop("scrollHeight")}, 500);
    checkifDM();
    }
    function checkifDM(){
    socket.emit("get-dm-data", room)
    }
    function addFriendToList(friend_name){
    current_date_time = new Date();
    date =  current_date_time.getDate()+'/'+(current_date_time.getMonth()+1)+'/'+ current_date_time.getFullYear()
    time = current_date_time.getHours() + ":" + current_date_time.getMinutes();
    dateTime = ' ' + time + ' ' + date;
    console.log(dateTime)
        var create_msg = `
        <div id="friend-` +  friend_name + `">
        <li class="p-2">
            <a class="d-flex justify-content-between">
            <div class="text-small">
                <button type="button" class="btn btn-primary friend-username">` + friend_name + `</button>
                <p class="last-message text-muted"></p>
            </div>
            <div class="chat-footer">
                <p class="text-smaller text-muted mb-0 date">` + dateTime + `</p>
                <span class="text-muted float-right"><i class="fas fa-mail-reply" aria-hidden="true"></i></span>
            </div>
            </a>
        </li>
        </div>
        `
        $(".friend-list").append(create_msg);
    
    }
});