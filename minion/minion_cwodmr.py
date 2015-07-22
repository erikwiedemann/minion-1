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
        self.frequency = 2.87*10**9  #Hz

        self.uisetup()

    def uisetup(self):
        self.cwodmrfigure = Figure()
        self.cwodmrcanvas = FigureCanvas(self.cwodmrfigure)
        self.cwodmrcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cwodmrcanvas.setMinimumSize(50, 50)
        self.cwodmrtoolbar = NavigationToolbar(self.cwodmrcanvas, self)
        self.cwodmraxes = self.cwodmrfigure.add_subplot(111)
        self.cwodmraxes.hold(False)

        self.freqlabel = QLabel('Frequency [GHz]')
        self.freqtext = QDoubleSpinBox()
        self.freqtext.setRange(0, 6)
        self.freqtext.setValue(self.frequency/(1*10**9))
        self.freqtext.editingFinished.connect(self.freqchanged)






        # LAYOUT
        self.button = QPushButton('test')

        cwodmrlayout = QGridLayout()
        cwodmrlayout.addWidget(self.button)

        self.setLayout(cwodmrlayout)

    def freqchanged(self):
        pass