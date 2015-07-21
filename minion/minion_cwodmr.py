print('executing minion.minion_cwodmr')
import numpy as np
import scipy.optimize as opt
import matplotlib as mpl
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
import scipy.ndimage as ndi
import scipy.signal as sig
import time
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from ctypes import *
import serial



class MinionCwodmrUI(QWidget):
    def __init__(self, parent):
        super(MinionCwodmrUI, self).__init__(parent)
        self.parent = parent

        self.uisetup()

    def uisetup(self):
        self.button = QPushButton('test')

        cwodmrlayout = QGridLayout()
        cwodmrlayout.addWidget(self.button)

        self.setLayout(cwodmrlayout)