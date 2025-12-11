from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
import random
from string import ascii_uppercase
import os   # ←←← VERY IMPORTANT

app = Flask(__name__)
app.config["SECRET_KEY"] = "ashleyiscute"
socketio = SocketIO(app)

rooms = {}  # room_code: {members: int, messages: []}

# ----------------------
# Helper：產生房間代碼
# ----------------------
def generate_room_code(length=4):
    return "".join(random.choice(ascii_uppercase) for _ in range(length))


# ----------------------
# Home Page
# ----------------------
@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()

    if request.method == "POST":
        name = request.form.get("name")
        room = request.form.get("room")
        action = request.form.get("action")

        if not name:
            return render_template("home.html", error="請輸入名字！")

        session["name"] = name

        # ➤ 使用者要加入房間
        if action == "join":
            if room not in rooms:
                return render_template("home.html", error="房間不存在！")
            session["room"] = room
            return redirect(url_for("room_page"))

        # ➤ 使用者要創建房間
        elif action == "create":
            room = generate_room_code()
            rooms[room] = {"members": 0, "messages": []}
            session["room"] = room
            return redirect(url_for("room_page"))

    return render_template("home.html")


# ----------------------
# 房間頁面
# ----------------------
@app.route("/room")
def room_page():
    room = session.get("room")
    name = session.get("name")

    if room not in rooms or not name:
        return redirect(url_for("home"))

    return render_template("room.html",
                           room=room,
                           messages=rooms[room]["messages"])


# ----------------------
# SocketIO 事件
# ----------------------
@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    join_room(room)
    rooms[room]["members"] += 1

    timestamp = datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")
    msg = {"avatar": "💖", "text": f"{name} has entered the room", "time": timestamp}

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get("name")

    timestamp = datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")

    msg = {
        "avatar": "⭐",   # 隨機頭貼可改
        "text": f"{name}: {data['text']}",
        "time": timestamp
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]


# ----------------------
# REALLY IMPORTANT: Render 要這段才能啟動
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)