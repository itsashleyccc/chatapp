from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import os
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"

# 重要：Render 上跑 SocketIO 建議加 async_mode=eventlet
socketio = SocketIO(app, async_mode="eventlet")

rooms = {}

def generate_unique_code(length=4):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

@app.route("/", methods=["GET", "POST"])
def home():
    # 只在 GET 清 session，避免你按 Create/Join 後 session 被清掉
    if request.method == "GET":
        session.clear()
        return render_template("home.html")

    # POST 才會到這裡
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()

    join_clicked = request.form.get("join")  # 有按 join 才會有值
    create_clicked = request.form.get("create")

    if not name:
        return render_template("home.html", error="請輸入名字。", code=code, name=name)

    # 按 Join 但沒輸入房間代碼
    if join_clicked and not code:
        return render_template("home.html", error="請輸入房間代碼。", code=code, name=name)

    room = code

    # 按 Create：直接建立新房間
    if create_clicked:
        room = generate_unique_code(4)
        rooms[room] = {"members": 0, "messages": []}

    # 按 Join：房間必須存在
    elif join_clicked:
        if room not in rooms:
            return render_template("home.html", error="房間不存在。", code=code, name=name)

    # 理論上不會發生，但保險：沒按 join 也沒按 create
    else:
        return render_template("home.html", error="請按「加入」或「建立新房間」。", code=code, name=name)

    session["room"] = room
    session["name"] = name
    return redirect(url_for("room"))

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")

    if not room or not name or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if not room or room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data.get("data", "")
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name or room not in rooms:
        return

    join_room(room)
    rooms[room]["members"] += 1
    send({"name": name, "message": "已加入房間"}, to=room)

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if room:
        leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    if room and name:
        send({"name": name, "message": "已離開房間"}, to=room)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)