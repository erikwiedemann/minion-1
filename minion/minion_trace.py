"""
trace module
"""
print('executing minion.minion_trace')

import os
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
from matplotlib.animation import FuncAnimation


class MinionTraceUi(QWidget):
    def __init__(self, parent=None):
        super(MinionTraceUi, self).__init__(parent)
        # check hardware
        from minion.minion_hardware_check import CheckHardware
        self.hardware_counter, self.hardware_laser, self.hardware_stage = CheckHardware.check(CheckHardware)
        # set initial parameters
        self.status = False   # True - allowed to measure, False - forbidden to measure (e.g. if counter is needed elsewhere)
        self.uisetup()

    def uisetup(self):
        self.tracefigure = Figure()
        self.tracecanvas = FigureCanvas(self.tracefigure)
        self.tracecanvas.setFixedSize(600, 200)
        # self.tracecanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar(self.tracecanvas, self)
        self.traceaxes = self.tracefigure.add_subplot(111)
        self.traceaxes.hold(False)


        self.tracestartbutton = QPushButton('start')
        self.tracestartbutton.pressed.connect(self.tracestartclicked)
        self.tracestopbutton = QPushButton('stop')
        self.tracestopbutton.pressed.connect(self.tracestopclicked)


        # create layout
        trace_layout = QGridLayout()
        trace_layout.addWidget(self.tracecanvas, 0, 0, 5, 10)
        trace_layout.addWidget(self.toolbar, 5, 0, 1, 10)
        trace_layout.addWidget(self.tracestartbutton, 6, 0)
        trace_layout.addWidget(self.tracestopbutton, 6, 1)

        trace_layout.setSpacing(2)
        self.setLayout(trace_layout)

    def tracestartclicked(self):
        print("[%s] start trace" % QThread.currentThread().objectName())
        countertemp = True
        self.tracex = np.ndarray([])
        self.tracey = np.ndarray([])
        self.line, = self.traceaxes.plot(self.tracex, self.tracey, '-')
        if countertemp is True:
            self.traceaquisition = MinionTraceAquisition()
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

    @pyqtSlot(np.ndarray, np.ndarray)
    def updatetraceplot(self, newx, newy):
        print('update')

        print(np.shape(newx), np.shape(newx))
        self.tracex = np.append(self.tracex, newx)

        self.tracey = np.append(self.tracey, newy)
        print(np.shape(self.tracex), np.shape(self.tracey))
        self.traceaxes.plot(self.tracex, self.tracey, '-')
        # self.line.set_data(self.tracex, self.tracey)
        self.tracecanvas.draw()



class MinionTraceAquisition(QObject):
    tracestart = pyqtSignal()
    tracestop = pyqtSignal()
    updatetrace = pyqtSignal(np.ndarray, np.ndarray)

    def __init__(self):
        super(MinionTraceAquisition, self).__init__()

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning = False

    def longrun(self):
        print("[%s] start trace" % QThread.currentThread().objectName())
        i = 0
        xpart = []
        ypart = []
        tstart = time.time()
        while self._isRunning is True:
            i += 1
            xpart.append(i * 0.2)
            ypart.append(np.random.random_integers(0, 100))
            time.sleep(0.1)

            if i % 10 == 0:
                xpart = np.array(xpart)
                ypart = np.array(ypart)
                self.updatetrace.emit(xpart, ypart)
                xpart = []
                ypart = []

        print('total time measured:', time.time()-tstart)
        print('thread done')
        self.tracestop.emit()




