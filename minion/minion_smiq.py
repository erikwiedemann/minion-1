import gpib
import numpy as np
import time
from PyQt5.QtCore import *


class MinionSmiq06b(QObject):
    def __init__(self, parent=None):
        super(MinionSmiq06b, self).__init__(parent)

    def __del__(self):
        print('smiq disconnected')
        gpib.write(self.smiq, '*RST')
        gpib.close(self.smiq)

    def disconnect(self):
        gpib.write(self.smiq, '*RST')
        gpib.close(self.smiq)
        print('smiq disconnected')

    def connect(self):
        self.smiq = gpib.find('smiq06b')
        gpib.write(self.smiq, '*RST')
        print('smiq connected')

    def output(self):
        gpib.write(self.smiq, ':OUTP?')
        return gpib.read(self.smiq, 256)

    def off(self):
        gpib.write(self.smiq, ':FREQ:MODE?')
        answer = gpib.read(self.smiq, 256)
        if answer == 'LIST':
            gpib.write(self.smiq, ':FREQ:MODE CW')
        gpib.write(self.smiq, ':OUTP OFF')
        gpib.write(self.smiq, '*WAI')

    def on(self):
        gpib.write(self.smiq, ':OUTP ON')
        gpib.write(self.smiq, '*WAI')

    def power(self, power=None):
        if power != None:
            print(power)
            gpib.write(self.smiq, ':POW '+str(power))
            gpib.write(self.smiq, ':POW?')
        return float(gpib.read(self.smiq, 256))

    def freq(self, freq=None):
        if freq != None:
            gpib.write(self.smiq, ':FREQ '+str(freq))
            gpib.write(self.smiq, '*WAI')
            gpib.write(self.smiq, ':FREQ?')
        return float(gpib.read(self.smiq, 256))

    def cw(self, freq=None, power=None):
        gpib.write(self.smiq, ':FREQ:MODE CW')
        if freq != None:
            gpib.write(self.smiq, ':FREQ '+str(freq))
        if power != None:
            gpib.write(self.smiq, ':POW '+str(power))


    def setlist(self, freqlist, powerlist, dt=0.010, adt=0.5):
        freqliststring = ', '.join(np.char.mod('%d', freqlist))
        powerliststring = 'dBm, '.join(np.char.mod('%d', powerlist))
        print(freqliststring)
        print(powerliststring)

        gpib.write(self.smiq, ':FREQ:MODE CW')
        gpib.write(self.smiq, ':FREQ '+str(np.mean(freqlist)))
        gpib.write(self.smiq, ':POW '+str(np.mean(powerlist))+'dBm')
        gpib.write(self.smiq, '*WAI')

        gpib.write(self.smiq, ':LIST:DELETE:ALL')
        gpib.write(self.smiq, ':LIST:SELECT \'MINION\'')
        gpib.write(self.smiq, ':TRIG1:LIST:SOURCE SINGLE')  # single trigger an liste
        gpib.write(self.smiq, ':LIST:MODE AUTO')  # liste einmal durchfahren
        gpib.write(self.smiq, ':LIST:DWELL '+str(dt+adt))

        gpib.write(self.smiq, ':LIST:FREQ '+freqliststring)
        gpib.write(self.smiq, ':LIST:POW '+powerliststring)

    def liston(self):
        gpib.write(self.smiq, ':OUTP ON')
        gpib.write(self.smiq, ':LIST:LEARN')
        gpib.write(self.smiq, ':FREQ:MODE LIST')
        time.sleep(1)

    def listrun(self):
        gpib.write(self.smiq, ':TRIG:LIST')  # startet








