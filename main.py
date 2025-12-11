from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
import random
from string import ascii_uppercase
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
socketio = SocketIO(app)

rooms = {}

def generate_code(length=4):
    code = ""
    for i in range(length):
        code += random.choice(ascii_uppercase)
    return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()

    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")

        if not name:
            return render_template("home.html", error="請輸入名字")

        # Create room
        if create:
            room = generate_code()
            rooms[room] = {"members": 0, "messages": []}
            session["room"] = room
            session["name"] = name
            return redirect(url_for("room"))

        # Join room
        if join:
            if code not in rooms:
                return render_template("home.html", error="房間不存在", name=name)
            session["room"] = code
            session["name"] = name
            return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")

    if room not in rooms or not name:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get("name")

    time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    msg = {"name": name, "message": data["message"], "avatar": data["avatar"], "time": time}
    rooms[room]["messages"].append(msg)

    send(msg, to=room)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    join_room(room)
    rooms[room]["members"] += 1

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)