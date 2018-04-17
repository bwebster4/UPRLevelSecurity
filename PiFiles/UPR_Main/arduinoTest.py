import serial
import string
import time

ser = serial.Serial("/dev/ttyUSB0", 9600)
if(ser.isOpen() == False):
    ser.open()

try:
        while 1:
                ser.write("1")
                time.sleep(2)
                ser.write("2")
                time.sleep(2)
                ser.write("3")
                time.sleep(2)
                
except KeyboardInterrupt:
        pass

ser.close()
