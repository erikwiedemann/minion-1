import serial
import numpy as np
import time
from PyQt5.QtCore import *

class MinionCounter(QObject):
    def __init__(self, parent=None):
        super(MinionCounter, self).__init__(parent)
        self.counter = serial.Serial('/dev/ttyUSB2', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        self.fpgaclock = 80*10**6  # in Hz
        print('\t counter connected')

    def __del__(self):
        self.counter.close()
        print(self.counter)

    def setcountingbins(self, numbins):
        self.numbins = numbins
        counterbins = numbins.to_bytes(2, byteorder='little')
        self.counter.write(b'B'+counterbins)

    def readcountingbins(self, ):
        self.counter.write(b'd')  #ReadTriggeredCountingData
        time.sleep(0.1)
        self.counter.read(self.numbins*3*2)  #2=two apds, res=numbins, 3=? - why not 4?

    def settriggermasks(self, mask=8, invertedmask=8):
        self.counter.write(b'M'+mask.to_bytes(1, byteorder='little'))
        self.counter.write(b'Q'+invertedmask.to_bytes(1, byteorder='little'))

    def setcountingbinrepetitions(self, rep=1):
        self.counter.write(b'K'+rep.to_bytes(4, byteorder='little'))

    def resettriggerbins(self):
        self.counter.write(b'0')

    def enabletriggeredcounting(self):
        self.counter.write(b'R')

    def disabletriggeredcounting(self):
        self.counter.write(b'r')

    def setcountingtime(self, counttime=0.005):
        counttime_bytes = (int(counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
        self.counter.write(b'T'+counttime_bytes)  # set counttime at fpga

    def checkcounttime(self):
        self.counter.write(b't')  # check counttime
        check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
        return check_counttime



