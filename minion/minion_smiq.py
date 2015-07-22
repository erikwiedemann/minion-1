import gpib
import numpy as np
import time
from PyQt5.QtCore import *


class MinionSmiq06b(QObject):
    def __init__(self, parent=None):
        super(MinionSmiq06b, self).__init__(parent)
        self.smiq = gpib.find('smiq06b')
        gpib.write(self.smiq, '*RST')

    def __del__(self):
        gpib.write(self.smiq, '*RST')
        gpib.close(self.smiq)

    def output(self):
        return gpib.ask(self.smiq, ':OUTP?')

    def off(self):
        if gpib.ask(self.smiq, ':FREQ:MODE?') == 'LIST':
            gpib.write(self.smiq, ':FREQ:MODE CW')
        gpib.write(self.smiq, ':OUTP OFF')
        gpib.write(self.smiq, '*WAI')

    def on(self):
        gpib.write(self.smiq, ':OUTP ON')
        gpib.write(self.smiq, '*WAI')

    def power(self, power=None):
        if power != None:
            gpib.write(self.smiq, ':POW %f' % power)
        return float(gpib.ask(self.smiq, ':POW?'))

    def freq(self, f=None):
        if f != None:
            gpib.write(self.smiq, ':FREQ %e' % f)
        return float(gpib.ask(self.smiq, ':FREQ?'))

    def cw(self, freq=None, power=None):
        gpib.write(self.smiq, ':FREQ:MODE CW')
        if freq != None:
            gpib.write(self.smiq, ':FREQ %e' % freq)
        if power != None:
            gpib.write(self.smiq, ':POW %f' % power)


    def setlist(self, freqlist, powerlist, dt=0.010, adt=0.001):
        freqliststring = ', '.join(np.char.mod('%d', freqlist))
        powerliststring = 'dBm, '.join(np.char.mod('%d', powerlist))

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
        gpib.write(self.smiq, '*WAI')
        gpib.write(self.smiq, ':LIST:LEARN')
        gpib.write(self.smiq, '*WAI')
        time.sleep(1)

        gpib.write(self.smiq, ':FREQ:MODE LIST')







