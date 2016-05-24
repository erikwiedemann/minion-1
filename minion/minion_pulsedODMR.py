print('executing minion.minion_pulsed_ODMR')

import numpy as np
import sys
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
#from minion.minion_smiq import MinionSmiq06b as smiq
#import gpib

class MinionPulsedODMR(QWidget):
    def __init__(self, parent=None):
        super(MinionPulsedODMR, self).__init__(parent)
        self.parent = parent

        self.initUI()

    def initUI(self):

        # -------- create ODMR display ---------------------------------------------------------------------------------

        self.pulsedodmrfigure = Figure()
        self.pulsedodmrcanvas = FigureCanvas(self.pulsedodmrfigure)
        self.pulsedodmrcanvas.setPolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pulsedodmrcanvas.setMinimumSize(50, 50)
        self.pulsedodmrtoolbar = NavigationToolbar(self.pulsedodmrcanvas, self)
        self.pulsedodmraxes = self.pulsedodmrfigure.add_subplot(111)
        self.pulsedodmraxes.hold(False)

        # -------- create control panel --------------------------------------------------------------------------------

        self.freqlabel = QLabel('Frequency [GHz')

        self.powerlabel = QLabel('Power [dBm]')

        self.modeselectlabel = QLabel('mode:')

        self.startmeasurementbutton = QPushButton('start')
        self.startmeasurementbutton.clicked.connect(self.startmeasurement)
        self.abortmeasurementbutton = QPushButton('abort')
        self.abortmeasurementbutton.clicked.connect(self.abortmeasurement)

        # -------- create layout ---------------------------------------------------------------------------------------

        # display layout

        displaylayout = QHBoxLayout()
        displaylayout.addWidget(self.pulsedodmrcanvas)
        displaylayout.addWidget(self.pulsedodmrtoolbar)

        # control layout

        # start stop layout
        controlmeasurementlayout = QHBoxLayout()
        controlmeasurementlayout.addWidget(self.startmeasurementbutton)
        controlmeasurementlayout.addWidget(self.abortmeasurementbutton)

        # create main layout and show it
        layout = QGridLayout()
        layout.addLayout(displaylayout, 0, 0)
        layout.addLayout(controlmeasurementlayout, 1, 0)

        self.setLayout(layout)
        self.setGeometry(1500, 200, 800, 300)
        self.setWindowTitle('Message box')
        self.show()

    def startmeasurement(self):
        print('measurement started')

    def abortmeasurement(self):
        print('abort measurement')
