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
        self.power = -20.
        self.modi = ['const', 'list']
        self.mode = 'const'
        self.cwodmrdata = np.zeros(100)
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
        self.freqtext.setDecimals(6)
        self.freqtext.setSingleStep(0.001)
        self.freqtext.setValue(self.frequency/(1.*10**9))
        self.freqtext.editingFinished.connect(self.freqchanged)

        self.powerlabel = QLabel('Power [dBm]')
        self.powertext = QDoubleSpinBox()
        self.powertext.setRange(-140, 16)
        self.powertext.setDecimals(1)
        self.powertext.setValue(self.power)
        self.powertext.editingFinished.connect(self.powerchanged)

        self.modeselectlabel = QLabel('mode:')
        self.modeselect = QComboBox()
        self.modeselect.addItems(self.modi)
        self.modeselect.currentIndexChanged.connect(self.modechange)

        self.toggleoutputbutton = QPushButton('output on/off')
        self.toggleoutputbutton.setCheckable(True)
        self.toggleoutputbutton.setStyleSheet("QPushButton {background-color: red;}")
        self.toggleoutputbutton.toggled.connect(self.toggleoutput)

        self.listtable = QTableWidget()
        self.listtable.setColumnCount(3)
        self.listtable.setRowCount(1)
        self.listtable.setHorizontalHeaderLabels(('start[GHz]', 'stop[GHz]', 'points[#]'))

        self.listtableaddrowbutton = QPushButton('add row')
        self.listtableaddrowbutton.clicked.connect(self.listtableaddrow)
        self.listtableremoverowbutton = QPushButton('remove row')
        self.listtableremoverowbutton.clicked.connect(self.listtableremoverow)


        self.sendlisttosmiqbutton = QPushButton('send list')
        self.sendlisttosmiqbutton.clicked.connect(self.sendlisttosmiq)

        self.startcwodmrbutton = QPushButton('start list')
        self.startcwodmrbutton.setCheckable(True)
        self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: red;}")
        self.startcwodmrbutton.toggled.connect(self.startcwodmr)

        # LAYOUT

        cwodmrlayout = QGridLayout()
        cwodmrlayout.addWidget(self.cwodmrcanvas)
        cwodmrlayout.addWidget(self.cwodmrtoolbar)
        cwodmrlayout.addWidget(self.freqlabel)
        cwodmrlayout.addWidget(self.freqtext)
        cwodmrlayout.addWidget(self.powerlabel)
        cwodmrlayout.addWidget(self.powertext)
        cwodmrlayout.addWidget(self.modeselectlabel)
        cwodmrlayout.addWidget(self.modeselect)
        cwodmrlayout.addWidget(self.toggleoutputbutton)
        cwodmrlayout.addWidget(self.listtable)
        cwodmrlayout.addWidget(self.listtableaddrowbutton)
        cwodmrlayout.addWidget(self.listtableremoverowbutton)
        cwodmrlayout.addWidget(self.sendlisttosmiqbutton)
        cwodmrlayout.addWidget(self.startcwodmrbutton)

        self.setLayout(cwodmrlayout)

    def freqchanged(self):
        pass

    def powerchanged(self):
        pass

    def modechange(self):
        pass

    def toggleoutput(self):
        if self.toggleoutputbutton.isChecked() is True:
            self.toggleoutputbutton.setStyleSheet("QPushButton {background-color: green;}")

        else:
            self.toggleoutputbutton.setStyleSheet("QPushButton {background-color: red;}")

    def listtableaddrow(self):
        self.listtable.insertRow(self.listtable.rowCount()+1)
        self.listtable.setRowCount(self.listtable.rowCount()+1)


    def listtableremoverow(self):
        if self.listtable.rowCount() >= 2:
            self.listtable.removeRow(self.listtable.rowCount())
            self.listtable.setRowCount(self.listtable.rowCount()-1)
        else:
            pass

    def sendlisttosmiq(self):
        self.listdata = np.zeros((self.listtable.rowCount(), self.listtable.columnCount()))
        print(range(self.listtable.rowCount()))
        print(range(self.listtable.columnCount()))
        for i in range(self.listtable.rowCount()):
            for j in range(self.listtable.columnCount()):
                self.listdata[i, j] = float(self.listtable.item(i, j).text())

    def startcwodmr(self):
        if self.startcwodmrbutton.isChecked() is True:
            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: green;}")

        else:
            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: red;}")