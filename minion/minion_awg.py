import gpib
import numpy as np
import time
from PyQt5.QtCore import *


class MinionAwg520(QObject):
    def __init__(self, parent=None):
        super(MinionAwg520, self).__init__(parent)
        self.awg = gpib.find('awg520')
        gpib.write(self.awg, '*RST')
        gpib.write(self.awg,'DISPLAY:BRIGHTNESS 0.1')
        gpib.write(self.awg,':ROSCILLATOR:SOURCE EXTERNAL')
        gpib.write(self.awg,'SOURCE1:MARKER1:DELAY 0')
        gpib.write(self.awg,'SOURCE1:MARKER1:VOLTAGE:LOW 0')
        gpib.write(self.awg,'SOURCE1:MARKER1:VOLTAGE:HIGH 1')
        gpib.write(self.awg,'SOURCE1:MARKER2:DELAY 0')
        gpib.write(self.awg,'SOURCE1:MARKER2:VOLTAGE:LOW 0')
        gpib.write(self.awg,'SOURCE1:MARKER2:VOLTAGE:HIGH 2')
        gpib.write(self.awg,'SOURCE2:MARKER1:DELAY 0')
        gpib.write(self.awg,'SOURCE2:MARKER1:VOLTAGE:LOW 0')
        gpib.write(self.awg,'SOURCE2:MARKER1:VOLTAGE:HIGH 1')
        gpib.write(self.awg,'SOURCE2:MARKER2:DELAY 0')
        gpib.write(self.awg,'SOURCE2:MARKER2:VOLTAGE:LOW 0')
        gpib.write(self.awg,'SOURCE2:MARKER2:VOLTAGE:HIGH 2')

    def __del__(self):
        gpib.write(self.awg, '*RST')
        gpib.close(self.awg)

    def laserandmicrowave(self):
        pass

