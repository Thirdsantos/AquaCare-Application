
import eventlet
eventlet.monkey_patch()

import os
import json
from flask import Flask
from flask_socketio import SocketIO
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


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


@app.route("/")
def index():
    return "AQUACARE THE BRIDGE BETWEEN THE GAPS"

@socketio.on("connect")
def connection():
    print("A Client is Connected!")
    socketio.emit("Message", "You're now connected")


@socketio.on("disconnect")
def disconnection():
    print("A Client is Disconnected!")

def updateToDb(data):
    
                
            ref.update(data)  
            print("Successfully updated Firebase")
       


def checkTreshHold(data):
    refPh = db.reference("Notification/PH")
    refTemp = db.reference("Notification/Temperature")
    refTurb = db.reference("Notification/Turbidity")
    

    ph_value = refPh.get()
    temp_value = refTemp.get()
    turb_value = refTurb.get()

    phValue = data["PH"]
    temperatureValue = data["Temperature"]
    turbidityValue = data["Turbidity"]


    if ph_value["Min"] > phValue or ph_value["Max"] < phValue:
        socketio.emit('PHNotif', {"alert": "PH value is out of range!"})
    
    if temp_value["Min"] > temperatureValue or temp_value["Max"] < temperatureValue:
        socketio.emit('TemperatureNotif', {"alert": "Temperature value is out of range!"})
    
    if turb_value["Min"] > turbidityValue or turb_value["Max"] < turbidityValue:
        socketio.emit('TurbidityNotif', {"alert": "Turbidity value is out of range!"})
        


refNotif = db.reference("Notifications")

@socketio.on("sensors")
def handle_sensors(data):
    try:
        if isinstance(data, dict):
            if "PH" in data and "Temperature" in data and "Turbidity" in data:
                print(f"Received data: {data}")
                updateToDb(data)
                checkTreshHold(data)

            else:
                print("Error: Missing 'PH' or 'Temperature' data or 'Turbidity' data")
                socketio.emit('sensor_response', 'Invalid data format')
        else:
            print("Error: Data is not in the correct format")
            socketio.emit('sensor_response', 'Invalid data format')
        



        
    except Exception as e:
        print(f"Error updating Firebase: {e}")
        socketio.emit('sensor_response', 'Failed to update data')


if __name__ == "__main__":
    print("WebSocket Server is Running...")
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)