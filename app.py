from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room, leave_room, emit
app = Flask(__name__)
app.config['SECRET_KEY'] = 'topsecret'
socketio = SocketIO(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///foo1.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
public_rooms = ["Vanila", "Chocolate"]
class AllHistory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    message = db.Column(db.TEXT)

@app.route("/", methods=["GET"])
def index():
    all_msg = AllHistory.query.all()
    return render_template("index.html", msgs="", rooms=public_rooms)

@socketio.on('message')
def handle_message(message):
    #new_msg = AllHistory(message=message)
    #db.session.add(new_msg)
    #db.session.commit()
    try:
        room=message["room"]
        send("From room " + room + " Message: " + message["message"], room=room)
    except:
        print(type(message))
        send("All: " + message, broadcast=True)

@socketio.on('message', namespace="/room")
def handle_message(data):
    if data == "Connected!":
        send(data)
    else:
        print('received message room: ' + data["message"] + " from room " + data["room"])
        send(data["message"], room=data["room"])

@socketio.on('join')
def on_join(data):
    #username = data['username']
    room = data['room']
    print("join " + room)
    join_room(room)
    send('has entered ' + room, room=room)

@socketio.on('leave')
def on_leave(data):
    #username = data['username']
    room = data['room']
    leave_room(room)
    print("leave " + room)
    send('has left has entered ' + room, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)