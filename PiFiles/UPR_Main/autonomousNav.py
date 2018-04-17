from main_v2 import remoteControl, setAtGauge
import time
import math
import serial
from gnssRun import approxDistAng, initialAngleDifference
from RTCM3.positionTracker import trackPosition
import os
import config

def isAtDest(destination, current):
##    return current > destination
    return (math.fabs(destination[0] - current[0] < 0.000015) and math.fabs(destination[1] - current[1] < 0.000015))
        

def startAutonomousNavigation(gps_port, arduino_port):
    
    print('Autonomous Nav Started')

    points = [(0, 0.00009)]
    
##    timeToDest = 10
##    startTime = time.time()
##    destTime = None
    
    nextDest = None
    currentAngle = 0 # THIS IS EAST IN OUR CODE STRAIGHT EAST
    
    currentPosition = (0.0, 0.0)
    
    objectAvoidance = False
    
    arduinoStarted = False
    
    target = (0, 0)

    atDest = False
    
    config.receivedData = False
        
    while True:
        if not config.autonomousFlag:
            time.sleep(1)
            continue
        
        testpos = trackPosition(gps_port)
        print('currentposition: {}'.format(currentPosition))

        if(testpos[0] == 0 and testpos[1] == 0):
            pass
        else:
            currentPosition = testpos
                
        if(len(points) > 0 and nextDest == None and arduinoStarted):
            nextDest = points.pop(0)
            target = (currentPosition[0] + nextDest[0], currentPosition[1] + nextDest[1])            
            print('TARGET: ')
            print(target)
            distance, totalAngle = approxDistAng(target[0], target[1], currentPosition[0], currentPosition[1])
            turnAngle, direction = initialAngleDifference(currentAngle, totalAngle)
            
##            print('Distance: {}, Total Angle: {}, Turn Angle: {}, Direction: {}'.format(distance, totalAngle, turnAngle, direction))
            
        if not arduinoStarted:
            with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:
                if ser.isOpen():
                    try:
                        arduino_output = ser.readline().decode('utf-8')
                        print(arduino_output)
                    except Exception as e:
                        print(str(e))
                        continue
                    if 'Calibrated' in arduino_output:
                        if not arduinoStarted:
##                            destTime = time.time() + timeToDest
                            arduinoStarted = True
                            
                        if remoteControl:
                            ser_rc = '1'
                        else:
                            ser_rc = '0'
                        while 1:
                            if not config.receivedData:
                                try:
                                    serialString = '{},{},{},{},{}\n'.format(0, 0, 0, ser_rc, ' ')
                                    ser.write(serialString.encode('utf-8'))
                                    readValue = ser.readline().decode('utf-8')
                                    print('Autonomous Nav, not received print, ' + readValue)
                                    if serialString in readValue:
                                        ser.write('Proceed'.encode('utf-8'))
                                        print('Pi sent proceed')
                                        config.receivedData = True
                                except Exception as e:
                                    print(str(e))
                            else:
                                try:
                                    dummyRead = ser.readline()
                                    readValue = ser.readline().decode('utf-8')
                                    print('Autonomous Nav, received Print, ' + readValue)
                                except Exception as e:
                                    print(str(e))
                                if 'Proceed' in readValue:
                                    config.receivedData = False
                                    break
                                else:
                                    config.receivedData = False
            
        else:
##            atDest = isAtDest(destTime, time.time())
            atDest = isAtDest(target, currentPosition)
            with serial.Serial(arduino_port, config.baudRate, timeout=2) as ser:               
                readValue = ser.readline().decode('utf-8')
                print('Arduino Started: {}'.format(readValue))
                if 'Avoided' in readValue:
                    while 1:
                        if not config.receivedData:
                            diffAngle = ''
                            angleFlag = False
                            for elem in readValue:
                                if not angleFlag:
                                    if elem == '<':
                                        angleFlag = True
                                else:
                                    if elem == '>':
                                        angleFlag = False
                                        #break
                                    else:
                                        diffAngle += elem
                            print('sending angle: {}'.format(diffAngle))
                            #ser.write(diffAngle.encode('utf-8'))
                            config.receivedData = True
                        else:
                            diffAngle = float(diffAngle)
                            break
                            #readValue = ser.readline().decode('utf-8')
                            #print("Should get proceed, end of object avoidance {}".format(readValue))
                            #if 'Proceed' in readValue:
                            #    for i in range(10):
                            #       ser.write("Proceed".encode('utf-8'))
                            #    diffAngle = float(diffAngle)
                            #    turnAngle, direction = initialAngleDifference(currentAngle-diffAngle, totalAngle)
                            #    config.receivedData = False
                            #    break
                            #else:
                            #    config.receivedData = False
                    while 1:
                        if not config.receivedData:
                            distance, totalAngle = approxDistAng(target[0], target[1], currentPosition[0], currentPosition[1])
                            turnAngle, direction = initialAngleDifference(currentAngle+diffAngle, totalAngle)
                            time.sleep(0.5)
                            serialString = '{},{},{},{},{}\n'.format(0, turnAngle, direction, ser_rc, 0)
                            ser.write(serialString.encode('utf-8'))
                            time.sleep(0.5)
                            readValue = ser.readline().decode('utf-8')
                            print('Autonomous Nav, not received print, ' + readValue)
                            if serialString in readValue:
                                ser.write('Proceed'.encode('utf-8'))
                                print('Pi sent proceed')
                                config.receivedData = True
                        else:
                            try:
                                dummyRead = ser.readline()
                                readValue = ser.readline().decode('utf-8')
                                print('Autonomous Nav, received Print, ' + readValue)
                            except Exception as e:
                                print(str(e))
                            if 'Proceed' in readValue:
                                config.receivedData = False
                                break
                            else:
                                config.receivedData = False
            if atDest:
                config.receivedData = False
                nextDest = None
                setAtGauge(True)
                time.sleep(1)
