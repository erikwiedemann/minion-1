"""
check hardware
"""
print('executing minion.minion_hardware_check')

from PyQt5.QtCore import *
import serial
import serial.tools.list_ports
from serial import serialutil
from ctypes import *
import gpib

class CheckHardware(QObject):
    def __init__(self):
        super(CheckHardware, self).__init__()

    def check(self):
        portlist = serial.tools.list_ports.comports()
        # TODO - find hardware and hand correct port over
        # hardware_counter = False
        # hardware_laser = False
        # hardware_stage = False
        hardware_counter = True
        # hardware_laser = True
        # hardware_stage = True

        # check for hardware and set states

        try:
            self.laser = serial.Serial('/dev/ttyUSB0', baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
            hardware_laser = True
        except serialutil.SerialException:
            self.laser = []
            hardware_laser = False
            print('laser not connected at /dev/ttyUSB2')

        try:
            CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
            self.stagelib = CDLL('libmadlib.so', 1)
            self.stage = self.stagelib.MCL_InitHandleOrGetExisting()
            if self.stage == 0:
                hardware_stage = False
                self.stage = []
                self.stagelib = []
                print('cound not get stage handle')
            else:
                hardware_stage = True
        except:
            hardware_stage = False
            self.stage = []
            self.stagelib = []
            print('could not connect stage - either no stage found or issue with libraries')



        return hardware_counter, hardware_laser, self.laser, hardware_stage, self.stage, self.stagelib
