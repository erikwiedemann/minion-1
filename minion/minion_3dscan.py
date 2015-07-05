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
import matplotlib.style as mplstyle
import serial
from ctypes import *

mpl.use("Qt5Agg")
mplstyle.use('ggplot')  # 'ggplot', 'dark_background', 'bmh', 'fivethirtyeight'

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Minion3dscanUI(QWidget):
    def __init__(self, parent=None):
        super(Minion3dscanUI, self).__init__(parent)
        self.xmin = 5.0
        self.xmax = 10.0
        self.xpos = 10
        self.ymin = 5.0
        self.ymax = 10.0
        self.ypos = 10
        self.zmin = 0.0
        self.zmax = 50.0
        self.zpos = 25.0
        self.xlim = 75.0
        self.ylim = 75.0
        self.zlim = 50.0

        self.resolution1 = 21
        self.resolution2 = 21
        self.resolution3 = 21
        self.mapdata = np.zeros((self.resolution1, self.resolution2, self.resolution3))
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        self.settlingtime = 0.01  # pos error about 10nm - 0.01 results in about 30 nm
        self.counttime = 0.005


        self.uisetup()

    def uisetup(self):
        self.volumescanstart = QPushButton('start scan')

        volumescanlayout = QGridLayout()
        volumescanlayout.addWidget(self.volumescanstart)

        volumescanlayout.setSpacing(2)
        self.setLayout(volumescanlayout)
