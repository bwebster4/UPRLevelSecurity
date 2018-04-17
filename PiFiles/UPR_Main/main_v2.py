import cv2
import sys
import serial
import os
from flask import Flask, render_template, Response, jsonify, request
from camera_v2 import VideoCamera
import time
from datetime import datetime
import threading
from PersonAlert import sendAlert, upload_video
from gnssRun import serial_ports
import config

remoteControl = False

config.receivedData = False

arduino_port = None
gps_port = None

alert_update_interval = 15 # sends an email only once in this time interval
video_camera = None
object_classifier = cv2.CascadeClassifier("models/facial_recognition_model.xml") # an opencv classifier
frame_interval = 100 #reads frame once per interval

filename = 'Patrol'

# App Globals (do not edit)
app = Flask(__name__)
last_epoch = 0
last_epoch_frame = 0
currently_found_object = False;


def manageThreads():
    global remoteControl
    
    global video_camera
    global arduino_port
    global gps_port

    video_camera = VideoCamera(flip=False) # creates a camera object, flip vertically
    
    arduino_port, gps_port = serial_ports()
    
    personDetectionThread = threading.Thread(target=check_for_objects, args=())
    personDetectionThread.daemon = True #this should be True
    config.personDetectionFlag = True
    
    personDetectionThread.start()
    
    from autonomousNav import startAutonomousNavigation
    autonomousThread = threading.Thread(target=startAutonomousNavigation, args=[gps_port, arduino_port])
    autonomousThread.daemon = True
    config.autonomousFlag = True
    
##    if gps_port is not None:
##        autonomousThread.start()
    autonomousThread.start()

    gaugeDetectionThread = threading.Thread(target = gauge_detection, args=())
    gaugeDetectionThread.daemon = True
    config.gaugeDetectionFlag = False
    
    gaugeDetectionThread.start()
    
    remoteControlDataFlag = False
    while True:
        if remoteControl:
            config.personDetectionFlag = False
            config.autonomousFlag = False
            config.gaugeDetectionFlag = False
            config.receivedData = False
            if not remoteControlDataFlag:
                with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:
                    if ser.isOpen():
                        while 1:
                            if not config.receivedData:                           
                                serialString = '{},{},{},{},{}'.format('0', '0', '0', '1', '0')
                                ser.write(serialString.encode('utf-8'))
                                try:
                                    readValue = ser.readline().decode('utf-8')
                                except Exception as e:
                                    print(str(e))
                                print('Not received print, ' + readValue)
                                if serialString in readValue:
                                    ser.write('Proceed'.encode('utf-8'))
                                    print('Pi sent proceed')
                                    config.receivedData = True
                            else:
                                try:
                                    dummyRead = ser.readline()
                                    readValue = ser.readline().decode('utf-8')
                                    print('Received Print, ' + readValue)
                                except Exception as e:
                                    print(str(e))
                                if 'Proceed' in readValue:
                                    config.receivedData = False
                                    break
                                else:
                                    config.receivedData = False
                        print('we should be in remote control')
            remoteControlDataFlag = True
        elif config.atGauge:
            config.personDetectionFlag = False
            config.autonomousFlag = False
            config.gaugeDetectionFlag = True
            remoteControlDataFlag = False
        else:
            config.personDetectionFlag = False #this should be True
            config.autonomousFlag = False
            config.gaugeDetectionFlag = True
            remoteControlDataFlag = False
        print('person: {} auto: {} gauge: {}'.format(config.personDetectionFlag, config.autonomousFlag, config.gaugeDetectionFlag))
        time.sleep(1)
    
def setAtGauge(flag):
##    global video_camera
    config.atGauge = flag

def check_for_objects():
    global last_epoch
    global last_epoch_frame
    global currently_found_object
    global video_camera

    filename = 'Patrol_' + datetime.now().isoformat() + '.h264'
    video_camera.start_recording(filename)
	
    while True:
        try:
            if not config.personDetectionFlag:
                time.sleep(1)
                continue
            
            last_epoch_frame = time.time()
            frame, found_obj, objs = video_camera.HOG_Person_Detector()
            
            if not found_obj:
                currently_found_object = False
                
            if found_obj and not currently_found_object and (time.time() - last_epoch) > alert_update_interval:
                    last_epoch = time.time()
                    print("person detected")
                    old_filename = video_camera.filename
                    video_camera.stop_recording()
                    new_filename = 'Patrol_' + datetime.now().isoformat() + '.h264'
                    video_camera.start_recording(new_filename)
                    
                    video_id = upload_video(old_filename)
                    title = "Human Detected"
                    text = "Human intruder detected at substation."           
                    sendAlert(title, text, video_id)
                    os.remove(old_filename)
                    currently_found_object = True
                    
                    isTracking = video_camera.Tracker(objs, arduino_port, video_camera.HOG_Person_Detector)
                    if not isTracking:
                        found_obj == False
                    print ("alert upload completed!")
                    
        except Exception as e:
            print(str(e))
          
def gauge_detection():
    global video_camera
    hasSent = False
    while True:
        if not config.gaugeDetectionFlag:
            time.sleep(1)
            continue
        frame, found_obj, objs = video_camera.GaugeDetector()
        
       
        with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser: 
            if not hasSent:
                if ser.isOpen():
                    if config.atGauge:
                        ser_atGauge = '1'
                    else:
                        ser_atGauge = '0'
                        
                    if remoteControl:
                        ser_rc = '1'
                    else:
                        ser_rc = '0'
                    
                    while 1:
                        if not config.receivedData:
                            try:
                                print('Should have sent data from pi to arduino')
                                time.sleep(0.5)
                                serialString = '{},{},{},{},{}'.format(1, 0, 0, ser_rc, 0) #ser_atGauge
                                ser.write(serialString.encode('utf-8'))
                                time.sleep(0.5)
                                readValue = ser.readline().decode('utf-8')
                                print('At Gauge, not received print, ' + readValue)
                                if serialString == readValue.strip():
                                    ser.write('Proceed'.encode('utf-8'))
                                    print('Pi sent proceed')
                                    config.receivedData = True
                            except Exception as e:
                                print(str(e))
                        else:
                            try:
                                dummyRead = ser.readline()
                                readValue = ser.readline().decode('utf-8')
                                print('At Gauge, received Print, ' + readValue)
                            except Exception as e:
                                print(str(e))
                            if 'Proceed' in readValue:
                                hasSent = True
                                config.receivedData = False
                                break
                            else:
                                config.receivedData = False

        if found_obj:          
            video_id = -1
            title = "Gauge Detected"
            text = "Gauge has been detected at destination."
            sendAlert(title, text, video_id)
            print ("Detection")
            isTracking = video_camera.Tracker(objs, arduino_port, video_camera.GaugeDetector)            
            if not isTracking:
                found_obj = False
        else:
            with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:
                if ser.isOpen():
                    while 1:
                        if not config.receivedData:                           
                            serialString = '9'
                            ser.write(serialString.encode('utf-8'))
                            time.sleep(0.5)
                            try:
                                readValue = ser.readline().decode('utf-8')
                            except Exception as e:
                                print(str(e))
                            print('Gauge not detected, not received print, ' + readValue)
                            if serialString in readValue:
                                ser.write('Proceed'.encode('utf-8'))
                                print('Pi sent proceed')
                                config.receivedData = True
                        else:
##                            receivedData = False
##                            break
                            try:
                                dummyRead = ser.readline()
                                readValue = ser.readline().decode('utf-8')
                                print('Received Print, ' + readValue)
                            except Exception as e:
                                print(str(e))
                            if 'Proceed' in readValue:
                                config.receivedData = False
                                break
                            else:
                                config.receivedData = False        

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/command', methods=["GET","POST"])
def receive_command():
    global remoteControl
    global arduino_port
    remoteControl = True
    
    direction = request.args.get('op')
    
    if direction == '27':
        with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser: 
            ser.write('q'.encode('utf-8'))

        remoteControl = False
        return jsonify({"success":True}), 201

    try:
        with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:
            print('writing direction: {}'.format(direction))
            ser.write(direction.encode('utf-8'))
    except Exception as e:
        print(e)
    return jsonify({"success":True}), 201

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    global video_camera
    
    if video_camera is None:
        return {'Error':'Camera not yet initiated'}, 500
    
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=manageThreads, args=())
    t.daemon = True
    t.start()
    
    app.run(host= '192.168.1.3', debug=False, threaded=True)
    
##    app.run(host='128.197.180.233', debug=False, threaded=True)
