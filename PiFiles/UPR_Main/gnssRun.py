# -*- coding: utf-8 -*-
"""
Created on Sun May 21 14:35:38 2017
@author: smrak
"""

import sys
import glob
import serial
import getpass
import datetime
import math
import os.path
# import utilfunctions
import time
import socket

def serial_ports():    
##    ports = glob.glob('/dev/ttyUSB*')
##    ports = glob.glob('/dev/ttyACM*')
    arduino_port = '/dev/ttyACM0'
    gps_port = '/dev/ttyACM1'
##    count = 0
##    for port in ports:
        #if count == 0:
         #   try:
##                with serial.Serial(port, 115200, timeout=1) as s:
##                    if 'ARDUINO' in s.read(100).decode('utf-8'):
##                        arduino_port = port
##                    else:
##                        gps_port = port
##                arduino_port = port
                
##            except Exception as e:
##                print(str(e))
##        else:
##            gps_port = port            
##        count+=1
            
    print('Arduino Port: {}'.format(arduino_port))
    
    return arduino_port, gps_port

def checksum(data):
    """
    Calculate and return a checksum for skytraq binary protocol
    XOR
    """
    checksum = 0
    for by in data:
        checksum ^= ord(by)
    #print (hex(checksum))
    return hex(checksum)
    
def createfile(fn):
    """
    """
    if not os.path.exists(fn):
        fw = open(fn, 'wb')
    else:
        c = 1
        fn_temp = fn + '_' + str(c)
        while os.path.isfile(fn_temp):
            c += 1
            fn_temp = fn + '_' + str(c)
        fw = open(fn_temp, 'wb')
    return fw

def newfile(fw, dd, mm, yy):
    """
    """
    fw.close()
    #t = datetime.datetime.utcnow()
    #tm = t.strftime('%Y%m%d')
    #day = t.strftime('%d')
    tm = str(yy)+str(mm)+str(dd)
    t = datetime.datetime.utcnow()
    day_in_year = t.timetuple().tm_yday
    path = os.path.dirname(os.path.realpath(__file__))
    fn = path+'/data/'+usr+'0'+str(day_in_year)+'.'+yy+'r'
    fw = createfile(fn)
    return fw, dd, mm, yy

def setModuleMore(ser):
#    prefix = '\xa0\xa1\x00\x03'
    data = '\x09\x01\x01'
    cs = checksum(data)
    #~ print (cs)
#    cs = chr(sum(map(ord, data)))
#    sufix = '\x0d\x0a'
    message = '\xa0\xa1\x00\x03\x09\x01\x01\x09\x0d\x0a'
    ser.write(message)
    ack = ser.readline()
    # print("setModuleMore ack: ")
    # print([ack])
    return ack
#    print (message)


# query position update rate 
def readPositionDataRate(ser):
    message = '\xa0\xa1\x00\x01\x10\x10\x0d\x0a'
    ser.write(message)
    ack = ser.readline()
    msg = ser.readline()
    # print("readPosistionDataRate ack, msg: ")
    # print([ack, msg])
    return [ack, msg]

def readBinaryDataRate(ser):
#    prefix = '\xa0\xa1\x00\x01'
#    data = '\x1f'
#    cs = chr(sum(map(ord, data)))
#    sufix = '\x0d\x0a'
    message = '\xa0\xa1\x00\x01\x1f\x1f\x0d\x0a'
    ser.write(message)
    ack = ser.readline()
    msg = ser.readline()
    # print("ack, msg: " )
    # print([ack,msg]) #Brock added this
    return [ack, msg]

def setDataOutput(ser):
    # 'A0 A1 00 09 1E'
    # 04 == 10Hz
    # 00 00 01 00
    # 01 GPS only
    # 00 01
    # 37
    # 0D 0A
    data = '\x1E\x04\x00\x00\x01\x00\x01\x00\x01'
    message = '\xA0\xA1\x00\x08\x1E\x04\x01\x01\x01\x00\x01\x01\x1B\x0D\x0A' # 10 Hz
#    message = '\xA0\xA1\x00\x09\x1E\x03\x01\x01\x01\x01\x01\x00\x01\x1D\x0D\x0A'
#    message = '\xA0\xA1\x00\x08\x1E\x00\x01\x01\x01\x00\x01\x01\x1F\x0D\x0A' # 1Hz
    ser.write(message)
    ack = ser.readline()
    return ack

def approxDistAng(gLat, gLon, iLat, iLon):
    gLat /= math.pi
    gLon /= math.pi
    iLat /= math.pi
    iLon /= math.pi
    
    lon_difference = gLon-iLon
    lat_difference = gLat-iLat

    deltaX = (6371000)*(lon_difference)*(math.cos(gLat))
    deltaY = (6371000)*(lat_difference)
    
    #Case that X doesn't change, either you need to go straight North or straight South
    if deltaX == 0:
        if lat_difference > 0:
            dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
            angle = 90
            return (dis,angle)
        else:
            dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
            angle = 270
            return (dis,angle)
        
    #Case that Y doesn't change, either you need to go straight West or straight East    
    if deltaY == 0:
        if lon_difference < 0:
            dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
            angle = 180
            return (dis,angle)
        else:
            dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
            angle = 0
            return (dis,angle)
        
    #Going North East
    if lon_difference > 0 and lat_difference > 0:
        dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
        angle = math.atan(deltaY/deltaX) * (180/math.pi)
        return (dis,angle)
    
    #Going North West
    elif lon_difference < 0 and lat_difference > 0:
        dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
        angle = 180 - (math.atan(deltaY/deltaX) * (180/math.pi))
        return (dis,angle)
    
    #Going South East
    elif lon_difference > 0 and lat_difference < 0:
        dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
        angle = math.atan(deltaY/deltaX) * (180/math.pi)
        return (dis,angle)
    
    #Going South West
    else:
        dis = math.sqrt(math.pow(deltaX, 2) + math.pow(deltaY, 2))
        angle = 180 + (math.atan(deltaY/deltaX) * (180/math.pi))
        return (dis,angle)
    

def initialAngleDifference(init_angle, total_angle):
    if init_angle > 0:
        init_angle = 360 - init_angle
    else:
        init_angle*=-1
    diff = total_angle - init_angle
    if diff > 0:
        if diff > 180:
            turn_angle = 360 - diff
            direction = "r"
            return([turn_angle, direction])
        else:
            turn_angle = diff
            direction = "l"
            return([turn_angle, direction])
    elif diff < 0:
        if diff < -180:
            turn_angle = 360 + diff
            direction = "l"
            return([turn_angle, direction])
        else:
            turn_angle = diff * -1
            direction = "r"
            return([turn_angle, direction])
    else:
        turn_angle = 0
        direction = ' '
        return([turn_angle, direction])

def getCurrentPosition(gps_port):
    
    ser = serial.Serial(gps_port)
    ser.baudrate = 115200
    
    location_csv = str(ser.readline())
    location_list = location_csv.split(",")

    lat = 0
    lon = 0

    if(location_list[0] == "$GPGGA"):
        lat = float(location_list[2])/100
        if(location_list[3] == "S"):
            lat *= -1

        lon = float(location_list[4])/100
        if(location_list[5] == "W"):
            lon *= -1
        # print (location_csv) #Brock added this



    elif(location_list[0] == "$GPRMC"):
        lat = float(location_list[3])/100
        if(location_list[4] == "S"):
            lat *= -1

        lon = float(location_list[5])/100
        if(location_list[6] == "W"):
            lon *= -1
        # print (location_csv) #Brock added this

    elif location_list[0] == '$GPGLL':
        lat = float(location_list[1])/100
        if(location_list[2] == "S"):
            lat *= -1

        lon = float(location_list[3])/100
        if(location_list[4] == "W"):
            lon *= -1

    return (lat, lon)

# Open serial port
##try:
##    port = serial_ports()[0]
##    print(port)  #Brock added this
##    ser = serial.Serial()
##    ser.baudrate = 115200
##    ser.port = port
##    ser.open()
##    if(ser.isOpen):
##        print("SkyTraq opened successfully!")
##except (Exception, serial.SerialException):
##    raise EnvironmentError('No ports found')
##
### File name constitution
##usr = socket.gethostname()
##t = datetime.datetime.utcnow()
##tm = t.strftime('%Y%m%d')
##dd1 = t.strftime('%d')
##mm1 = t.strftime('%m')
##yy1 = t.strftime('%y')
##day_in_year = t.timetuple().tm_yday
##path = os.path.dirname(os.path.realpath(__file__))
##fn = path+'/data/'+usr+'0'+str(day_in_year)+'.txt'
### print(fn) #Brock added this
##fw = createfile(fn)
##
##goal_latitude = input("Input goal latitude value: ")/100.00
##goal_lat_dir = raw_input("Input goal latitude direction (N/S): ")
##
##goal_longitude = input("Input goal longitude value: ")/100.00
##goal_lon_dir = raw_input("Input goal longitude direction (E/W): ")
##
##if(goal_lat_dir == "S" or goal_lat_dir == "s'"):
##    goal_latitude *= -1
##
##if(goal_lon_dir == "W" or goal_lon_dir == "w"):
##    goal_longitude *= -1
##
##
##
##
### Main script
##a = 0
### Configure the board
##ack1 = setModuleMore(ser)
##time.sleep(0.1)
##ack2 = setDataOutput(ser)
##time.sleep(0.1)
##pos_rate = readPositionDataRate(ser)
### bin_rate = readBinaryDataRate(ser)
###print ('Data return ack: ', ack2)
###print ('Query return: ', pos_rate)
###~ print ('Query return binary: ', ack1)
###~ print ('Query return binary: ', ack2)
##
### Read and store the data
##while True:
##    tt = datetime.datetime.utcnow()
##    dd = tt.strftime('%d')
##    yy = tt.strftime('%y')
##    mm = tt.strftime('%m')
##    if (int(dd) > int(dd1)) or (int(yy) > int(yy1)) or (int(mm) > int(mm1)):
##        fw, dd1, mm1, yy1  = newfile(fw, dd, mm, yy)
##    fw.write(ser.readline())
##    location_csv = str(ser.readline())
##    location_list = location_csv.split(",")
##
####    lat = 0
####    lon = 0
##
##    if(location_list[0] == "$GPGGA"):
##        lat = float(location_list[2])/100
##        if(location_list[3] == "S"):
##            lat *= -1
##
##        lon = float(location_list[4])/100
##        if(location_list[5] == "W"):
##            lon *= -1
##        # print (location_csv) #Brock added this
##
##
##
##    elif(location_list[0] == "$GPRMC"):
##        lat = float(location_list[3])/100
##        if(location_list[4] == "S"):
##            lat *= -1
##
##        lon = float(location_list[5])/100
##        if(location_list[6] == "W"):
##            lon *= -1
##        # print (location_csv) #Brock added this
##
##    elif location_list[0] == '$GPGLL':
##        lat = float(location_list[1])/100
##        if(location_list[2] == "S"):
##            lat *= -1
##
##        lon = float(location_list[3])/100
##        if(location_list[4] == "W"):
##            lon *= -1
##
##    else:
##        print(location_list[0])
##    
##    print("iLAT", lat, "iLON", lon)
##    
##    distance, totalAngle = approxDistAng(goal_latitude, goal_longitude, lat, lon)
##    initialAngle = 240
##    turnAngle, direction = initialAngleDifference(initialAngle, totalAngle)
##        
##    print('turnAngle: {} distance: {} direction: {}'.format(turnAngle, distance, direction))
    
##    ang = (direc[1])*(180/3.14159)
##    #print(ang)
##    # print(ang)
##
##    if(ang < 0 and ang > -45):
##        print("Turn clockwise by: ")
##        print(math.fabs(ang) + 90)
##    elif( ang > 0 and ang < 90):
##        print("Turn clockwise by: ")
##        print(90 - math.fabs(ang))
##    elif(ang > 90 and ang < 180):
##        print("Turn counterclockwise by: ")
##        print(ang)
##    elif(ang > 180 and ang < 270):
##        print("Turn counterclockwise by: ")
##        print("yeah")
##    else:
##        print("Go straight!")
##
##    
##    print("Travel distance in m: ")
##    print(direc[0])
##
##    print('\n')
        
    # print(location_list[2] + ' '+ location_list[4])
    # print (location_csv) #Brock added this
    #a+=1
##print ('to je to')
##ser.close()
##fw.close()
