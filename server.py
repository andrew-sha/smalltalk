from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.secret_key = 'secret!'
socketio = SocketIO(app, secret_key='secret!')

active_rooms = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/chat/<room>')
def chat(room):
    username = request.cookies.get('username', 'Guest')
    user_list = active_rooms[room]
    return render_template('chat.html', room=room, username=username, user_list=user_list)

# To render list of actives room on the home page
@socketio.on('connect')
def send_active_rooms():
    active_room_names = list(active_rooms.keys())
    emit('send_active_rooms', active_room_names)

@socketio.on('attempt_join')
def handle_join_attempt(data):
    room = data['room']
    username = data['username']
    new_room = data['new_room']

    if not new_room:
        if username in active_rooms[room]:
            emit('duplicate_username', {'username': username, 'room': room})
        else:
            active_rooms[room].append(username)
            emit('succesful_join', {'username': username, 'room': room})
    else:
        if room in active_rooms:
            emit('duplicate_room_name', {'username': username, 'room': room})
        else:
            active_rooms[room] = [username]
            emit('succesful_join', {'username': username, 'room': room})


@socketio.on('join_socket_room')
def join_socket_room(data):
    room = data['room']
    username = data['username']
    join_room(room)
    emit('broadcast_user_info', {'username': username, 'dir': 'joined'}, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    username = data['username']
    message = data['message']

    emit('update_chat', {'username': username, 'message': message}, to=room)

@socketio.on('leave_room')
def handle_leave_room(data):
    room = data['room']
    username = data['username']
    
    leave_room(room)
    active_rooms[room].remove(username)

    emit('broadcast_user_info', {'username': username, 'dir': 'left'}, to=room)

    # Automatically delete room with no active users
    if len(active_rooms[room]) == 0:
        del active_rooms[room]


if __name__ == '__main__':
    socketio.run(app, debug=True)