from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
import random
from string import ascii_uppercase
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "ashleyiscute"
socketio = SocketIO(app)

rooms = {}  # room_code: {members: int, messages: []}