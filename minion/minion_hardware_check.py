"""
check hardware
"""
print('executing minion.minion_hardware_check')

from PyQt5.QtCore import *
import serial

class CheckHardware(QObject):
    def __init__(self):
        super(CheckHardware, self).__init__()

    def check(self):
        # check for hardware and set states
        print('checking available hardware:')

        # TODO - check for confocal hardware with if then
        self.confocal_status = False
        print('\tconfocal not available')

        # TODO - check for trace hardware with if then
        self.trace_status = False
        print('\ttrace not available')
        return self.confocal_status,
