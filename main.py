import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        room = request.form.get("room", "").strip()

        if not name or not room:
            return render_template("home.html", error="請輸入名字與房間號碼")

        session["name"] = name
        session["room"] = room
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    if "name" not in session or "room" not in session:
        return redirect(url_for("home"))
    return render_template("room.html", name=session["name"], room=session["room"])

@socketio.on("connect")
def on_connect():
    # 連線時不做事，等 join
    pass

@socketio.on("join")
def on_join(data):
    name = session.get("name")
    room = session.get("room")
    if not name or not room:
        return

    join_room(room)
    send({"name": "系統", "message": f"{name} 加入了房間"}, to=room)

@socketio.on("message")
def on_message(data):
    name = session.get("name")
    room = session.get("room")
    text = (data.get("text") or "").strip()

    if not name or not room or not text:
        return

    send({"name": name, "message": text}, to=room)

@socketio.on("disconnect")
def on_disconnect():
    name = session.get("name")
    room = session.get("room")
    if name and room:
        try:
            leave_room(room)
            send({"name": "系統", "message": f"{name} 離開了房間"}, to=room)
        except:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)