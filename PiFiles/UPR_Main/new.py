#!/usr/bin/env python3
import serial
from time import sleep
from typing import Tuple
import logging

BAUD=115200
STOP=b'1,0,0,0,0'
OK_SIGNAL=b'<OK>'
arduino_port = '/dev/ttyACM1'
gps_port = '/dev/ttyACM0'
TO=0.1


def getGpsPos() -> Tuple[str,str]:
    with serial.Serial(gps_port, BAUD, timeout=TO) as ser:
        N = ser.inWaiting()
        while N < 81:
            print('waiting for first packet, bytes received',N, end='\r')
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
            lat = line[3]+line[4]
            lon = line[5]+line[6]

            return lat,lon


def startmove(azimuth:float):

    with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
        ser.flushOutput()
        cmd = '<0,{},r,0,0>'.format(azimuth).encode('ascii')
        ser.write(cmd)
        sleep(.1)
        # validate move command
        buf = ser.readline().strip()
        while buf and buf!=OK_SIGNAL:
            ser.write(cmd)
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


def checkmode():
    with open('mode.txt','r') as f:
        stat = f.readline().lower()
        if stat.startswith('a'): # autonomous
            pass
        elif stat.startswith('r'): # manual remote control
            stopmove()
            # tell Arduino to go to manual mode
            manualmove()
        else:
            stopmove()
            raise ValueError('unexpected command {}'.format(stat))

def waitForArduino():
    with serial.Serial(arduino_port, BAUD, timeout=TO) as ser:
        output = ser.readline().strip()
        while output != b'Calibrated':
            if len(output) > 1:
                print(output)
                ser.flushOutput()
                sleep(0.2)
                output = ser.readline().strip()

if __name__ == '__main__':


    waitForArduino()

    lat, lon = getGpsPos()

    latgoal=(lat + 0.00000)
    longoal=(lon + 0.00009)

    for latg, long in zip(latgoal,longoal):

        lat,lon = getGpsPos()
        #az = calcAzimuth(lat,lon,latg,long)

        az = 35 #FIXME
        startmove(az)
       # while dist(lat,lon,latg,long) > eps:
       #     sleep(0.1)
       #     lat,lon = getGpsPos()

        sleep(2.)  #FIXME
        stopmove()

