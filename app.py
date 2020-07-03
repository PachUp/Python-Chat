from flask import Flask, render_template, url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import func
app = Flask(__name__)
app.config['SECRET_KEY'] = 'topsecret'
socketio = SocketIO(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db3.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
public_rooms = ["Vanila", "Chocolate", "Main"] # need to be inside the db

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.TEXT)
    password = db.Column(db.TEXT)
    email = db.Column(db.TEXT)

class all_rooms(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    room_messages = db.Column(db.TEXT) # create one to many relationship to present the messages
    rooms = db.Column(db.TEXT) # change name to room
    room_password = db.Column(db.TEXT)
    room_owner = db.Column(db.TEXT)

@app.route("/", methods=["GET"])
@login_required
def index():

    return render_template("index.html", msgs="", rooms=public_rooms)

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
        send({"msg" : message["message"], "user" : current_user.username}, room=room)
    except:
        print(type(message))
        if message == "Connected!":
            send(current_user.username +" Has " + message)

@socketio.on('message', namespace="/room")
def handle_message(data):
    if data == "Connected!":
        send(current_user.username +" Has " + data)
    else:
        print('received message room: ' + data["message"] + " from room " + data["room"])
        send(data["message"], room=data["room"])

@socketio.on('add')
def add(data):
    room_name = data["name"]
    rooms_obj = all_rooms.query.all()
    room_exist = False
    for i in rooms_obj:
        if i.room_name == room_name:
            room_exist = True
    if room_exist is False:
        owner = current_user.username
        room_password = data["password"] # None for now
        add_new_room = all_rooms(rooms= room_name, room_password= room_password, owner= owner)
        db.session.add(add_new_room)
        db.session.commit()

@socketio.on('join')
def on_join(data):
    #username = data['username']
    room = data['room']
    print("join " + room)
    join_room(room)
    send(current_user.username +' has entered ' + room, room=room)

@socketio.on('leave')
def on_leave(data):
    #username = data['username']
    room = data['room']
    leave_room(room)
    print("leave " + room)
    send('has left has entered ' + room, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)