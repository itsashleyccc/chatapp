@socketio.on("message")
def message(data):
    room = data["room"]
    name = data["name"]
    text = data["text"]
    avatar = data["avatar"]

    timestamp = datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")

    msg = {
        "name": name,
        "text": text,
        "avatar": avatar,
        "time": timestamp
    }

    rooms[room]["messages"].append(msg)
    socketio.emit("message", msg, to=room)