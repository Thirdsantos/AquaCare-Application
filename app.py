import eventlet
eventlet.monkey_patch()

import os
import json
from flask import Flask, request
from flask_socketio import SocketIO
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Firebase Setup
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
    print("Error: GOOGLE_APPLICATION_CREDENTIALS_JSON not found.")
    exit()

# Firebase References
refPh = db.reference("Notification/PH")
refTemp = db.reference("Notification/Temperature")
refTurb = db.reference("Notification/Turbidity")
ref = db.reference("Sensors")
refNotif = db.reference("Notifications")

@app.route("/")
def index():
    return "AQUACARE THE BRIDGE BETWEEN THE GAPS"

# WebSocket route for ESP32
@app.route("/ws")
def websocket_esp32():
    if request.environ.get("wsgi.websocket"):
        ws = request.environ["wsgi.websocket"]
        print("ESP32 connected via raw WebSocket")
        while True:
            msg = ws.receive()
            if msg:
                try:
                    data = json.loads(msg)
                    print("Received from ESP32:", data)
                    updateToDb(data)
                    checkTreshHold(data)
                except Exception as e:
                    print("Invalid format or error from ESP32:", e)
            else:
                print("ESP32 disconnected")
                break
    return

# Socket.IO Events for Flutter
@socketio.on("connect")
def connection():
    print("A Client is Connected (Flutter)")
    socketio.emit("Message", "You're now connected")

@socketio.on("disconnect")
def disconnection():
    print("A Client is Disconnected (Flutter)")

@socketio.on("message")
def handle_message(message):
    print(message)
    socketio.emit("Message", "Hello. Testing if connected kana")

@socketio.on("sensors")
def handle_sensors(data):
    try:
        if isinstance(data, dict) and "PH" in data and "Temperature" in data and "Turbidity" in data:
            print(f"Received data from Flutter: {data}")
            updateToDb(data)
            checkTreshHold(data)
        else:
            socketio.emit('sensor_response', 'Invalid data format')
    except Exception as e:
        print(f"Error updating Firebase: {e}")
        socketio.emit('sensor_response', 'Failed to update data')

# Firebase Update
def updateToDb(data):
    ref.update(data)
    print("Successfully updated Firebase")

# Threshold Check
def checkTreshHold(data):
    ph_value = refPh.get()
    temp_value = refTemp.get()
    turb_value = refTurb.get()

    phValue = data["PH"]
    temperatureValue = data["Temperature"]
    turbidityValue = data["Turbidity"]

    if ph_value["Min"] != 0 and ph_value["Max"] != 0:
        if ph_value["Min"] > phValue or ph_value["Max"] < phValue:
            socketio.emit('PHNotif', {"alert": "PH value is out of range!"})

    if temp_value["Min"] != 0 and temp_value["Max"] != 0:
        if temp_value["Min"] > temperatureValue or temp_value["Max"] < temperatureValue:
            socketio.emit('TemperatureNotif', {"alert": "Temperature value is out of range!"})

    if turb_value["Min"] != 0 and turb_value["Max"] != 0:
        if turb_value["Min"] > turbidityValue or turb_value["Max"] < turbidityValue:
            socketio.emit('TurbidityNotif', {"alert": "Turbidity value is out of range!"})

# Run WebSocket + SocketIO server
if __name__ == "__main__":
    print("Starting AquaCare Server with WebSocket (ESP32) + Socket.IO (Flutter)...")
    # Use pywsgi to serve both WebSocket and HTTP
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
