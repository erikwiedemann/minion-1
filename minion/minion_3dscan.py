"""
3dscan module
"""
print('executing minion.minion_3dscan')

import os
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import matplotlib as mpl
import serial
from ctypes import *
mpl.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Minion3dscanUI(QWidget):
    def __init__(self, parent=None):
        super(Minion3dscanUI, self).__init__(parent)
        self.uisetup()

    def uisetup(self):
        self.volumescanstart = QPushButton('start scan')

        volumescanlayout = QGridLayout()
        volumescanlayout.addWidget(self.volumescanstart)

        volumescanlayout.setSpacing(2)
        self.setLayout(volumescanlayout)
