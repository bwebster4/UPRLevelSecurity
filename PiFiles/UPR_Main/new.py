#!/usr/bin/env python3
import serial
import math
from time import sleep
from typing import Tuple
import logging

from gnssRun import approxDistAng, initialAngleDifference


BAUD=115200
STOP=b'<0,0,0,0,1>'
OK_SIGNAL=b'OK'
arduino_port = '/dev/ttyACM1'
gps_port = '/dev/ttyACM0'
TO=0.1

def degMin2deg(degrees, minutes):
    return degrees + minutes / 60

def getGpsPos() -> Tuple[str,str]:
    with serial.Serial(gps_port, BAUD, timeout=TO) as ser:
        N = ser.inWaiting()
        while N < 81:
            # print('waiting for first packet, bytes received',N)
            sleep(0.1)
            N = ser.inWaiting()


        while True:
            N = ser.inWaiting()
            while N < 81:
                sleep(0.1)
                N = ser.inWaiting()

            line = ser.readline().decode('ascii')
            while line and not line.startswith('$GNRMC'):
                line = ser.readline().decode('ascii')

            if not line.startswith('$GNRMC'):
                continue

            # we got a GNRMC sentence
            line = line.split(',')
            if len(line) < 8:  #FIXME: fragmented line read, oops!
                print('FIXME: fragmented line read:',line)
                ser.flushOutput()
                continue
            # we got a "complete enough" GNRMC sentence (FIXME: check checksum)
            gpsfix = line[2]=='A'
            if not gpsfix:
                print('waiting for GPS fix')
                ser.flushOutput()
                continue

            # GPS fix OK
            lat = degMin2deg(int(line[3][:2]), float(line[3][2:]))
            if(line[4] == "S"):
                lat *= -1

            lon = degMin2deg(int(line[5][:3]), float(line[5][3:]))
            if(line[6] == "W"):
                lon *= -1

            # lat = line[3]+line[4]
            # lon = line[5]+line[6]

            return float(lat),float(lon)


def startmove(azimuth:float, direction):

    with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
        # ser.flushOutput()
        cmd = '<0,{},{},0,0>'.format(azimuth, direction).encode('ascii')
        ser.write(cmd)
        sleep(.1)

        # validate move command
        buf = ser.readline().strip()
        print(buf)

        while OK_SIGNAL not in buf:
            print(buf)
            # ser.write(cmd)
            # ser.flushInput()
            sleep(.1)

            buf = ser.readline().strip()

        # if buf != cmd:
        #     logging.error('Arduino direction to move validation failed, buffer: {}'.format(buf))
        #     ser.flushOutput()
        #     return

        # ser.write(b'Proceed')


def stopmove():
	with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
		ser.write(STOP) # stopmoving


def waitForArduino():
    with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
        output = ser.readline().decode('ascii').strip()
        while output != 'Calibrated':
            if output:
                print(output)
                # ser.flushOutput()
            sleep(0.2)
            output = ser.readline().decode('ascii').strip()



def checkForObjects(totalAngle):

    with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
        output = ser.readline().decode('ascii').strip()
        print(output)
        if output.startswith('<') and 'OBJ' in output and output.endswith('>'):
            output = output[1:len(output) - 2]
            angle = float(output.split(',')[1])
            sleep(0.1)
            ser.write(b'<OK>')
            sleep(0.1)
            # ser.flushOutput()
            turnAngle, direction = initialAngleDifference(angle, totalAngle)

            ser.close()
            startmove(turnAngle, direction)



def dist(y1,x1,y2,x2):
    return math.sqrt((x2 - x1)**2 + (y2-y1)**2)

if __name__ == '__main__':


    waitForArduino()

    # lat, lon = getGpsPos()
    lat, lon = (0.0, 0.0)

    latgoal = lat + 0.00000
    longoal = lon + 0.00009

    # for latgoal, longoal in zip(latgoals,longoals):
    currentAngle = 0

    distance, totalAngle = approxDistAng(latgoal, longoal, lat, lon)
    turnAngle, direction = initialAngleDifference(currentAngle, totalAngle)

    print("Starting Movement")

    startmove(turnAngle, direction)
    while dist(lat,lon,latgoal,longoal) > 0.000015:
        sleep(0.1)
        # lat,lon = getGpsPos()

        print("Pos: {}, {}".format(lat, lon))

        checkForObjects(totalAngle)

    print("At Destination")

    stopmove()

