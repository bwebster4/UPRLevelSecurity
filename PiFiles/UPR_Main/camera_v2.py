import cv2
from imutils.video.pivideostream import PiVideoStream
import imutils
import time
from datetime import datetime
import numpy as np
from imutils.object_detection import non_max_suppression
from imutils import paths
import math
from PersonAlert import sendAlert, upload_video
import config
import serial


class VideoCamera(object):
    def __init__(self, flip = False):
        self.vs = PiVideoStream().start()
        #self.vs.camera.framerate = 1
        self.flip = flip
        time.sleep(2.0)

    def __del__(self):
        self.vs.camera.stop_recording()
        video_id = upload_video(self.filename)
        self.vs.stop()

    def start_recording(self, filename):
        self.filename = filename
        self.vs.camera.start_recording(filename, format='h264')

    def stop_recording(self):
        self.vs.camera.stop_recording()

    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(frame, 0)
        return frame

    def get_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def get_object(self, classifier):
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy() 
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True

        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return (jpeg.tobytes(), found_objects)
    
    def Tracker(self, objects, arduino_port, func):
        frame = self.flip_if_needed(self.vs.read()).copy()
        tracker = cv2.MultiTracker("KCF")
        cnt = 0

        bbox = ([[x, y, w, h] for (x, y, w, h) in objects])

        bbox = tuple(bbox[0])

        isTracking = tracker.add(frame, bbox)
        
        angleList = []
        
        detect = False
        
        receivedData = False
        
        centeredFlag = False

        while True:
            #print(isTracking)
            #print(cnt)
            # Read a new frame
            frame = self.flip_if_needed(self.vs.read()).copy()
            

            # Update tracker
            isTracking, bbox = tracker.update(frame)

            # Draw bounding box
            if isTracking:
                cnt += 1
                for (x, y, w, h) in bbox:
                    x = int(x)
                    y = int(y)
                    w = int(w)
                    h = int(h)
                    
                    
##                print(cnt)
##                print("tracking")
                    
                if 'VideoCamera.GaugeDetector' in str(func):
                    left = x + w < frame.shape[1] / 2
                    right = x > frame.shape[1] / 2
                    center = frame.shape[1] / 2 > x and frame.shape[1] / 2 < x + w
                    
                    with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:
                        if ser.isOpen():
                            if not centeredFlag:
                                while 1:
                                    time.sleep(0.5)
                                    if not receivedData:
                                        if left:
                                            serialString = '-1'
                                            ser.write(serialString.encode('utf-8'))
                                        elif right:
                                            serialString = '1'
                                            ser.write(serialString.encode('utf-8'))
                                        elif center:
                                            serialString = '0'
                                            ser.write(serialString.encode('utf-8'))
                                            centeredFlag = True
                                        try:
                                            time.sleep(0.5)
                                            readValue = ser.readline().decode('utf-8')
                                        except Exception as e:
                                            print(str(e))
                                        print('Gauge Centering, not received print, ' + readValue)
                                        if serialString in readValue:
                                            ser.write('Proceed'.encode('utf-8'))
                                            print('Pi sent proceed')
                                            receivedData = True
                                    else:
                                        try:
                                            dummyRead = ser.readline()
                                            readValue = ser.readline().decode('utf-8')
                                            print('Gauge Centering, received Print, ' + readValue)
                                        except Exception as e:
                                            print(str(e))
                                        if 'Proceed' in readValue:
                                            receivedData = False
                                            break
                                        else:
                                            receivedData = False
                                            
                            else:
                                startTime = time.time()
                                while 1:
                                    ser_read = ser.readline().decode('utf-8')
                                    print('ser_read: {}'.format(ser_read))
                                    if 'Detect' in ser_read:
                                        print('Were in Detect, weve received a detect thing')
                                        tempFrame, tempFound_objs, newCoordinates = self.GaugeDetector()
                                        if tempFound_objs:
                                            detect = True
                                    if detect:
                                        x = newCoordinates[0][0]
                                        y = newCoordinates[0][1]
                                        h = newCoordinates[0][2]
                                        w = newCoordinates[0][3]
                                        angle = self.GaugeReader(frame, [x,y,h,w])
                                        if angle != None:
                                            angleList.append(angle)
                                            break
                                        if time.time() - startTime > 30:
                                            break
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2, 1)

                
                if cnt == 15:
                    print(cnt)
                    f, stillDetecting, o = func()
                    cnt = 0
                    
                    if not stillDetecting:
                        isTracking = False
                        break
                    
                    if len(angleList) > 0:
                        avgDegrees = np.median(angleList)
                        avgDegrees = round(avgDegrees, 2)
                        video_id = -1
                        title = "Gauge Reading"
                        text = "Gauge has been read at destination. Value is {}".format(avgDegrees)
                        sendAlert(title, text, video_id)
                        config.atGauge = False
                        angleList[:] = []
                        return False

                    bbox = ([[x, y, w, h] for (x, y, w, h) in o])

                    bbox = tuple(bbox[0])

                    isTracking = tracker.add(f, bbox)
                    
                    
            else :
                break
            
        centeredFlag = False    
        return isTracking
    
    def HOG_Person_Detector(self):
        # initialize the HOG descriptor/person detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy()
        
        image = imutils.resize(frame, width=min(400, frame.shape[1]))
        orig = image.copy()
        
        # detect people in the image
        (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4), padding=(8, 8), scale=1.05)
        if len(rects) > 0:
            found_objects = True
                
        # draw the original bounding boxes
        for (x, y, w, h) in rects:
            cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)
        
        # apply non-maxima suppression to the bounding boxes using a
        # fairly large overlap threshold to try to maintain overlapping
        # boxes that are still people
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)
        
        # draw the final bounding boxes
        for (xA, yA, xB, yB) in pick:
            cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
            
        # return
        #if len(pick) > 0:
            #found_objects = True
            
        ret, jpeg = cv2.imencode('.jpg', frame)
        
        return (jpeg, found_objects, pick)

    
    def GaugeDetector(self):
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy()
        blur = cv2.medianBlur(frame, 5)
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        circle_coordinates = [[0,0,0,0]]
        
        
        try:
            circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,20,
                                param1=50,param2=65,minRadius=0,maxRadius=0)

            circles = np.uint16(np.around(circles))
            for i in circles[0,:]:
                # draw the outer circle
                #cv2.circle(frame,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                cv2.circle(frame,(i[0],i[1]),2,(0,0,255),3)
                #print(i[0])
                cv2.rectangle(frame, (i[0]-i[2],i[1]-i[2]), (i[0]+i[2],i[1]+i[2]), (0, 255, 0), 4)
                if len(circles) > 0:
                    found_objects = True
                x = i[0]-i[2]
                y = i[1]-i[2]
                h = 2*i[2]
                circle_coordinates = [[x,y,h,h]]
                
        except Exception as e:
            pass
        
        #ret, jpeg = cv2.imencode('.jpg', frame)
        
        return (frame, found_objects, circle_coordinates)
    
    def GaugeReader(self, frame, coordinates):
        print('We are in GaugeReader')
        found_objects = False
        
##        print(coordinates)
        
        x = int(coordinates[0])
        y = int(coordinates[1])
        h = int(coordinates[2])
        w = int(coordinates[3])
        
        if x > 60000:
            x = 0
        if y > 60000:
            y = 0
        
        img = frame[y:y+h, x:x+w]
        
##        cv2.imshow('cropped', img)
##        cv2.waitKey(0)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
##        cv2.imshow('gray pic', gray)
##        cv2.waitKey(0)
        #edges = cv2.Canny(gray,50,150,apertureSize = 3)
        edges = cv2.Canny(gray,100,200,apertureSize = 3)
        
        minLineLength = 140
        maxLineGap = 10
        
        lines = cv2.HoughLinesP(edges,1,np.pi/180,50,minLineLength,maxLineGap)
            
        if lines is None:
            print('No lines detected')
            return
        
        try:
            
            for x1,y1,x2,y2 in lines[0]:
                print('x:{} y:{} h:{} w:{}'.format(x1, y1, x2, y2))
                cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
                
            if math.fabs(x2 - x1) < 0.1:
##                if y2 - y1 > 0:
                degrees = 90.0
            else:                
                angle = math.atan((y2-y1)/(x2-x1))
                angle_degrees = 360.0/(2*math.pi) * angle
                degrees = round(angle_degrees, 2)
            
##            if degrees != 0:
##                cv2.imwrite('gaugeAngle.jpg', img)

            
            print('Degrees: ', str(degrees))
            
        except Exception as e:
            print(str(e))
            
        return degrees
            
