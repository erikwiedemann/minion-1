"""
trace module
"""
print('executing minion.minion_trace')

import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import matplotlib as mpl
import serial

mpl.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MinionTraceUi(QWidget):
    def __init__(self, parent=None):
        super(MinionTraceUi, self).__init__(parent)
        # check hardware
        from minion.minion_hardware_check import CheckHardware
        self.hardware_counter, self.hardware_laser, self.hardware_stage = CheckHardware.check(CheckHardware)

        # set initial parameters
        self.status = True   # True - allowed to measure, False - forbidden to measure (e.g. if counter is needed elsewhere)
        self.tracemin = 0.
        self.tracemax = 60.
        self.tracelength = 60.
        self.counttime = 0.005
        self.updatetime = 0.5
        self.tracex = np.ndarray([0])
        self.tracey1 = np.ndarray([0])  # apd1
        self.tracey2 = np.ndarray([0])  # apd2
        self.traceysum = np.ndarray([0])

        if self.hardware_counter is True:
            self.counter = serial.Serial('/dev/ttyUSB1', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
            self.fpgaclock = 80*10**6  # in Hz
            self.counttime_bytes = (int(self.counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
            self.counter.write(b'T'+self.counttime_bytes)  # set counttime at fpga
            self.counter.write(b't')  # check counttime
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
            print('\t fpga counttime:', self.check_counttime)
        else:
            print('counter not found')

        self.uisetup()

    def uisetup(self):
        self.tracefigure = Figure()
        self.tracecanvas = FigureCanvas(self.tracefigure)
        self.toolbar = NavigationToolbar(self.tracecanvas, self)

        self.tracestartbutton = QPushButton('start')
        self.tracestartbutton.pressed.connect(self.tracestartclicked)
        self.tracestopbutton = QPushButton('stop')
        self.tracestopbutton.pressed.connect(self.tracestopclicked)

        self.traceminlabel = QLabel('t_min:')
        self.tracemintext = QDoubleSpinBox()
        self.tracemintext.setRange(0, 9999)
        self.tracemintext.setValue(int(self.tracemin))
        self.tracemintext.editingFinished.connect(self.updatetracesetting)

        self.tracemaxlabel = QLabel('t_max:')
        self.tracemaxtext = QDoubleSpinBox()
        self.tracemaxtext.setRange(0, 9999)
        self.tracemaxtext.setValue(int(self.tracemax))
        self.tracemaxtext.editingFinished.connect(self.updatetracesetting)

        self.tracelengthlabel = QLabel('dt:')
        self.tracelengthtext = QDoubleSpinBox()
        self.tracelengthtext.setRange(0, 9999)
        self.tracelengthtext.setDecimals(2)
        self.tracelengthtext.setValue(self.tracelength)
        self.tracelengthtext.editingFinished.connect(self.updatetracesetting)

        self.updatetimelabel = QLabel('updatetime [s]:')
        self.updatetimetext = QDoubleSpinBox()
        self.updatetimetext.setRange(0, 100)
        self.updatetimetext.setDecimals(2)
        self.updatetimetext.setValue(self.updatetime)
        self.updatetimetext.editingFinished.connect(self.tracetimechanged)

        self.counttimelabel = QLabel('counttime [ms]:')
        self.counttimetext = QDoubleSpinBox()
        self.counttimetext.setRange(0, 1000)
        self.counttimetext.setValue(int(self.counttime*1000))
        self.counttimetext.editingFinished.connect(self.tracetimechanged)

        self.traceapd1check = QCheckBox('apd1')
        self.traceapd1check.stateChanged.connect(self.checkboxupdate)
        self.traceapd2check = QCheckBox('apd2')
        self.traceapd2check.stateChanged.connect(self.checkboxupdate)
        self.traceapdsumcheck = QCheckBox('sum')
        self.traceapdsumcheck.toggle()
        self.traceapdsumcheck.stateChanged.connect(self.checkboxupdate)

        # create layout
        trace_layout = QGridLayout()
        trace_layout.addWidget(self.tracecanvas, 0, 0, 5, 10)
        trace_layout.addWidget(self.toolbar, 5, 0, 1, 10)
        trace_layout.addWidget(self.tracelengthlabel, 6, 0, 1, 1)
        trace_layout.addWidget(self.tracelengthtext, 6, 1, 1, 1)

        trace_layout.addWidget(self.traceapd1check, 6, 2, 1, 1)
        trace_layout.addWidget(self.traceapd2check, 6, 3, 1, 1)
        trace_layout.addWidget(self.traceapdsumcheck, 6, 4, 1, 1)

        trace_layout.addWidget(self.traceminlabel, 7, 0, 1, 1)
        trace_layout.addWidget(self.tracemintext, 7, 1, 1, 1)
        trace_layout.addWidget(self.tracemaxlabel, 7, 2, 1, 1)
        trace_layout.addWidget(self.tracemaxtext, 7, 3, 1, 1)

        trace_layout.addWidget(self.counttimelabel, 8, 0, 1, 1)
        trace_layout.addWidget(self.counttimetext, 8, 1, 1, 1)
        trace_layout.addWidget(self.updatetimelabel, 8, 2, 1, 1)
        trace_layout.addWidget(self.updatetimetext, 8, 3, 1, 1)

        trace_layout.addWidget(self.tracestartbutton, 9, 0)
        trace_layout.addWidget(self.tracestopbutton, 9, 1)

        trace_layout.setSpacing(2)
        self.setLayout(trace_layout)

    def tracetimechanged(self):
        self.counttime = self.counttimetext.value()/1000.
        self.updatetime = self.updatetimetext.value()

        if self.hardware_counter is True:
            self.fpgaclock = 80*10**6  # in Hz
            self.counttime_bytes = (int(self.counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
            self.counter.write(b'T'+self.counttime_bytes)  # set counttime at fpga
            self.counter.write(b't')  # check counttime
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
            print('\t fpga counttime:', self.check_counttime)
        print('counttime:', self.counttime)

    def checkboxupdate(self):
        if len(self.tracex) > 0:
            if self.traceapd1check.isChecked() is True:
                self.line1.set_marker('.')
            else:
                self.line1.set_marker('None')

            if self.traceapd2check.isChecked() is True:
                self.line2.set_marker('.')
            else:
                self.line2.set_marker('None')

            if self.traceapdsumcheck.isChecked() is True:
                self.line3.set_marker('.')
            else:
                self.line3.set_marker('None')
            self.updatetraceplot([], [], [], 1)

    def tracestartclicked(self):
        if self.status is True and self.hardware_counter is True:
            print("[%s] start trace" % QThread.currentThread().objectName())
            self.tracex = np.ndarray([0])
            self.tracey1 = np.ndarray([0])  # apd1
            self.tracey2 = np.ndarray([0])  # apd2
            self.traceysum = np.ndarray([0])
            self.tracefigure.clear()
            self.traceaxes = self.tracefigure.add_subplot(111)
            self.line1, = self.traceaxes.plot(self.tracex, self.tracey1, '.')
            self.line2, = self.traceaxes.plot(self.tracex, self.tracey2, '.')
            self.line3, = self.traceaxes.plot(self.tracex, self.traceysum, '.')
            self.checkboxupdate()
            self.traceaxes.set_autoscaley_on(True)
            self.tracefigure.canvas.draw()
            self.traceaxes.grid()

            self.traceaquisition = MinionTraceAquisition(self.counttime, self.updatetime)
            self.tracethread = QThread(self, objectName='TraceThread')
            self.traceaquisition.moveToThread(self.tracethread)
            self.traceaquisition.tracestop.connect(self.tracethread.quit)

            self.tracethread.started.connect(self.traceaquisition.longrun)
            self.tracethread.finished.connect(self.tracethread.deleteLater)
            self.traceaquisition.updatetrace.connect(self.updatetraceplot)
            self.tracethread.start()

    def tracestopclicked(self):
        # TODO - look if the "ckeck if thread is running" works
        try:
            print('stop trace')
            self.traceaquisition.stop()
            self.tracethread.quit()
        except:
            print('no trace running')

    def updatetracesetting(self):
        self.tracemin = np.round(self.tracemintext.value(), decimals=2)
        self.tracemax = np.round(self.tracemaxtext.value(), decimals=2)
        self.tracelength = np.round(self.tracelengthtext.value(), decimals=2)
        self.updatetraceplot([], [], [], 1)

    @pyqtSlot(np.ndarray, np.ndarray, np.ndarray)
    def updatetraceplot(self, newx, newy1, newy2, updateflag=0):  # if updateflag=1 update min max - only after aquisition possible
        if updateflag == 0:
            self.tracex = np.append(self.tracex, newx)
            self.tracey1 = np.append(self.tracey1, newy1)
            self.tracey2 = np.append(self.tracey2, newy2)
            self.traceysum = self.tracey1+self.tracey2

            self.line1.set_xdata(self.tracex)
            self.line1.set_ydata(self.tracey1)
            self.line2.set_xdata(self.tracex)
            self.line2.set_ydata(self.tracey2)
            self.line3.set_xdata(self.tracex)
            self.line3.set_ydata(self.traceysum)

            tracexminlim = self.tracex.max()-self.tracelength
            if tracexminlim < 0:
                tracexminlim = 0
            self.traceaxes.set_xlim(tracexminlim, self.tracex.max())

            if self.traceapdsumcheck.isChecked() and not self.traceapd1check.isChecked() and not self.traceapd2check.isChecked():
                self.traceaxes.set_ylim(self.traceysum.min(), self.traceysum.max())
            elif self.traceapd1check.isChecked() and not self.traceapd2check.isChecked() and not self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(self.tracey1.min(), self.tracey1.max())
            elif self.traceapd2check.isChecked() and not self.traceapd1check.isChecked() and not self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(self.tracey2.min(), self.tracey2.max())
            elif self.traceapd1check.isChecked() and not self.traceapd2check.isChecked() and self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(np.min([self.tracey1.min(), self.traceysum.min()]), np.max([self.tracey1.max(), self.traceysum.max()]))
            elif self.traceapd2check.isChecked() and not self.traceapd1check.isChecked() and self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(np.min([self.tracey2.min(), self.traceysum.min()]), np.max([self.tracey2.max(), self.traceysum.max()]))
            elif self.traceapd1check.isChecked() and self.traceapd2check.isChecked() and self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(np.min([self.tracey2.min(), self.tracey1.min(), self.traceysum.min()]), np.max([self.tracey2.max(), self.tracey1.max(), self.traceysum.max()]))
            elif self.traceapd1check.isChecked() and self.traceapd2check.isChecked() and not self.traceapdsumcheck.isChecked():
                self.traceaxes.set_ylim(np.min([self.tracey1.min(), self.tracey2.min()]), np.max([self.tracey1.max(), self.tracey2.max()]))

            self.traceaxes.relim()
            self.traceaxes.autoscale_view()
            self.tracecanvas.draw()
            self.tracecanvas.flush_events()

        elif updateflag == 1:
            if len(self.tracex) > 0:
                self.traceaxes.set_xlim(self.tracemin, self.tracemax)
                if self.traceapdsumcheck.isChecked() and not self.traceapd1check.isChecked() and not self.traceapd2check.isChecked():
                    self.traceaxes.set_ylim(self.traceysum.min(), self.traceysum.max())
                elif self.traceapd1check.isChecked() and not self.traceapd2check.isChecked() and not self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(self.tracey1.min(), self.tracey1.max())
                elif self.traceapd2check.isChecked() and not self.traceapd1check.isChecked() and not self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(self.tracey2.min(), self.tracey2.max())
                elif self.traceapd1check.isChecked() and not self.traceapd2check.isChecked() and self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(np.min([self.tracey1.min(), self.traceysum.min()]), np.max([self.tracey1.max(), self.traceysum.max()]))
                elif self.traceapd2check.isChecked() and not self.traceapd1check.isChecked() and self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(np.min([self.tracey2.min(), self.traceysum.min()]), np.max([self.tracey2.max(), self.traceysum.max()]))
                elif self.traceapd1check.isChecked() and self.traceapd2check.isChecked() and self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(np.min([self.tracey2.min(), self.tracey1.min(), self.traceysum.min()]), np.max([self.tracey2.max(), self.tracey1.max(), self.traceysum.max()]))
                elif self.traceapd1check.isChecked() and self.traceapd2check.isChecked() and not self.traceapdsumcheck.isChecked():
                    self.traceaxes.set_ylim(np.min([self.tracey1.min(), self.tracey2.min()]), np.max([self.tracey1.max(), self.tracey2.max()]))

                self.traceaxes.relim()
                self.traceaxes.autoscale_view()

                self.tracecanvas.draw()
                self.tracecanvas.flush_events()


class MinionTraceAquisition(QObject):
    tracestart = pyqtSignal()
    tracestop = pyqtSignal()
    updatetrace = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, counttime, updatetime):
        super(MinionTraceAquisition, self).__init__()
        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())
        self.counttime = counttime
        self.updatetime = int(updatetime/self.counttime)

    def stop(self):
        self._isRunning = False

    def longrun(self):
        print("[%s] start trace" % QThread.currentThread().objectName())
        i = 0
        xpart = []
        ypart1 = []
        ypart2 = []
        tstart = time.time()
        while self._isRunning is True:
            # TODO - check if continuos counting works without delays
            i += 1
            xpart.append(i * self.counttime)
            # COUNT
            self.counter.write(b'C')
            time.sleep(self.counttime)
            answer = self.counter.read(8)
            apd1 = answer[:4]
            apd2 = answer[4:]
            apd1_count = int.from_bytes(apd1, byteorder='little')
            apd2_count = int.from_bytes(apd2, byteorder='little')
            ypart1.append(apd1_count)
            ypart2.append(apd2_count)
            time.sleep(self.counttime)

            if i % self.updatetime == 0:
                xpart = np.array(xpart)
                ypart1 = np.array(ypart1)
                ypart2 = np.array(ypart2)
                self.updatetrace.emit(xpart, ypart1, ypart2)
                xpart = []
                ypart1 = []
                ypart2 = []

        print('total time measured:', time.time()-tstart)
        print('thread done')
        self.tracestop.emit()
