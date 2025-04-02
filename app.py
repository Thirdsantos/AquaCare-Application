import os
import json
from flask import Flask
from flask_socketio import SocketIO
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


firebase_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if firebase_credentials:
    creds = json.loads(firebase_credentials)
    if not firebase_admin._apps:
        cred = credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://aquamans-47d16-default-rtdb.asia-southeast1.firebasedatabase.app/"
        })
        print("Firebase Connected Successfully!")
else:
    print("Error: GOOGLE_APPLICATION_CREDENTIALS_JSON not found in environment variables.")
    exit()

ref = db.reference("Sensors")

@socketio.on("connect")
def connection():
    print("A Client is Connected!")
    socketio.emit("Message", "You're now connected")

@socketio.on("disconnect")
def disconnection():
    print("A Client is Disconnected!")

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
