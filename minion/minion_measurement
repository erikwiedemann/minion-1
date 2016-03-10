from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import time
import serial
import numpy as np
import matplotlib as plt
#import matplotlib.style as pltstyle
from ctypes import *


class MinionMeasurement(QWidget):
    def __init__(self, parent=None):
        super(MinionMeasurement, self).__init__(parent)
        self.parent = parent

        # ComboBox lists
        self.measureprogrammes = ['position dependent fluorescence triaxial magnet',
                                  'position dependent fluorescence cubic magnet']


        self.initUI()

    def initUI(self):
        # -------- create measurement labels, Edits, Buttons -----------------------------------------------------------

        self.labelmeasurementheader = QLabel('choose preprogrammed measurement')
        self.choosemeasurement = QComboBox()
        self.choosemeasurement.addItems(self.measureprogrammes)
        self.buttonstartmeasurement = QPushButton('start process')
        self.buttonstartmeasurement.clicked.connect(self.startmeasurement)
        self.buttonabortmeasurement = QPushButton('abort process')
        self.buttonabortmeasurement.clicked.connect(self.abortmeasurement)
        self.labelmeasurementstatus = QLabel('process status')
        self.measurementstatus = QProgressBar()
        #self.measurementstatus.setGeometry()
        self.labelsavemeasurement = QLabel('save file under')
        self.savemeasurementfilename = QLineEdit()
        self.savemeasurementfilename.setText('filename')
        self.buttonsavemeasurement = QPushButton('save measurment')
        self.buttonsavemeasurement.clicked.connect(self.savemeasurementclicked)

        # layout measurement
        measurementlayout = QGridLayout()
        measurementlayout.addWidget(self.labelmeasurementheader, 0, 0)

        choosemeasurementlayout = QHBoxLayout()
        choosemeasurementlayout.addWidget(self.choosemeasurement)
        choosemeasurementlayout.addWidget(self.buttonstartmeasurement)
        choosemeasurementlayout.addWidget(self.buttonabortmeasurement)
        measurementlayout.addLayout(choosemeasurementlayout, 1, 0)

        statusmeasurementlayout = QHBoxLayout()
        statusmeasurementlayout.addWidget(self.labelmeasurementstatus)
        statusmeasurementlayout.addWidget(self.measurementstatus)
        measurementlayout.addLayout(statusmeasurementlayout, 2, 0)

        savemeasurementlayout = QHBoxLayout()
        savemeasurementlayout.addWidget(self.labelsavemeasurement)
        savemeasurementlayout.addWidget(self.savemeasurementfilename)
        savemeasurementlayout.addWidget(self.buttonsavemeasurement)
        measurementlayout.addLayout(savemeasurementlayout, 3, 0)

        # create main layout and show it
        layout = QGridLayout()
        layout.addLayout(measurementlayout, 0, 0)

        self.setLayout(layout)
        self.setGeometry(1500, 200, 800, 300)
        self.setWindowTitle('Message box')
        self.show()

    def startmeasurement(self):
        print('measurement started')
        self.measure = Measure(self.send, self.setreset, self.cubic)
        self.measurethread = QThread(self, objectName='MeasureThread')
        self.measure.moveToThread(self.measurethread)
        self.measure.finished.connect(self.measurethread.quit)

        self.resetstage

        if self.measureprogrammes == 'position dependent fluorescence triaxial magnet':
            self.cubic = False
            self.measurethread.started.connect(self.measure.fluorescence)      # call function
            self.measurethread.finished.connect(self.measurethread.deleteLater)
            self.measurethread.start()
        if self.measureprogrammes == 'position dependent fluorescence cubic magnet':
            self.cubic = True
            self.measurethread.started.connect(self.measure.fluorescence)      # call function
            self.measurethread.finished.connect(self.measurethread.deleteLater)
            self.measurethread.start()

    def resetstage(self):
        replychangemode = QMessageBox.question(self, 'Reset Stage?', 'Running measurement from reset stage?',
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if replychangemode == QMessageBox.Yes:
            self.setreset = True
        else:
            self.setreset = False

    def abortmeasurement(self):
        try:
            print('measurement aborted')
            QApplication.processEvents()
            self.measure.stop()
            self.measurethread.quit()
        except:
            print('no measurement running')

    def savemeasurementclicked(self):
        self.filename, *rest = self.savemeasurementfilename.text().split('.')
        # np.savetxt(str(os.getcwd())+'/data/'+str(self.filename)+'.txt', self.mapdata)
        # self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.pdf')
        # self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.png')
        print('file saved to data folder')


class Measure(QObject):

    def __init__(self, send, setreset, cubic):
        super(Measure, self).__init__()

        self.send = send
        self.setreset = setreset
        self.cubic = cubic
        self._isRunning = True

    def stop(self):
        self._isRunning = False
        print('stop measurement')

    def fluorescence(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('fluorescence is measured')
            self.arduino = serial.Serial('/dev/ttyACM0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
            print(self.arduino)
            print(self.arduino.isOpen())

            if self.setreset is True:
                self.send = 'r:' + str(self.positiontheta)
                self.arduino.write(self.send.encode('ASCII'))
                time.sleep(2)
                stopper = self.arduino.readline()
                if stopper == 'fullstop':
                    self.trace.stop()
                    self.tracethread.quit()
                    self.finished.emit()


            self.trace = MinionTraceAquisition()
            self.tracethread = QThread(self, objectName='TraceThread')
            self.trace.moveToThread(self.tracethread)
            self.trace.finished.connect(self.tracethread.quit)



            while self._isRunning is True:
                while self.Zisrunning is True:

                    checkstop = self.arduino.readline()
                    if checkstop == 'Xend stopped':
                        self.Zisrunning = False
                    else:
                        self.Zisrunning = True

                    while self.Yisrunning is True:

                        checkstop = self.arduino.readline()
                        if checkstop == 'Yend stopped':
                            self.Yisrunning = False
                        else:
                            self.Yisrunning = True

                        if self.cubic is True:
                            for theta in range(0, 200):
                                self.send = '4:1;0'
                                self.arduino.write(self.send.encode('ASCII'))

                                time.sleep(2)
                                self.tracethread.started.connect(self.trace.longrun)      # call function
                                self.tracethread.finished.connect(self.tracethread.deleteLater)
                                self.tracethread.start()
                                time.sleep(5)
                                self.trace.stop()

                                # safe data: safe mean value trace, safe actual position

                        if self.cubic is False:
                            while self.XisRunning is True:

                                checkstop = self.arduino.readline()
                                if checkstop == 'Xend stopped':
                                    self.Xisrunning = False
                                else:
                                    self.Xisrunning = True




class MinionTraceAquisition(QObject):
    tracestart = pyqtSignal()
    tracestop = pyqtSignal()
    updatetrace = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, counttime, updatetime, fpga):
        super(MinionTraceAquisition, self).__init__()
        self._isRunning = True

        print("[%s] create worker" % QThread.currentThread().objectName())
        self.fpga = fpga
        self.counttime = counttime
        self.updatetime = updatetime

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
            # check if continuos counting works without delays
            i += 1
            xpart.append(time.time()-tstart)
            # COUNT
            apd1_count, apd2_count, apd_sum = self.fpga.count()  # in cps
            ypart1.append(apd1_count)
            ypart2.append(apd2_count)

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MinionMeasurement()
    window.show()
    sys.exit(app.exec_())
