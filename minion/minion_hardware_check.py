"""
check hardware
"""
print('executing minion.minion_hardware_check')

from PyQt5.QtCore import *
import serial
from serial import serialutil
from ctypes import *

class CheckHardware(QObject):
    def __init__(self):
        super(CheckHardware, self).__init__()
        self.check()

    def check(self):
        # check for hardware and set states

        try:
            counter = serial.Serial('/dev/ttyUSB1', timeout=1)
            counter.close()
            hardware_counter = True
        except serialutil.SerialException:
            hardware_counter = False
            print('counter not connected at /dev/ttyUSB1')

        try:
            laser = serial.Serial('/dev/ttyUSB2', timeout=1)
            laser.close()
            hardware_laser = True
        except serialutil.SerialException:
            hardware_laser = False
            print('laser not connected at /dev/ttyUSB2')

        try:
            CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
            # stagelib = CDLL('/usr/local/lib/libmadlib.so', 1)
            stagelib = CDLL('/usr/lib/libmadlib.so', 1)
            stage = stagelib.MCL_InitHandle()
            if stage == 0:
                raise ValueError('no stage found')
            stagelib.MCL_ReleaseHandle(stage)
            hardware_stage = True
        except:
            hardware_stage = False
            print('could not connect stage - either no stage found or issue with libraries')

        return hardware_counter, hardware_laser, hardware_stage
