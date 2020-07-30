from flask import Flask, render_template, url_for,request,redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import func
from hashlib import md5
import datetime
import secrets
import os
import html
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY_C"]
socketio = SocketIO(app,cors_allowed_origins=['http://chat-py.herokuapp.com', 'http://127.0.0.1:5000'])
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["HEROKU_POSTGRESQL_PUCE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
server_rooms = ["Main", "Vanila", "Chocolate"] # a 'const' var
 
class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.TEXT)
    password = db.Column(db.TEXT)
    email = db.Column(db.TEXT)
    profile_picture = db.Column(db.TEXT, default="https://toppng.com/uploads/preview/user-font-awesome-nuevo-usuario-icono-11563566658mjtfvilgcs.png")
    active_sockets = db.relationship('activeSockets', backref='user_active_sockets')
    notifications = db.relationship('notifications', backref='user_notification')
    friends = db.relationship('friends', backref='user_friends')


class notifications(db.Model): # maybe add a filter option (friend, server notification etc')
    id = db.Column(db.Integer, primary_key = True)
    notification = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 


class friends(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    friend_name = db.Column(db.TEXT)
    last_text_message = db.Column(db.TEXT, default="")
    last_message_time = db.Column(db.TEXT, default=datetime.datetime.now().strftime("%H:%M %d/%m/%Y")) # I am not using datetime because I need to return a string of the time anyway
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 

class activeSockets(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    socket = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class allRooms(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    room_messages = db.Column(db.TEXT) # create one to many relationship to present the messages
    rooms = db.Column(db.TEXT) # change name to room
    room_password = db.Column(db.TEXT)
    room_owner = db.Column(db.TEXT)

class friendsdms(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_user = db.Column(db.TEXT)
    second_user = db.Column(db.TEXT)
    first_user_unread_messages = db.Column(db.Integer)
    second_user_unread_messages = db.Column(db.Integer)
    room = db.Column(db.TEXT)
    history = db.relationship('dmHistroy', backref='users_dms')

class dmHistroy(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    msg = db.Column(db.TEXT)
    msg_from_user = db.Column(db.TEXT)
    msg_time = db.Column(db.TEXT)
    friends_dm_id = db.Column(db.Integer, db.ForeignKey('friendsdms.id')) 


@app.route("/", methods=["GET"])
@login_required
def index():
    print("index")
    for i in current_user.active_sockets:
        print("current open sockets of the user: ", end="")
        print(i.socket)
    rooms = allRooms.query.all()
    notifi = []
    user_friends = []
    friend_profile_pic = []
    last_message_time_with_friends = []
    last_message = []
    public_rooms = []
    online_users = []
    private_rooms = []
    for i in current_user.notifications:
        notifi.append(i.notification)
    friends_obj_o_1 = friendsdms.query.filter_by(first_user=current_user.username).first()
    friends_obj_o_2 = friendsdms.query.filter_by(second_user=current_user.username).first()
    """
    if friends_obj_o_1 is not None:
        for i in range(len(friends_obj_o_1.history)):
            if(i == len(friends_obj_o_1.history) - 1):  
                last_message.append(friends_obj_o_1.history[i])
    if friends_obj_o_2 is not None:
        for i in range(len(friends_obj_o_2.history)):
            if(i == len(friends_obj_o_2.history) - 1):  
                last_message.append(friends_obj_o_2.history[i])
    """
    for i in current_user.friends:
        user_friends.append(i.friend_name)
        last_message_time_with_friends.append(i.last_message_time)
        last_message.append(i.last_text_message)
    # seprated loops so it'll be easier to see what is going on
    for i in current_user.friends:
        friend_obj_user = users.query.filter_by(username=i.friend_name).first()
        if friend_obj_user is not None:
            if friend_obj_user.username == current_user.username:
                continue
            if len(friend_obj_user.active_sockets) > 0:
                print("online")
                print(friend_obj_user.username)
                print(len(friend_obj_user.active_sockets))
                online_users.append(friend_obj_user.username) # I can do that because in the html file I loop though all the users by the same order
                friend_profile_pic.append(friend_obj_user.profile_picture)
            else:
                print("offline")
                print(len(friend_obj_user.active_sockets))
                online_users.append("offline")
    total_rooms = ["Main", "Vanila", "Chocolate"]
    for i in rooms:
        total_rooms.append(i.rooms)
        if i.room_password == "":
            public_rooms.append(i.rooms)
        else:
            private_rooms.append(i.rooms)
    print(server_rooms)
    return render_template("index.html", all_rooms=total_rooms,server_rooms= server_rooms,private_rooms=private_rooms,public_rooms=public_rooms ,notifications=notifi, user_friends=user_friends, username=current_user.username, last_message_time_with_friends=last_message_time_with_friends, last_message=last_message, online_users=online_users, friend_profile_pic=friend_profile_pic)

@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))

@app.route("/login", methods=["GET","POST"])
@login_manager.unauthorized_handler
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        check_box = request.form['CheckBox']
        print(check_box)
        print(check_box)
        send = ""
        user_check = bool(users.query.filter_by(username=username).first())
        pass_check = bool(users.query.filter_by(password=md5(password.encode("utf-8")).hexdigest()).first())
        if user_check and not pass_check:
            return "password"
        elif not user_check:
            return "username"
        else:
            user = users.query.filter_by(username=username,password=md5(password.encode("utf-8")).hexdigest()).first()
            db.session.commit()
            app.permanent_session_lifetime = False
            if check_box == "True": #always true for now
                login_user(user, remember=True)
            elif check_box == "False": #disabled for now
                login_user(user, remember=False)
            else:
                return "An unexpected error has occurred"
            return "Great"    
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect('/')
        else:
            return render_template('/login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        print(username)
        send = ""
        user_check = bool(users.query.filter(func.lower(users.username) == func.lower(username)).first())
        email_check = bool(users.query.filter_by(email=email).first())
        
        if (email_check) and (email[-10:] not in "@gmail.com" or email.count("@gmail.com") > 1) and user_check:
            print("all")
            return "all"
        elif user_check and (email[-10:] not in "@gmail.com" or email.count("@gmail.com") > 1):
            print("u e c")
            return "username exist email contain"
        elif user_check and email_check:
            print("u e e")
            return "username exist email exist"
        elif email_check:
            return "email exist"
        elif email[-10:] not in "@gmail.com" or email.count("@gmail.com") > 1:
            return "email contain"
        elif user_check:
            return "username exist"
        else:
            new_user = users(username = username, password=md5(password.encode("utf-8")).hexdigest(), email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect('/')
        else:
            return render_template('/register.html')

all_msgs_in_room = {} #this is to check if the quoted message exists because all of the main rooms doesn't have any histroy I can check on. I know, bad practice.
all_msgs_in_room["everyone"] = []
@socketio.on('message')
def handle_message(message):
    #new_msg = AllHistory(message=message)
    #db.session.add(new_msg)
    #db.session.commit()
    date = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
    try:
        print("In room")
        room=message["room"]
        print(message["room"])
        friend_obj = friendsdms.query.filter_by(room=room).first()  
        print(friend_obj) # should be none if it doesn't find it
        print(message)
        msg_njson = message["message"]
        msg_in_room = all_msgs_in_room[room]
        msg_in_room.append(msg_njson)
        print(msg_njson.startswith("[QUOTE "))
        print(msg_in_room)
        if(msg_njson.startswith("[QUOTE ")):
            print("pre quote")
            message["message"] = message_quote(msg_njson, msg_in_room)
        if friend_obj is not None:
            if current_user.username != friend_obj.first_user and current_user.username != friend_obj.second_user:
               emit("friend-add", "an unexpected error has occurred") # I did friend-add because it will show that there was a problem in toastr. it will happen if the user inspected the elemet to a diffrent user
            else: 
                print("not none2")
                print(message["message"])
                last_message = message["message"]
                friend = ""
                you = ""
                if friend_obj.first_user == current_user.username:
                    you = friend_obj.first_user
                    friend = friend_obj.second_user
                else:
                    you = friend_obj.second_user
                    friend = friend_obj.first_user
                print(you)
                print(friend)
                friends_obj = friends.query.filter_by(friend_name=friend, user_friends=current_user).first()
                friend_obj_user = users.query.filter_by(username=friend).first()
                your_obj = friends.query.filter_by(friend_name=current_user.username, user_friends=friend_obj_user).first()
                your_obj.last_text_message = last_message
                friends_obj.last_text_message = last_message
                db.session.commit()
                new_dm = dmHistroy(msg=last_message, msg_from_user=current_user.username, users_dms=friend_obj, msg_time=date)
                db.session.add(new_dm)
                db.session.commit()
                print("No exception")
                send({"msg" : message["message"], "user" : current_user.username, "time" : date, "server" : "no", "user profile picture": current_user.profile_picture}, room=room)
        else:
            send({"msg" : message["message"], "user" : current_user.username, "time" : date, "server" : "no", "user profile picture": current_user.profile_picture}, room=room)
    except Exception as e:
        print(e)
        print(type(message)) # server message
        if message == "Connected!":
            msg_in_room = all_msgs_in_room["everyone"]
            msg_in_room.append(current_user.username +" Has " + message)
            send({"msg" : current_user.username +" Has " + message, "time" : date, "server" : "yes", "user profile picture": current_user.profile_picture})

def message_quote(message_with_quote, msg_in_room):
    print("quote")
    message = message_with_quote
    message = message.split("[QUOTE ", 1)[1]
    print(message)
    if(message.startswith("user=")):
        message = message.split("user=", 1)[1]
        user = message.split("]", 1)[0]
        print(user)
        user_exist = bool(users.query.filter_by(username=user).first())
        if(user_exist) or user == "Server":
            print(message)
            message = message.split("[/QUOTE]", 1)[0]
            quote_msg = message.split("]", 1)[1]
            actual_message = message_with_quote.split("[/QUOTE]", 1)[1]
            quote_msg = quote_msg.replace("<br />", "", 1)
            print(all_msgs_in_room["everyone"])
            print(msg_in_room)
            print(quote_msg)
            if quote_msg.strip() in msg_in_room or quote_msg.strip() in all_msgs_in_room["everyone"]:    
                new_msg = '<footer class="blockquote-footer"><cite title="Source Title">By ' + user +': </cite>' + quote_msg +'</footer>' + actual_message
                print(new_msg)
                return new_msg
                    

@socketio.on('room-add') # Todo: need to check if the rooms has a password or not.
def room_add(data):
    print("adding")
    room_name = data["name"]
    room_name = html.escape(room_name)
    print(room_name)
    room_exist = False
    room_name_compare = room_name.lower()
    if room_name_compare == "main" or room_name_compare == "vanila" or room_name_compare == "chocolate":
        room_exist = True
    rooms_obj = allRooms.query.all()
    for i in rooms_obj:
        if i.rooms.lower() == room_name_compare:
            room_exist = True
    
    print(room_name)
    if room_exist is False:
        print("adding a room")
        owner = current_user.username
        room_password = data["room password"] # None for now
        print(room_password)
        password_is_dm = False
        for i in friendsdms.query.all():
            if room_password == i.room:
                password_is_dm = True
        if not password_is_dm:
            add_new_room = allRooms(rooms= room_name, room_password=room_password, room_owner= owner)
            db.session.add(add_new_room)
            db.session.commit()
            emit("room-add", {"msg" : "created!", "password" : room_password, "room" : room_name}) # send if the room is private or not
        else:
            emit("room-add", {"msg" : "an unexpected error has occurred, please choose a different password"}) # send if the room is private or not
    else:
        emit("room-add", {"msg" : "Room already exists"})

@socketio.on('join')
def on_join(data):
    #username = data['username']
    date = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
    room = data['room']
    all_msgs_in_room[room] = []
    dm = "False"
    try:
        dm = data["dm"]
    except:
        pass
    print("join " + room)
    join_room(room)
    if dm == "True":
        all_msgs_in_room["everyone"].append(current_user.username +' has entered the dm')
        send({"msg" : current_user.username +' has entered the dm', "server" : "yes", "time" : date, "user profile picture": current_user.profile_picture}, room=room) 
    else:
        all_msgs_in_room["everyone"].append(current_user.username +' has entered ' + room)
        send({"msg" : current_user.username +' has entered ' + room, "server" : "yes", "time" : date, "user profile picture": current_user.profile_picture}, room=room)
    
@socketio.on('friend-add')
def friend_add(data):
    friend_username = data["username"]
    all_users = users.query.all()
    found = False
    friend_exists = False
    for i in current_user.friends:
        if i.friend_name == friend_username:
            friend_exists = True
    if current_user.username == friend_username:
        emit("friend-add", "You can't send a friend request to yourself.")
        found = True
    elif friend_exists:
        found = True
        emit("friend-add", "You are already friends with " + friend_username)
    else:
        for i in all_users:
            print(i.username)
            if i.username == friend_username:
                found = True
                sent = False
                received = False
                for j in current_user.notifications:
                    if friend_username in j.notification:
                        received = True
                if not received:
                    user = users.query.filter_by(username=friend_username).first()
                    notification_msg = current_user.username + " Has added you as a friend!"
                    for j in user.notifications:
                        if j.notification == notification_msg:
                            sent = True
                    if not sent:
                        notifi = notifications(notification=notification_msg, user_notification=user)
                        db.session.add(notifi)
                        db.session.commit()
                        emit("friend-add", {"msg" :"Friend request sent!", "friend" : friend_username})
                    else:
                        emit("friend-add", "You have already sent the friend request")
                else:
                    emit("friend-add", "The user already sent you a friend request. Check your notifications! prehaps refresh the page")
    if not found:
        emit("friend-add", "The user does not exist.")

@socketio.on('friend-request-handler')
def friend_request_handler(data):
    print("friend-request-handler")
    request_status = data["type"]
    request_data = data["notification"]
    print(request_status)
    action = False
    for i in current_user.notifications:
        if i.notification == request_data:
            if request_status == "Accept":
                request_name = request_data.split(' ')[0]
                requester = users.query.filter_by(username=request_name).first()
                if requester is not None:
                    new_friend_requester = friends(friend_name=current_user.username, user_friends=requester)
                    new_friend = friends(friend_name=request_name, user_friends=current_user)
                    hash_salt = secrets.token_hex(6) # bascily creates 6 random chars and combines them to a string
                    room_hash = md5(str(current_user.username + requester.username + str(datetime.datetime.now()) + hash_salt).encode('utf-8')).hexdigest() # hashing MD5 with salt 
                    print(room_hash)
                    create_dm = friendsdms(first_user=current_user.username, second_user=requester.username,room=room_hash)
                    notifications.query.filter_by(notification=request_data, user_id=current_user.id).delete()
                    db.session.add(new_friend)
                    db.session.add(new_friend_requester)
                    db.session.add(create_dm)
                    db.session.commit()
                    user_status = "offline"
                    if(len(requester.active_sockets) > 0):
                        user_status = "online"
                    emit("friend-request-handler", {"msg" : "The friend was added!", "notification": request_data, "type" : request_status, "name" : request_name, "user status": user_status})
                    action = True
                    break
                else:
                    action = False # to make sure
                    break
            elif request_status == "Reject":
                    print("del")
                    notifications.query.filter_by(notification=request_data, user_id=current_user.id).delete()
                    db.session.commit()
                    action = True
                    emit("friend-request-handler", {"msg" : "Notification removed!", "notification": request_data})
                    break
    if action is False:
        emit("friend-request-handler", {"msg" : "Error", "notification": "None"})


@socketio.on('friends-dm')
def friends_dm(friend_username):
    exist = False
    for i in current_user.friends: # first I need to check if the username even exists, the client could inspect element.
        if i.friend_name == friend_username:
            exist = True
    if exist:
        dm_obj = friendsdms.query.filter_by(first_user=current_user.username, second_user=friend_username).first()
        if dm_obj == None: #could be that the requester is trying to access the dm
            dm_obj = friendsdms.query.filter_by(first_user=friend_username, second_user=current_user.username).first()
        if dm_obj != None:
            emit("friends-dm", dm_obj.room)
        else:
            emit("friends-dm", "error")  
    else:
        emit("friends-dm", "Friend not found")



@app.route("/validate", methods=["POST"])
def validate_room_password():
    print(request.get_data())
    room = request.get_data().decode()
    print(room)
    print("val " + room)
    if room != "Main":
        room_list = allRooms.query.all()
        password = ""
        for i in room_list:
            if i.rooms == room:
                password = i.room_password
        print(password)
        if password != "":
            return password
        else:
            return "False"
    else:
        return "False"

@socketio.on("dm-history")
def show_dm_history(friend_name):
    dm_obj =  friendsdms.query.filter_by(first_user = current_user.username, second_user=friend_name).first()
    if dm_obj is None:
        dm_obj =  friendsdms.query.filter_by(first_user = friend_name, second_user=current_user.username).first()
    if dm_obj is None:
        emit("dm-history", "the dm was not found in the db")
    else:
        chat_history = {}
        sent_user = []
        user_msg = []
        msg_time = []
        user_profile_pic =[]
        for i in dm_obj.history:
            user_msg.append(i.msg) 
            sent_user.append(i.msg_from_user)
            msg_time.append(i.msg_time)
            user_profile_pic.append(users.query.filter_by(username=i.msg_from_user).first().profile_picture)
        chat_history["user"] = sent_user
        chat_history["msg"] = user_msg
        chat_history["room"] = dm_obj.room
        chat_history["friend"] = friend_name
        chat_history["time"] = msg_time
        chat_history["profile picture"] = user_profile_pic
        emit("dm-history", chat_history)

@socketio.on('get-dm-data')
def get_dm_data(room):
    dm_obj = friendsdms.query.filter_by(room=room).first()
    if dm_obj is not None:
        print(request.sid) 
        now = datetime.datetime.now()
        date = now.strftime("%H:%M %d/%m/%Y") # no more seconds
        first_user = dm_obj.first_user
        second_user = dm_obj.second_user
        friend = ""
        first = False
        if first_user != current_user.username:
            friend = first_user
            first = True
        elif second_user != current_user.username:
            friend = second_user
        else:
            friend = "Error"
        print(friend)
        you = ""
        if first:
            you = second_user
        else:
            you = first_user
        friends_obj = friends.query.filter_by(friend_name=friend, user_friends=current_user).first() # should never be None
        friend_obj = users.query.filter_by(username=friend).first()
        you_friends_obj = friends.query.filter_by(friend_name=you, user_friends=friend_obj).first() # should never be None
        if friends_obj is not None and you_friends_obj is not None:
            print("not none")
            friends_obj.last_message_time = date
            you_friends_obj.last_message_time = date
            db.session.commit()
            last_friends_msg = friends_obj.last_text_message # doesn't matter which one
            print(last_friends_msg)
            emit("get-dm-data", {"date" : date, "friend" : friend, "you" : you, "last message" : last_friends_msg}, broadcast=True)
        else:
            print("None?")

@socketio.on("add-friend-requester-live") # adding the requester to the friend list live too.
def add_friend_requester_live(data):
    print("checking if user is online")
    user_obj = users.query.filter_by(username=data["requester"]).first()
    user_status = "offline"
    if len(user_obj.active_sockets) > 0:
        user_status = "online"
        for i in user_obj.active_sockets:
            emit("add-friend-requester-live",{"friend" : data["requester"], "accepted from" : data["accepted from"], "user status" : user_status},room=i.socket)

@socketio.on("send-notificaton-live")
def send_notificaton_live(data):
    print(data)
    user_obj = users.query.filter_by(username=data["receiver"]).first()
    user_status = "offline"
    if len(user_obj.active_sockets) > 0:
        user_status = "online"
        for i in user_obj.active_sockets:
            emit("send-notificaton-live",{"receiver" : data["receiver"], "sender" : data["sender"], "user status" : user_status},room=i.socket)

@socketio.on('user-typing')
def user_typing(data):
    emit("user-typing", {"typing" : data["typing"], "user" : data["user"]}, room=data["room"])

@socketio.on('update-profile-picture')
def profile_picture(data):
    picture_url = data["picture url"]
    current_user.profile_picture = picture_url
    db.session.commit()

@socketio.on('leave')
def on_leave(data):
    #username = data['username']
    now = datetime.datetime.now()
    date = now.strftime("%H:%M %d/%m/%Y")
    dm = "False"
    try:
        dm = data["dm"]
    except:
        pass
    room = data['room']
    leave_room(room)

    send({"msg" : current_user.username + ' has left the conversation', "server" : "yes", "time" : date} , room=room)
    
@socketio.on('disconnect')
def test_disconnect():
    socket = request.sid
    print("client dissconeted sid: " + socket)
    if socket is not None:
        activeSockets.query.filter_by(socket=socket).delete()
        db.session.commit()
        if(len(current_user.active_sockets) == 0):
            emit("user-offline", {"username" : current_user.username}, broadcast=True)
    print('Client disconnected')

@socketio.on('connect')
def test_disconnect():
    print(current_user.username)
    socket = request.sid
    if socket is not None:
        print("client connected sid: " + socket)
        if(len(current_user.active_sockets) == 0): # to check if even needed
            emit("user-online", {"username" : current_user.username}, broadcast=True)
        socket_obj = activeSockets(user_active_sockets=current_user, socket=socket)
        db.session.add(socket_obj)
        db.session.commit()
    print('Client connect')

if __name__ == "__main__":
    socketio.run(app, debug=True)