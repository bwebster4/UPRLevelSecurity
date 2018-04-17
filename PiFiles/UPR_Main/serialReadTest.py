import glob
import serial
import time

ports = glob.glob('/dev/ttyACM*')
arduino_port = None
gps_port = None
for port in ports:
    try:
        arduino_port = port
    except Exception as e:
        print(str(e))
        
receivedData = False

with serial.Serial(arduino_port, 115200, timeout=2) as ser:
    if ser.isOpen():
        while 1:
            readData = ser.readline().decode('utf-8')
            print('This is the initial read: {}'.format(readData))
##            if not receivedData:
##                try:
##                    serialString = '{},{},{},{},{}\n'.format(0, 0, 0, 0, 0)
##                    ser.write(serialString.encode('utf-8'))
##                    readValue = ser.readline().decode('utf-8')
##                    print('Not received print, ' + readValue)
##                    if serialString in readValue:
##                        ser.write('Proceed'.encode('utf-8'))
##                        print('Pi sent proceed')
##                        receivedData = True
##                except Exception as e:
##                    print(str(e))
##                    
##            else:
##                try:
##                    dummyRead = ser.readline()
##                    readValue = ser.readline().decode('utf-8')
##                    print('Received Print, ' + readValue)
##                except Exception as e:
##                    print(str(e))
##                if 'Proceed' in readValue:
##                    while 1:
##                        time.sleep(1)
##                        readValue = ser.readline().decode('utf-8')
##                        print('Proceed worked, ' + readValue)
##                else:
##                    receivedData = False