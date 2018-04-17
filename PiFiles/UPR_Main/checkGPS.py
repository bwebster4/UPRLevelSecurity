from __future__ import print_function
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



ser = serial.Serial()
ser.baudrate = 115200
ser.port = '/dev/ttyUSB0'
ser.open()
if(ser.isOpen):
    print("SkyTraq opened successfully!")
    
while True:
    location_csv = str(ser.readline())
    location_list = location_csv.split(",")

    for i in location_list:
        print(i, end = ' ')
