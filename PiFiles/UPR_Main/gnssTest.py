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
try:
    port = "/dev/ttyUSB0"
    print(port)  #Brock added this
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.port = port
    ser.open()
    if(ser.isOpen):
        print("SkyTraq opened successfully!")
except (Exception, serial.SerialException):
    raise EnvironmentError('No ports found')

# File name constitution
##usr = socket.gethostname()
##t = datetime.datetime.utcnow()
##tm = t.strftime('%Y%m%d')
##dd1 = t.strftime('%d')
##mm1 = t.strftime('%m')
##yy1 = t.strftime('%y')
##day_in_year = t.timetuple().tm_yday
##path = os.path.dirname(os.path.realpath(__file__))
##fn = path+'/data/'+usr+'0'+str(day_in_year)+'.txt'
##print(fn) #Brock added this
##fw = createfile(fn)

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




# Main script
a = 0
# Configure the board
ack1 = setModuleMore(ser)
time.sleep(0.1)
ack2 = setDataOutput(ser)
time.sleep(0.1)
pos_rate = readPositionDataRate(ser)
# bin_rate = readBinaryDataRate(ser)
#print ('Data return ack: ', ack2)
#print ('Query return: ', pos_rate)
#~ print ('Query return binary: ', ack1)
#~ print ('Query return binary: ', ack2)

# Read and store the data
while True:
    print(ser.readline())
        
    # print(location_list[2] + ' '+ location_list[4])
    # print (location_csv) #Brock added this
    #a+=1
print ('to je to')
ser.close()
fw.close()