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
import gpib


class MinionCwodmrUI(QWidget):
    continueodmr = pyqtSignal()
    def __init__(self, parent):
        super(MinionCwodmrUI, self).__init__(parent)
        self.parent = parent
        self.counter = self.parent.counter

        smiq.connect(smiq)
        self.measurementrunning = False

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

        self.startcwodmrbutton = QPushButton('start sweep')
        self.startcwodmrbutton.setCheckable(True)
        self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: red;}")
        self.startcwodmrbutton.toggled.connect(self.startcwodmr)

        self.abortodmrsweepbutton = QPushButton('abort sweep')
        self.abortodmrsweepbutton.clicked.connect(self.abortodmrsweep)


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
        cwodmrlayout.addWidget(self.abortodmrsweepbutton)

        self.setLayout(cwodmrlayout)

    def abortodmrsweep(self):
        try:
            print('aborting sweep')
            self.cwODMRaquisition.stop()
            self.cwODMRaquisitionthread.quit()
        except:
            print('no sweep running')

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
                self.listdata[i, j] = float(self.listtable.item(i, j).text().replace(',', '.'))
        for i in range(len(self.listdata)):
            list = self.listdata[i, :]
            self.freqlist.extend(np.array(np.linspace(list[0]*10**9, list[1]*10**9, int(list[2]))))
            self.powerlist.extend(np.ones(int(list[2]))*list[3])
        self.power = self.powerlist[0]
        print('list updated')
        # smiq.setlist(smiq, self.freqlist, self.powerlist)

    @pyqtSlot(np.ndarray)
    def updateODMRdata(self, odmrupdate):
        self.cwodmrdataplot += odmrupdate
        if np.size(self.cwodmrdata, 0) == 1:
            self.cwodmrdata = odmrupdate
            self.cwodmraxes.plot(self.freqlist[:-1], self.cwodmrdataplot[:-1])
        else:
            self.cwodmrdata = np.vstack((self.cwodmrdata, odmrupdate))
            self.cwodmraxes.plot(self.freqlist[:-1], self.cwodmrdataplot[:-1])

        # self.cwodmraxes.relim()
        # self.cwodmraxes.autoscale_view()
        self.cwodmrcanvas.draw()

    @pyqtSlot()
    def continueodmraquisition(self):
        self.continueodmr.emit()

    def startcwodmr(self):
        if self.startcwodmrbutton.isChecked() is True:
            if self.parent.hardware_stage is True and self.parent.hardware_counter is True:
                self.measurementrunning = True
                self.cwodmrdata = np.zeros(len(self.freqlist))
                self.cwodmrdataplot = np.zeros(len(self.freqlist))
                self.cwODMRaquisition = MinionODMRAquisition(self.parent.fpga, self.parent.confocalwidget.xpos, self.parent.confocalwidget.ypos, self.parent.confocalwidget.zpos, self.power, self.freqlist)
                self.cwODMRaquisitionthread = QThread(self, objectName='workerThread')
                self.cwODMRaquisition.moveToThread(self.cwODMRaquisitionthread)
                self.cwODMRaquisition.finished.connect(self.cwODMRaquisitionthread.quit)
                self.cwODMRaquisition.track.connect(self.parent.trackerwidget.findmaxclicked)
                self.cwODMRaquisition.update.connect(self.updateODMRdata)
                self.continueodmr.connect(self.cwODMRaquisition.trackfinished)
                self.cwODMRaquisitionthread.started.connect(self.cwODMRaquisition.longrun)
                self.cwODMRaquisitionthread.finished.connect(self.cwODMRaquisitionthread.deleteLater)
                # self.findmax.update.connect(self.updatefindcentermaps)

                self.cwODMRaquisitionthread.start()

            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: green;}")



            # self.parent.fpga.settriggermasks(mask=8, invertedmask=8)  # SetTriggerMask + SetTriggerinvertedMask
            # self.parent.fpga.setnumbercountingbins(len(self.freqlist))  # SetNumberOfTriggeredCountingBins
            # print('num bins:', self.parent.fpga.getnumbercountingbins())
            #
            # self.parent.fpga.setcountingbinrepetitions(1)  # SetTriggeredCountingBinRepetitions
            # self.parent.fpga.setsplittriggeredbins(0)  # SetSplitTriggeredCountingBins
            # smiq.liston(smiq)
            # time.sleep(2)
            # self.parent.fpga.resettriggerbins()  #ResetTriggeredCountingData
            # time.sleep(0.001)
            # self.parent.fpga.enabletriggeredcounting()  #EnableTriggeredCounting
            # time.sleep(0.001)
            # self.cwodmrdata = np.zeros(len(self.freqlist))
            # # for i in range(2):
            # smiq.listrun(smiq)
            # time.sleep(len(self.freqlist)*0.011*2)
            # print('binpos:', self.parent.fpga.getcurrentbinpos())
            # print('counttime:', self.parent.fpga.checkcounttime())
            # smiq.listrun(smiq)
            # apd1, apd2, apd_sum = self.parent.fpga.readcountingbins()
            # self.cwodmrdata += apd_sum
            # print(self.cwodmrdata)
            # # time.sleep(0.5)
            # # smiq.cw(smiq, 2.87*10**9, -20)
            # # disable triggered counting
            #
            # # self.counter.write(b'r')  #DisableTriggeredCounting
            # # self.counter.write(b'0')  #ResetTriggeredCountingData
            #
            # check_counttime = self.parent.fpga.checkcounttime()  # check counttime
            # print('counttime:', check_counttime)
            #
            # self.counter.write(b'r')  #DisableTriggeredCounting

            # TODO - remove below and fix above
            # dont use list mode and sweep over cw modes


        else:
            self.startcwodmrbutton.toggle()
            self.startcwodmrbutton.setStyleSheet("QPushButton {background-color: red;}")




class MinionODMRAquisition(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray)
    track = pyqtSignal()
    goon = pyqtSignal()

    def __init__(self, fpga, xpos, ypos, zpos, power, freqlist,  parent=None):  # remove data as not needed
        super(MinionODMRAquisition, self).__init__(parent)
        self.fpga = fpga
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.power = power
        self.freqlist = freqlist
        self.run = True
        self.pause = False
        self.abort = False
        self._isRunning = True

    def stop(self):
        self._isRunning = False
        self.abort = True

        self.trackertimer.stop()
        self.finished.emit()

    def starttrack(self):
        self.pause = True
        print('pause for tracking')
        time.sleep(0.05)
        self.track.emit()

    @pyqtSlot()
    def trackfinished(self):
        self.pause = False

    def longrun(self):
        self.contexttrackertimer = QTimer()
        # self.contexttrackertimer.setInterval(120*10**3)  # ms
        # self.contexttrackertimer.timeout.connect(self.starttrack)
        # self.contexttrackertimer.start()

        self.fpga.setcountingtime(0.01)  # set counttime at fpga
        time.sleep(0.001)
        check_counttime = self.fpga.checkcounttime()  # check counttime
        print('counttime:', check_counttime)
        print("[%s] start cwODMR scan" % QThread.currentThread().objectName())

        self.cwodmrdata = np.zeros(len(self.freqlist))

        smiq.on(smiq)
        smiq.setpower(smiq, self.power)

        while self.run is True:
            for f in range(len(self.freqlist)):
                while self.pause is True:
                    print('pause')
                    time.sleep(1)
                smiq.setfreq(smiq, self.freqlist[f])
                time.sleep(0.003)
                apd1, apd2, apd_sum = self.fpga.count()
                self.cwodmrdata[f-1] = apd_sum*0.01
                if f%len(self.freqlist) == 0:
                    self.update.emit(self.cwodmrdata)
            if self.abort is True:
                self.run = False

        smiq.off(smiq)

        print('done')