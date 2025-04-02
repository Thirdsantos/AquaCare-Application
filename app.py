from flask import Flask
from flask_socketio import SocketIO
import firebase_admin
from firebase_admin import credentials, db


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  


if not firebase_admin._apps:
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://aquamans-47d16-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })
    print("Firebase Connected Successfully!")

ref = db.reference("Sensors") 

@socketio.on("connect")
def connection():
    print(" A Client is Connected!")
    socketio.emit("Message", "You're now connected")

@socketio.on("disconnect")
def disconnection():
    print(" A Client is Disconnected!")

@socketio.on("message")
def handle_message(msg):
    print(f"Received message: {msg}")
    socketio.send(f"Server received: {msg}")




def update_db(data):
    key = data.keys()
    keyList = list(key)[0]
    values = data[keyList]
    return values

@socketio.on("sensors")
def handle_sensors(data):
    ref.update(data)  
    print("Successfully updated Firebase")




if __name__ == "__main__":
    print("WebSocket Server is Running...")
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
