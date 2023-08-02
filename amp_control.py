"""
python program to comunicate with arduino amp control board
used to get system stats, control logging, control amp gain and power
author: RNS
"""

# imports
import serial
import time
import sys
import threading


# global variables and flags
# could use a flag array or reg, but to keep it simple just using vars
shutdownFlag = 0 # used to indicate program shutdown
vvaFlag = 0 # change in VVA value
loggingToggleFlag = 0 # change in logging toggle
ampToggleFlag = 0 # change in amp state

loggingFreq = 5 # seconds per update
vvaValue = 0 # gain value of the amp, int, 0 - 100 %
currValue = 0 # current value from ADC. Int, 10 bit (nano)
tempValue = 0 # temp value from ADC, Int, 10 bit (nano)
ampState = 0 # 0 for off, 1 for on

def arduinoBootCheck(serialPort):
    time.sleep(2)
    numBytes = serialPort.in_waiting
    data = bytearray(serialPort.read(size=numBytes)[:-2])
    test = bytearray("<good morning, dave>","ASCII")
    if data:
        if (data == test):
            return True
        else:
            return False

def loggingUpdate(serialPort):
    global currValue
    global tempValue
    serialPort.write(bytearray([1,0]))
    time.sleep(.1)
    w = serialPort.in_waiting
    tempValue = int(serialPort.read(w))
    # send current request flag
    serialPort.write(bytearray([0,0]))
    time.sleep(.1)
    w = serialPort.in_waiting
    currValue = int(serialPort.read(w))
    start = time.time() # reset start time
    # if logging, log the data
    if (loggingToggleFlag == 1):
        logFile = open("logfile.txt", "a+")
        logFile.write(str(round(tempValue*.4882,2)) + " " + str(round(currValue*.00976,2)) + " " + str(vvaValue)
                        + " " + str(ampState)+"\n")
        logFile.close()
    return start

def serialHandler(serialPort):
    global shutdownFlag
    global ampToggleFlag
    global loggingToggleFlag
    global vvaFlag
    global loggingFreq
    global vvaValue
    global currValue
    global tempValue
    global ampState

    # comms connected, move onto poll loop
    # poll global flags for tasks
    stopBool = True
    # function start time
    start = time.time()
    while stopBool:
        time.sleep(.1)
         # shutdown flag
        if (shutdownFlag == 1):
            stopBool = False
            print("SH: caught exit bool")
        # amp toggle
        elif(ampToggleFlag == 1):
            ampToggleFlag = 0 #reset flag
            if (ampState == 0):
                ampState = 1
            else:
                ampState = 0
            # send amp state toggle packet
            serialPort.write(bytearray([3,0]))
            time.sleep(.1)
            w = serialPort.in_waiting
            temp = int.from_bytes(serialPort.read(w),"little")
            if (temp == ampState):
                print("amp state set")
        # vva gain update
        elif(vvaFlag == 1):
            vvaFlag = 0 # reset flag
            # send vva gain packet
            serialPort.write(bytearray([2,vvaValue]))
            time.sleep(.1)
            w = serialPort.in_waiting
            temp = int.from_bytes(serialPort.read(w),"little")
            if (temp == vvaValue):
                print("VVA gain set")
        # see if we need to log temp and current
        end = time.time()
        timeDiff = end-start
        if(timeDiff > loggingFreq):
            # need to log
            # send temp request flag
            start = loggingUpdate(serialPort)
    
    # shutdown cleanup
    # shutdown amp
    if (ampState == 1):
        print("shutting off amp")
        # send amp state toggle packet
        serialPort.write(bytearray([3,0]))
        time.sleep(.1)
        w = serialPort.in_waiting
        temp = int.from_bytes(serialPort.read(w),"little")
        if (temp == ampState):
            print("amp state set")
    # set gain to zero
    print("setting gain to zero")
    # send vva gain packet
    serialPort.write(bytearray([2,0]))
    time.sleep(.1)
    w = serialPort.in_waiting
    temp = int.from_bytes(serialPort.read(w),"little")
    if (temp == 0):
        print("VVA gain set")

    print("SH: exiting")
  
def userInterface():
    global ampToggleFlag
    global loggingToggleFlag
    global vvaFlag
    global shutdownFlag
    global loggingFreq
    global vvaValue
    global currValue
    global tempValue
    global ampState

    stopBool = True
    while stopBool:
        
        if (shutdownFlag == 1):
            stopBool = False
        time.sleep(.3)
        print("\n+++  USER INTERFACE  +++")
        print("========================")
        print("1: get system status")
        print("2: toggle logging")
        print("3: set logging frequency")
        print("4: set amp VVA value")
        print("5: toggle amp on/off")

        print("0: exit")
        print("========================\n")
        sel = int(input())

        if (sel == 1):
            # get stats
            print("+++ system status +++")
            print("temp: "+str(round(tempValue*.4882,2)))
            print("current: "+str(round(currValue*.00976,2)))
            print("VVA gain: "+str(vvaValue))
            print("amp state: "+str(ampState))
            print("logging state: "+str(loggingToggleFlag))
            print("logging freq: "+str(loggingFreq))
            print("DEBUG")
            print("temp raw: "+str(tempValue))
            print("temp volts: "+str(tempValue*.0048828))
            print("current raw: "+str(currValue))
            print("current volts: "+str(currValue*.0048828))


        elif (sel == 2):
            # toggle logging
            print("toggle logging")
            if (loggingToggleFlag == 0):
                loggingToggleFlag = 1
            else:
                loggingToggleFlag = 0
        elif (sel == 3):
            # set logging frequency
            print("input new log freq")
            temp = int(input())
            if (temp > 10 or temp < 1):
                print("error: logging freq invalid (1-10)")
                temp = 5
            loggingFreq = temp
        elif (sel == 4):
            # set amp vva vlaue
            print("set amp vva")
            temp = int(input())
            vvaFlag = 1
            if (temp > 100 or temp < 0):
                print("error: VVA gain invald (0-100)")
                temp = 0
            vvaValue = temp
        elif (sel == 5):
            # toggle amp on/off
            print("toggle amp")
            ampToggleFlag = 1
        elif (sel == 0):
            # exit
            print("exiting")
            shutdownFlag = 1
            break
        else:
            # bad entry
            print("ERROR: invalid selection")
    print("UI: exiting")

def main():
    # main function
    # serial port vars
    comPort = "/dev/ttyUSB0"
    baudRate = 9600

    # first, check that we can talk with the arduino
    # we expect to receive serial data on start: <good morning, dave>
    print("starting serial connect: "+str(comPort))
    serialPort = serial.Serial(comPort, baudRate, timeout=0) # 1/timeout is the frequency at which the port is read
    bootBool = arduinoBootCheck(serialPort)
    if (bootBool == False):
        print("Error in serial comms")
        sys.exit()
    else:
        print("serial comms connected\n")
    # make the log file
    logFile = open("logfile.txt", "a+")
    logFile.close()
    # start the serial handler thread
    sh = threading.Thread(target = serialHandler, args = (serialPort,))
    sh.start()
    # start the user interface thread
    ui = threading.Thread(target = userInterface(), args = ())
    ui.start()
    
    # wait for threads to finish
    sh.join()
    ui.join()
    print("main: threads joined, exiting")

if __name__ == '__main__':
    sys.exit(main())