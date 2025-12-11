from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
from datetime import datetime
import random
from string import ascii_uppercase
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "ashleyiscute"
socketio = SocketIO(app, cors_allowed_origins="*")

# 房間資料庫：room_code -> {members, messages}
rooms = {}


# --------------------------
# 產生房間代碼
# --------------------------
def generate_room_code(length=4):
    return "".join(random.choice(ascii_uppercase) for _ in range(length))


# --------------------------
# 首頁（登入頁）
# --------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip().upper()
        action = request.form.get("action")

        if not name:
            return render_template("home.html", error="請輸入名字", name=name, code=code)

        # 加入房間
        if action == "join":
            if not code:
                return render_template("home.html", error="請輸入房間代碼", name=name, code=code)
            if code not in rooms:
                return render_template("home.html", error="房間不存在", name=name, code=code)

            room = code

        # 建立房間
        elif action == "create":
            room = generate_room_code()
            rooms[room] = {"members": 0, "messages": []}

        else:
            return render_template("home.html", error="不明操作", name=name, code=code)

        session["name"] = name
        session["room"] = room
        return redirect(url_for("room_page"))

    # GET → 顯示登入畫面
    return render_template("home.html", name="", code="", error=None)


# --------------------------
# 房間頁面
# --------------------------
@app.route("/room")
def room_page():
    room = session.get("room")
    name = session.get("name")

    if room not in rooms or not name:
        return redirect(url_for("home"))

    return render_template("room.html", room=room, name=name, messages=rooms[room]["messages"])


# --------------------------
# SocketIO：連線
# --------------------------
@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return

    join_room(room)
    rooms[room]["members"] += 1

    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    msg = {
        "name": name,
        "text": f"{name} has entered the room",
        "time": timestamp
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


# --------------------------
# SocketIO：接收訊息
# --------------------------
@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    name = session.get("name")

    text = data["text"]
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    msg = {
        "name": name,
        "text": text,
        "time": timestamp
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)


# --------------------------
# SocketIO：離線
# --------------------------
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if room in rooms:
        leave_room(room)
        rooms[room]["members"] -= 1

        if rooms[room]["members"] <= 0:
            del rooms[room]


# --------------------------
# Render 專用啟動（很重要!!!）
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)