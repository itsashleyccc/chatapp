from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
from string import ascii_uppercase
import random
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "ashleyiscute"
socketio = SocketIO(app)

rooms = {}  # { room_code: { members: int, messages: [] } }


# 房間代碼
def generate_room_code(length=4):
    return "".join(random.choice(ascii_uppercase) for _ in range(length))


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip().upper()
        action = request.form.get("action")

        if not name:
            return render_template("home.html", error="請輸入名字")

        # 加入房間
        if action == "join":
            if not code:
                return render_template("home.html",
                                       error="請輸入房間代碼",
                                       name=name)
            if code not in rooms:
                return render_template("home.html",
                                       error="房間不存在",
                                       name=name)
            room = code

        # 建立新房間
        elif action == "create":
            room = generate_room_code()
            rooms[room] = {"members": 0, "messages": []}

        session["name"] = name
        session["room"] = room

        return redirect(url_for("room_page"))

    return render_template("home.html")


@app.route("/room")
def room_page():
    room = session.get("room")
    name = session.get("name")

    if not room or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html",
                           room=room,
                           name=name,
                           messages=rooms[room]["messages"])


# -------- SocketIO --------
@socketio.on("join")
def on_join(data):
    room = data["room"]
    name = data["name"]

    join_room(room)
    rooms[room]["members"] += 1

    msg = {
        "avatar": "✨",
        "name": name,
        "text": f"{name} 進入了聊天室",
        "time": datetime.now().strftime("%H:%M")
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


@socketio.on("message")
def handle_message(data):
    room = data["room"]
    text = data["text"]
    name = data["name"]

    avatar = random.choice(["✨","🌙","🌸","⭐","☁️","💖"])

    msg = {
        "avatar": avatar,
        "name": name,
        "text": text,
        "time": datetime.now().strftime("%H:%M")
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


@socketio.on("disconnect")
def on_disconnect():
    room = session.get("room")
    name = session.get("name")

    if not room:
        return

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)