from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, join_room, leave_room, send
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "pixelchatsecret"
socketio = SocketIO(app)

rooms = {}  # room_code: { "messages": [] }

avatars = ["⭐", "💖", "🌙", "💫", "✨", "🌟"]

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        room = request.form.get("room")

        if not name or not room:
            return render_template("home.html", error="Enter name & room code!")

        if room not in rooms:
            return render_template("home.html", error="Room does not exist.")

        return redirect(f"/room?name={name}&room={room}")

    return render_template("home.html")


@app.route("/create", methods=["POST"])
def create():
    name = request.form.get("name")
    room = str(random.randint(1000, 9999))

    rooms[room] = {"messages": []}

    return redirect(f"/room?name={name}&room={room}")


@app.route("/room")
def room():
    name = request.args.get("name")
    room = request.args.get("room")

    if room not in rooms:
        return "Room does not exist."

    return render_template(
        "room.html",
        user=name,
        room=room,
        messages=rooms[room]["messages"],
    )


@socketio.on("join")
def handle_join(data):
    name = data["name"]
    room = data["room"]

    join_room(room)

    avatar = random.choice(avatars)

    rooms[room]["messages"].append({"user": name, "avatar": avatar, "text": "joined the room"})

    send({"user": name, "avatar": avatar, "text": "joined the room"}, to=room)


@socketio.on("message")
def handle_message(data):
    room = data["room"]
    rooms[room]["messages"].append(data)
    
    send(data, to=room)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)