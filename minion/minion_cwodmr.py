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
from minion.minion_smiq import MinionSmiq06b as smiq


class MinionCwodmrUI(QWidget):
    def __init__(self, parent):
        super(MinionCwodmrUI, self).__init__(parent)
        self.parent = parent
        self.counter = self.parent.counter

        smiq.connect(smiq)

        self.frequency = 2.87*10**9  #Hz
        self.power = -20.
        self.modi = ['const', 'list']
        self.mode = 'const'
        self.cwodmrdata = np.zeros(100)
        self.freqlist = []
        self.powerlist = []

        self.uisetup()

    def __del__(self):
        smiq.disconnect(smiq)

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
        self.listtable.setColumnCount(4)
        self.listtable.setRowCount(1)
        self.listtable.setHorizontalHeaderLabels(('start[GHz]', 'stop[GHz]', 'points[#]', 'power[dBm]'))

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
        freq = self.freqtext.value()*10**9
        self.freq = smiq.freq(smiq, freq)

    def powerchanged(self):
        power = self.powertext.value()
        self.power = smiq.power(smiq, power)

    def modechange(self):
        pass

    def toggleoutput(self):
        if self.toggleoutputbutton.isChecked() is True:
            self.toggleoutputbutton.setStyleSheet("QPushButton {background-color: green;}")
            smiq.on(smiq)
        else:
            self.toggleoutputbutton.setStyleSheet("QPushButton {background-color: red;}")
            smiq.off(smiq)

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
        self.freqlist = []
        self.powerlist = []
        self.listdata = np.zeros((self.listtable.rowCount(), self.listtable.columnCount()))
        for i in range(self.listtable.rowCount()):
            for j in range(self.listtable.columnCount()):
                self.listdata[i, j] = float(self.listtable.item(i, j).text())
        for i in range(len(self.listdata)):
            list = self.listdata[i, :]
            self.freqlist.extend(np.array(np.linspace(list[0]*10**9, list[1]*10**9, int(list[2]))))
            self.powerlist.extend(np.ones(int(list[2]))*list[3])
        smiq.setlist(smiq, self.freqlist, self.powerlist)


    def startcwodmr(self):
        if self.startcwodmrbutton.isChecked() is True:
            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: green;}")
            fpgaclock = 80*10**6  # in Hz
            self.counter.write(b't')  # check counttime
            check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/fpgaclock
            print('counttime:', check_counttime)

            smiq.liston(smiq)
            time.sleep(1.5)

            self.counter.write(b'M'+(8).to_bytes(1, byteorder='little'))  #SetTriggerMask
            self.counter.write(b'Q'+(8).to_bytes(1, byteorder='little'))  #SetTriggerinvertedMask
            counterbins = (len(self.freqlist)).to_bytes(2, byteorder='little')
            self.counter.write(b'B'+counterbins)  #SetNumberOfTriggeredCountingBins
            self.counter.write(b'b')
            print('num bins:', int.from_bytes(self.counter.read(20), byteorder='little'))

            self.counter.write(b'K'+(1).to_bytes(2, byteorder='little'))  #SetTriggeredCountingBinRepetitions

            self.counter.write(b'0')  #ResetTriggeredCountingData
            self.counter.write(b'R')  #EnableTriggeredCounting



            for i in range(1):
                smiq.listrun(smiq)
                time.sleep(len(self.freqlist)*0.011+1)

                self.counter.write(b'd')  #ReadTriggeredCountingData
                time.sleep(0.1)
                print(len(self.freqlist))
                countingbindata = self.counter.read(len(self.freqlist)*3*2)  #2=two apds, res=numbins, 3=bytes per bin
                print(countingbindata)
                countbinlist = [countingbindata[i:i+6] for i in range(0, len(countingbindata), 6)]
                print(countbinlist)
                apd1 = [bin[:3] for bin in countbinlist]
                print(apd1)

                apd2 = [bin[-3:] for bin in countbinlist]
                print(apd2)
                apd1_count = np.array([int.from_bytes(count1, byteorder='little') for count1 in apd1])
                apd2_count = np.array([int.from_bytes(count2, byteorder='little') for count2 in apd2])
                print(apd1_count)
                print(apd2_count)
                test = apd1_count+apd2_count
                print(test)

            smiq.cw(smiq, 2.87*10**9, -20)
            # disable triggered counting
            self.counter.write(b'r')  #DisableTriggeredCounting


            time.sleep(0.1)
            counttime_bytes = (int(0.005*fpgaclock)).to_bytes(4, byteorder='little') # TODO - change to current counttime
            self.counter.write(b'T'+counttime_bytes)  # set counttime at fpga
            time.sleep(0.1)
            self.counter.write(b't')  # check counttime
            check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/fpgaclock
            print('counttime:', check_counttime)

        else:
            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: red;}")