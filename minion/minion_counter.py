import serial
import numpy as np
import time
from PyQt5.QtCore import *

class MinionCounter(QObject):
    def __init__(self, parent=None):
        super(MinionCounter, self).__init__(parent)
        self.counter = serial.Serial('/dev/ttyUSB2', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        self.fpgaclock = 80*10**6  # in Hz
        self.counttime = 0.005
        print('\t counter connected')

    def __del__(self):
        self.counter.close()
        print(self.counter)

    def setnumbercountingbins(self, numbins):
        self.numbins = numbins
        counterbins = numbins.to_bytes(2, byteorder='little')
        self.counter.write(b'B'+counterbins)

    def getcurrentbinpos(self):
        self.counter.write(b'a')
        binposbyte = self.counter.read(2)
        return int.from_bytes(binposbyte, byteorder='little')

    def getnumbercountingbins(self):
        self.counter.write(b'b')
        self.numbins = int.from_bytes(self.counter.read(2), byteorder='little')
        return self.numbins

    def readcountingbins(self):
        self.counter.write(b'd')  #ReadTriggeredCountingData
        time.sleep(0.5)
        countingbindata = self.counter.read(self.numbins*3*2) #2=two apds, res=numbins
        countbinlist = [countingbindata[i:i+6] for i in range(0, len(countingbindata), 6)]
        apd1 = [bin[:3] for bin in countbinlist]
        apd2 = [bin[-3:] for bin in countbinlist]
        apd1_count = np.array([int.from_bytes(count1, byteorder='little') for count1 in apd1])
        apd2_count = np.array([int.from_bytes(count2, byteorder='little') for count2 in apd2])
        return apd1_count, apd2_count, apd1_count+apd2_count

    def settriggermasks(self, mask=8, invertedmask=8):
        self.counter.write(b'M'+mask.to_bytes(1, byteorder='little'))
        self.counter.write(b'Q'+invertedmask.to_bytes(1, byteorder='little'))

    def setcountingbinrepetitions(self, rep=1):
        self.counter.write(b'K'+rep.to_bytes(2, byteorder='little'))

    def setsplittriggeredbins(self, split=0):
        self.counter.write(b'F'+split.to_bytes(1, byteorder='little'))
        print('split byte:', b'F'+split.to_bytes(1, byteorder='little'))

    def getsplittriggeredbins(self):
        pass  # not yet there

    def resettriggerbins(self):
        self.counter.write(b'0')

    def enabletriggeredcounting(self):
        self.counter.write(b'R')

    def disabletriggeredcounting(self):
        self.counter.write(b'r')

    def setcountingtime(self, counttime=0.005):
        self.counttime = counttime
        counttime_bytes = (int(counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
        self.counter.write(b'T'+counttime_bytes)  # set counttime at fpga

    def checkcounttime(self):
        self.counter.write(b't')  # check counttime
        check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
        return check_counttime

    def count(self):
        self.counter.write(b'C')
        time.sleep(self.counttime*1.05)
        answer = self.counter.read(8)
        apd1 = answer[:4]
        apd2 = answer[4:]
        apd1_count = int.from_bytes(apd1, byteorder='little')/self.counttime  # in cps
        apd2_count = int.from_bytes(apd2, byteorder='little')/self.counttime  # in cps
        return [apd1_count, apd2_count, apd1_count + apd2_count]

