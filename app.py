from flask import Flask, render_template, url_for,request,redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import func
from hashlib import md5
import datetime
import secrets
app = Flask(__name__)
app.config['SECRET_KEY'] = 'topsecret'
socketio = SocketIO(app,cors_allowed_origins=['http://chat-py.herokuapp.com', 'http://127.0.0.1:5000'])
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://vzhrgnqdyaziyw:6bdbaf5bcd402e3921a8c3692924fafb5afc00f3ad065cca78894629c611f411@ec2-54-75-246-118.eu-west-1.compute.amazonaws.com:5432/d9lulko2sfvhhu"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
server_rooms = ["Main", "Vanila", "Chocolate"] # need to be inside the db

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.TEXT)
    password = db.Column(db.TEXT)
    email = db.Column(db.TEXT)
    notifications = db.relationship('notifications', backref='user_notification')
    friends = db.relationship('friends', backref='user_friends')


class notifications(db.Model): # maybe add a filter option (friend, server notification etc')
    id = db.Column(db.Integer, primary_key = True)
    notification = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 


class friends(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    friend_name = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 

class all_rooms(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    room_messages = db.Column(db.TEXT) # create one to many relationship to present the messages
    rooms = db.Column(db.TEXT) # change name to room
    room_password = db.Column(db.TEXT)
    room_owner = db.Column(db.TEXT)

class friends_dms(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_user = db.Column(db.TEXT)
    second_user = db.Column(db.TEXT)
    room = db.Column(db.TEXT)
    history = db.relationship('dm_history', backref='users_dms')

class dm_history(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    msg = db.Column(db.TEXT)
    msg_from_user = db.Column(db.TEXT)
    friends_dm_id = db.Column(db.Integer, db.ForeignKey('friends_dms.id')) 

@app.route("/", methods=["GET"])
@login_required
def index():
    print("index")
    rooms = all_rooms.query.all()
    notifi = []
    user_friends = []
    public_rooms = []
    private_rooms = []
    for i in current_user.notifications:
        notifi.append(i.notification)
    for i in current_user.friends:
        user_friends.append(i.friend_name)
    total_rooms = ["Main", "Vanila", "Chocolate"]
    for i in rooms:
        total_rooms.append(i.rooms)
        if i.room_password == "":
            public_rooms.append(i.rooms)
        else:
            private_rooms.append(i.rooms)
    print(server_rooms)
    return render_template("index.html", msgs="", all_rooms=total_rooms,server_rooms= server_rooms,private_rooms=private_rooms,public_rooms=public_rooms ,notifications=notifi, user_friends=user_friends)

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
        pass_check = bool(users.query.filter_by(password=password).first())
        if user_check and not pass_check:
            return "password"
        elif not user_check:
            return "username"
        else:
            user = users.query.filter_by(username=username,password=password).first()
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
        
        if (email_check) and ("@gmail.com" not in email) and user_check:
            print("all")
            return "all"
        elif user_check and ("@gmail.com" not in email):
            print("u e c")
            return "username exist email contain"
        elif user_check and email_check:
            print("u e e")
            return "username exist email exist"
        elif email_check:
            return "email exist"
        elif "@gmail.com" not in email:
            return "email contain"
        elif user_check:
            return "username exist"
        else:
            new_user = users(username = username, password=password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect('/')
        else:
            return render_template('/register.html')


@socketio.on('message')
def handle_message(message):
    #new_msg = AllHistory(message=message)
    #db.session.add(new_msg)
    #db.session.commit()
    try:
        print("In room")
        room=message["room"]
        print(message["room"])
        friend_obj = friends_dms.query.filter_by(room=room).first()
        print(friend_obj) # should be none if it doesn't find it
        if friend_obj != None:
           new_dm = dm_history(msg=message["message"], msg_from_user=current_user.username, users_dms=friend_obj)
           db.session.add(new_dm)
           db.session.commit()
        send({"msg" : message["message"], "user" : current_user.username}, room=room)
    except:
        print(type(message)) # server message
        if message == "Connected!":
            send(current_user.username +" Has " + message)

@socketio.on('message', namespace="/room")
def handle_message(data):
    if data == "Connected!":
        send(current_user.username +" Has " + data)
    else:
        print('received message room: ' + data["message"] + " from room " + data["room"])
        send(data["message"], room=data["room"])

@socketio.on('add') # Todo: need to check if the rooms has a password or not.
def add(data):
    print("adding")
    room_name = data["name"]
    if room_name.lower() == "main":
        room_exist = True
    rooms_obj = all_rooms.query.all()
    room_exist = False
    for i in rooms_obj:
        if i.rooms.lower() == room_name.lower():
            room_exist = True
    if room_exist is False:
        print("adding a room")
        owner = current_user.username
        room_password = data["room password"] # None for now
        print(room_password)
        password_is_dm = False
        for i in friends_dms.query.all():
            if room_password == i.room:
                password_is_dm = True
        if not password_is_dm:
            add_new_room = all_rooms(rooms= room_name, room_password=room_password, room_owner= owner)
            db.session.add(add_new_room)
            db.session.commit()
            emit("add", room_name) # send if the room is private or not
        else:
            emit("add", "an unexpected error has occurred, please choose a different password") # send if the room is private or not
    else:
        emit("add", "Room already exists")

@socketio.on('join')
def on_join(data):
    #username = data['username']
    room = data['room']
    dm = "False"
    try:
        dm = data["dm"]
    except:
        pass
    print("join " + room)
    join_room(room)
    if dm == "True":
        send(current_user.username +' has entered the dm', room=room)
    else:
        send(current_user.username +' has entered ' + room, room=room)

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
                user = users.query.filter_by(username=friend_username).first()
                notification_msg = current_user.username + " Has added you as a friend!"
                for j in user.notifications:
                    if j.notification == notification_msg:
                        sent = True
                if not sent:
                    notifi = notifications(notification=notification_msg, user_notification=user)
                    db.session.add(notifi)
                    db.session.commit()
                    emit("friend-add", "Friend request sent!")
                else:
                    emit("friend-add", "You have already sent the friend request")
    if not found:
        emit("friend-add", "The user does not exist.")

@socketio.on('friend-request-handler')
def friend_request_handler(data):
    request_status = data["type"]
    request_data = data["notification"]
    print(request_status)
    action = False
    for i in current_user.notifications:
        if i.notification == request_data:
            if request_status == "Accept":
                request_name = request_data.split(' ')[0]
                requester = users.query.filter_by(username=request_name).first()
                new_friend_requester = friends(friend_name=current_user.username, user_friends=requester)
                new_friend = friends(friend_name=request_name, user_friends=current_user)
                hash_salt = secrets.token_hex(6) # bascily creates 6 random chars and combines them to a string
                room_hash = md5(str(current_user.username + requester.username + str(datetime.datetime.now()) + hash_salt).encode('utf-8')).hexdigest() # hashing MD5 with salt 
                print(room_hash)
                create_dm = friends_dms(first_user=current_user.username, second_user=requester.username,room=room_hash)
                notifications.query.filter_by(notification=request_data, user_id=current_user.id).delete()
                db.session.add(new_friend)
                db.session.add(new_friend_requester)
                db.session.add(create_dm)
                db.session.commit()
                emit("friend-request-handler", {"msg" : "The friend was added!", "notification": request_data, "type" : request_status, "name" : request_name})
                action = True
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
        dm_obj = friends_dms.query.filter_by(first_user=current_user.username, second_user=friend_username).first()
        if dm_obj == None: #could be that the requester is trying to access the dm
            dm_obj = friends_dms.query.filter_by(first_user=friend_username, second_user=current_user.username).first()
        if dm_obj != None:
            emit("friends-dm", dm_obj.room)
        else:
            emit("friends-dm", "error") # problem, shouldn't happen because I am check if the friend exist before hand.
    else:
        emit("friends-dm", "Friend not found")



@app.route("/validate", methods=["POST"])
def validate_room_password():
    print(request.get_data())
    room = request.get_data().decode()
    print(room)
    print("val " + room)
    if room != "Main":
        room_list = all_rooms.query.all()
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
    dm_obj =  friends_dms.query.filter_by(first_user = current_user.username, second_user=friend_name).first()
    if dm_obj is None:
        dm_obj =  friends_dms.query.filter_by(first_user = friend_name, second_user=current_user.username).first()
    if dm_obj is None:
        emit("dm-history", "the dm was not found in the db")
    else:
        chat_history = {}
        sent_user = []
        user_msg = []
        for i in dm_obj.history:
            user_msg.append(i.msg) 
            sent_user.append(i.msg_from_user)
        chat_history["user"] = sent_user
        chat_history["msg"] = user_msg
        emit("dm-history", chat_history)

@socketio.on('leave')
def on_leave(data):
    #username = data['username']
    dm = "False"
    try:
        dm = data["dm"]
    except:
        pass
    room = data['room']
    leave_room(room)
    if dm == "True":
        send(current_user.username +' has left the dm', room=room)
    else:
        send(current_user.username + ' has left ' + room, room=room)
    send('has left has entered ' + room, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)