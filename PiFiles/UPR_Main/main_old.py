import cv2
import sys
import serial
import os
# from mail import sendEmail
from flask import Flask, render_template, Response, jsonify, request
from camera import VideoCamera
import time
from datetime import datetime
import threading
from PersonAlert import sendAlert, upload_video

alert_update_interval = 15 # sends an email only once in this time interval
video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically
object_classifier = cv2.CascadeClassifier("models/facial_recognition_model.xml") # an opencv classifier
frame_interval = 100 #reads frame once per interval

filename = 'Patrol'

# App Globals (do not edit)
app = Flask(__name__)
last_epoch = 0
last_epoch_frame = 0
currently_found_object = False;

def check_for_objects():
	global last_epoch
	global last_epoch_frame
	global currently_found_object
	while True:
        # try:
        
            last_epoch_frame = time.time()
            frame, found_obj = video_camera.get_object(object_classifier)
##            print(found_obj)
            if not found_obj:
                currently_found_object = False
            if found_obj and not currently_found_object and (time.time() - last_epoch) > alert_update_interval:
                    last_epoch = time.time()
                    print("hey")
                    old_filename = video_camera.filename
                    video_camera.stop_recording()
                    new_filename = 'Patrol_' + datetime.now().isoformat() + '.h264'
                    video_camera.start_recording(new_filename)
                    
                    video_id = upload_video(old_filename)
                    sendAlert(video_id)
                    os.remove(old_filename)
                    currently_found_object = True
                    # sendEmail(frame)
                    print ("done!")
        # except:
          #   print ("Error sending email: "), sys.exc_info()[0]

@app.route('/')
def index():
    return render_template('index.html')

#ser = serial.Serial('/dev/ttyUSB0', 9600)

@app.route('/command', methods=["GET","POST"])
def receive_command():
    direction = request.args.get('op')
##    direction = request.json
    print(direction)
    print(direction.encode('utf-8'))
    try:
        ser.write(direction.encode('utf-8'))
        #ser.flush()
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
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()
    filename = 'Patrol_' + datetime.now().isoformat() + '.h264'
    video_camera.start_recording(filename)
    app.run(host='128.197.180.218', debug=False, threaded=True)