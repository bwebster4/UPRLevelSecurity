import subprocess
import serial
import pymap3d
import math
##from ... import config

actualMAMI = (42.27205171388889, 71.048680563888889)
actualMANB = (42.28405, 71.66126)

def degMin2deg(degrees, minutes):
    return degrees + minutes / 60

def getCurrentPosition(location_csv):
    
    location_list = location_csv.split(",")

    lat = 0
    lon = 0

    if(location_list[0] == "$GNGGA"):
        lat = degMin2deg(int(location_list[2][:2]), float(location_list[2][2:]))
        if(location_list[3] == "S"):
            lat *= -1

        lon = degMin2deg(int(location_list[4][:3]), float(location_list[4][3:]))
        if(location_list[5] == "W"):
            lon *= -1
        # print (location_csv) #Brock added this



    elif(location_list[0] == "$GNRMC"):
        lat = degMin2deg(int(location_list[3][:2]), float(location_list[3][2:]))
        if(location_list[4] == "S"):
            lat *= -1

        lon = degMin2deg(int(location_list[5][:3]), float(location_list[5][3:]))
        if(location_list[6] == "W"):
            lon *= -1
        # print (location_csv) #Brock added this

    elif location_list[0] == '$GNGLL':
        lat = degMin2deg(int(location_list[1][:2]), float(location_list[1][2:]))
        if(location_list[2] == "S"):
            lat *= -1

        lon = degMin2deg(int(location_list[3][:3]), float(location_list[3][3:]))
        if(location_list[4] == "W"):
            lon *= -1

    return (lat, lon)

def trackPosition(serialPort):
    currentPosition = (0.0,0.0)

    with serial.Serial(serialPort, 9600, timeout=2) as ser:
        if ser.isOpen():
#            print("serial is open")
            try:
                positionInput = ser.readline().decode('utf-8')
                return getCurrentPosition(positionInput)
            except:
                return currentPosition
#            print(positionInput)
            # positionInput = "$GPGGA,161319,4220.5667,N,07106.20004,W,1,08,0.9,40.0,M,46.9,M,,*47"
            # positionInput = "$GPGLL,4234.92,N,07110.65,W,162130,A,*1D"
            x = 0
            y = 0
            z = 0

            x1 = 0
            y1 = 0
            z1 = 0

            if "GNGGA" in positionInput or "GNRMC" in positionInput or "GNGLL" in positionInput:
                
                
                ntripOutput = subprocess.Popen(('./RTCM3/ntripclient', '-s', '64.28.83.185', '-r', '31000', '-m', 'RTCM3_MAMI', '-M', 'ntrip1', '-u', 'bweb', '-p', 'uppersec', '-n', positionInput), stdout=subprocess.PIPE)
                decodedOutput = subprocess.Popen(('python2', 'RTCM3/RTCM3_Decode.py'), stdin=ntripOutput.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                positionFound = False
                for line in iter(decodedOutput.stdout.readline, ""):
#                    print('stuck in first base')
                    stringLine = str(line)
##                            print(stringLine)
##                            print(ntripOutput.stdout.read())
                    if 'Message Number: 1006' in stringLine:
                        positionFound = True
                    if positionFound:
                        if 'ECEF-X:' in stringLine:
#                            print("ECEF-X")
#                            print(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                            x1 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                        if 'ECEF-Y:' in stringLine:
#                            print("ECEF-Y")
#                            print(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                            y1 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                        if 'ECEF-Z:' in stringLine:
#                            print("ECEF-Z")
#                            print(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                            z1 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                            
                            decodedOutput.terminate()
                            ntripOutput.terminate()
                            
                            
                            break
                        
                ntripOutput2 = subprocess.Popen(('./RTCM3/ntripclient', '-s', '64.28.83.185', '-r', '31000', '-m', 'RTCM3_MANB', '-M', 'ntrip1', '-u', 'bweb', '-p', 'uppersec', '-n', positionInput), stdout=subprocess.PIPE)
                decodedOutput2 = subprocess.Popen(('python2', 'RTCM3/RTCM3_Decode.py'), stdin=ntripOutput2.stdout, stdout=subprocess.PIPE, stderr = subprocess.DEVNULL)
                positionFound2 = False
                for line in iter(decodedOutput2.stdout.readline, ""):
                    stringLine = str(line)

                    if 'Message Number: 1006' in stringLine:
                        print('found message 1006')
                        positionFound2 = True
                    if positionFound2:
                        if 'ECEF-X:' in stringLine:
                            x2 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                        if 'ECEF-Y:' in stringLine:
                            y2 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])
                        if 'ECEF-Z:' in stringLine:
                            z2 = int(stringLine[stringLine.find(':')+2:len(stringLine)-3])

                            decodedOutput2.terminate()
                            ntripOutput2.terminate()                                    
                            uncorrectedPosition = getCurrentPosition(positionInput)

                            basePosition1 = pymap3d.ecef2geodetic(x1/100,y1/100,z1/100)
                            basePosition2 = pymap3d.ecef2geodetic(x2/100,y2/100,z2/100)

                            difference1 = (actualMAMI[0] - basePosition1[0], actualMAMI[1] - basePosition1[1])
                            difference2 = (actualMANB[0] - basePosition2[0], actualMANB[1] - basePosition2[1])

                            difference = ((difference1[0] + difference2[0])/2, (difference1[1] + difference2[1])/2)

                            currentPosition = (uncorrectedPosition[0] + difference[0], uncorrectedPosition[1] + difference[1])
                            return currentPosition

    return currentPosition
                    
##trackPosition("/dev/ttyACM0")
