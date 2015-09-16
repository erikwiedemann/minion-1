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
        # hardware_counter = True
        # hardware_laser = True
        # hardware_stage = True

        # check for hardware and set states
        try:
            self.counter = serial.Serial('/dev/ttyUSB3', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10) #Lattice Lattice FTUSB Interface Cable
            self.fpgaclock = 80*10**6  # in Hz
            self.counttime_bytes = (int(0.005*self.fpgaclock)).to_bytes(4, byteorder='little')
            self.counter.write(b'T'+self.counttime_bytes)  # set counttime at fpga
            self.counter.write(b't')  # check counttime
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
            print('\t fpga counttime:', self.check_counttime)
            print('\t counter connected')
            hardware_counter = True
        except serialutil.SerialException:
            self.counter = []
            hardware_counter = False
            print('counter not connected at /dev/ttyUSB2')

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



        return hardware_counter, self.counter, hardware_laser, self.laser, hardware_stage, self.stage, self.stagelib
