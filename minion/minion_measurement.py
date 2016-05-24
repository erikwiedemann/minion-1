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


class InputRangePopup(QDialog):
    def __init__(self, parent=None):
        super(InputRangePopup, self).__init__(parent)

        self.msrz = 1
        self.msry = 1
        self.msrx = 1
        self.msrt = 1
        self.okvalue = False
        self.startz = 0.0
        self.starty = 0.0
        self.startx = 0.0
        self.starttheta = 0.0
        self.endz = 0.0
        self.endy = 0.0
        self.endx = 0.0
        self.endtheta = 0.0

        # microstep resolution
        self.labelmsrz = QLabel('used MSR for Z:')
        self.inputmsrz = QLineEdit()
        self.labelmsry = QLabel('used MSR for Y:')
        self.inputmsry = QLineEdit()
        self.labelmsrx = QLabel('used MSR for X:')
        self.inputmsrx = QLineEdit()
        self.labelmsrt = QLabel('used MSR for ' + u"\u03B8" + ':')
        self.inputmsrt = QLineEdit()

        # input measurement range
        self.labelstartz = QLabel('Z range: start at:')
        self.inputstartz = QLineEdit()
        self.labelendz = QLabel('end at:')
        self.inputendz = QLineEdit()
        self.labelstarty = QLabel('Y range: start at:')
        self.inputstarty = QLineEdit()
        self.labelendy = QLabel('end at:')
        self.inputendy = QLineEdit()
        self.labelstartx = QLabel('X range: start at:')
        self.inputstartx = QLineEdit()
        self.labelendx = QLabel('end at:')
        self.inputendx = QLineEdit()
        self.labelstarttheta = QLabel(u"\u03B8" + ' range: start at:')
        self.inputstarttheta = QLineEdit()
        self.labelendtheta = QLabel('end at:')
        self.inputendtheta = QLineEdit()

        # Ok and Cancel dialog
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.ok)
        self.buttons.rejected.connect(self.cancel)

        # layout
        layoutmsr = QVBoxLayout()
        layoutmsrz = QHBoxLayout()
        layoutmsrz.addWidget(self.labelmsrz)
        layoutmsrz.addWidget(self.inputmsrz)
        layoutmsry = QHBoxLayout()
        layoutmsry.addWidget(self.labelmsry)
        layoutmsry.addWidget(self.inputmsry)
        layoutmsrx = QHBoxLayout()
        layoutmsrx.addWidget(self.labelmsrx)
        layoutmsrx.addWidget(self.inputmsrx)
        layoutmsrt = QHBoxLayout()
        layoutmsrt.addWidget(self.labelmsrt)
        layoutmsrt.addWidget(self.inputmsrt)
        layoutmsr.addLayout(layoutmsrz)
        layoutmsr.addLayout(layoutmsry)
        layoutmsr.addLayout(layoutmsrx)
        layoutmsr.addLayout(layoutmsrt)

        inpurangelayout = QVBoxLayout()
        zrangelayout = QHBoxLayout()
        zrangelayout.addWidget(self.labelstartz)
        zrangelayout.addWidget(self.inputstartz)
        zrangelayout.addWidget(self.labelendz)
        zrangelayout.addWidget(self.inputendz)
        inpurangelayout.addLayout(zrangelayout)

        yrangelayout = QHBoxLayout()
        yrangelayout.addWidget(self.labelstarty)
        yrangelayout.addWidget(self.inputstarty)
        yrangelayout.addWidget(self.labelendy)
        yrangelayout.addWidget(self.inputendy)
        inpurangelayout.addLayout(yrangelayout)

        xrangelayout = QHBoxLayout()
        xrangelayout.addWidget(self.labelstartx)
        xrangelayout.addWidget(self.inputstartx)
        xrangelayout.addWidget(self.labelendx)
        xrangelayout.addWidget(self.inputendx)
        inpurangelayout.addLayout(xrangelayout)

        thetarangelayout = QHBoxLayout()
        thetarangelayout.addWidget(self.labelstarttheta)
        thetarangelayout.addWidget(self.inputstarttheta)
        thetarangelayout.addWidget(self.labelendtheta)
        thetarangelayout.addWidget(self.inputendtheta)
        inpurangelayout.addLayout(thetarangelayout)

        layout = QGridLayout()
        layout.addLayout(layoutmsr, 0, 0)
        layout.addLayout(inpurangelayout, 1, 0)
        layout.addWidget(self.buttons, 2, 0)
        self.setLayout(layout)
        self.setWindowTitle('InputRange')
        self.setGeometry(1600, 300, 200, 200)

    def ok(self):
        self.okvalue = True
        self.accept()

    def cancel(self):
        self.okvalue = False
        self.reject()

    def getInputs(self):
        try:
            self.startz = self.inputstartz.text()
            self.endz = self.inputendz.text()
            self.starty = self.inputstarty.text()
            self.endy = self.inputendy.text()
            self.startx = self.inputstartx.text()
            self.endx = self.inputendx.text()
            self.starttheta = self.inputstarttheta.text()
            self.endtheta = self.inputendtheta.text()
            self.msrz = self.inputmsrz.text()
            self.msry = self.inputmsry.text()
            self.msrx = self.inputmsrx.text()
            self.msrt = self.inputmsrt.text()
            return self.okvalue, self.msrz, self.msry, self.msrx, self.msrt, self.startz, self.endz, self.starty,\
                   self.endy, self.startx, self.endx, self.starttheta, self.endtheta
        except:
            print("no input")

    @staticmethod
    def popup_and_get_inputs(parent=None):
        dialog = InputRangePopup(parent)
        dialog.show()
        dialog.exec_()
        return dialog.getInputs()


class InputMSRPopup(QDialog):
    def __init__(self, parent=None):
        super(InputMSRPopup, self).__init__(parent)

        self.msrz = 1
        self.msry = 1
        self.msrx = 1
        self.msrt = 1
        self.okvalue = False

        # microstep resolution
        self.labelmsrz = QLabel('used MSR for Z:')
        self.inputmsrz = QLineEdit()
        self.labelmsry = QLabel('used MSR for Y:')
        self.inputmsry = QLineEdit()
        self.labelmsrx = QLabel('used MSR for X:')
        self.inputmsrx = QLineEdit()
        self.labelmsrt = QLabel('used MSR for ' + u"\u03B8" + ':')
        self.inputmsrt = QLineEdit()

        # Ok and Cancel dialog
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.ok)
        self.buttons.rejected.connect(self.cancel)

        # layout
        layoutmsr = QVBoxLayout()
        layoutmsrz = QHBoxLayout()
        layoutmsrz.addWidget(self.labelmsrz)
        layoutmsrz.addWidget(self.inputmsrz)
        layoutmsry = QHBoxLayout()
        layoutmsry.addWidget(self.labelmsry)
        layoutmsry.addWidget(self.inputmsry)
        layoutmsrx = QHBoxLayout()
        layoutmsrx.addWidget(self.labelmsrx)
        layoutmsrx.addWidget(self.inputmsrx)
        layoutmsrt = QHBoxLayout()
        layoutmsrt.addWidget(self.labelmsrt)
        layoutmsrt.addWidget(self.inputmsrt)
        layoutmsr.addLayout(layoutmsrz)
        layoutmsr.addLayout(layoutmsry)
        layoutmsr.addLayout(layoutmsrx)
        layoutmsr.addLayout(layoutmsrt)

        layout = QGridLayout()
        layout.addLayout(layoutmsr, 0, 0)
        layout.addWidget(self.buttons, 1, 0)
        self.setLayout(layout)
        self.setWindowTitle('InputMSR')
        self.setGeometry(1600, 300, 200, 100)

    def ok(self):
        self.okvalue = True
        self.accept()

    def cancel(self):
        self.okvalue = False
        self.reject()

    def getInputs(self):
        try:
            self.msrz = self.inputmsrz.text()
            self.msry = self.inputmsry.text()
            self.msrx = self.inputmsrx.text()
            self.msrt = self.inputmsrt.text()
            return self.okvalue, self.msrz, self.msry, self.msrx, self.msrt
        except:
            print("no input")

    @staticmethod
    def popup_and_get_inputs(parent=None):
        dialog = InputMSRPopup(parent)
        dialog.show()
        dialog.exec_()
        return dialog.getInputs()


class MinionMeasurement(QWidget):
    def __init__(self, parent=None):    # when implemented into the whole programme, clear '=None'. the big programme is the parent
        super(MinionMeasurement, self).__init__(parent)
        self.parent = parent

        # integrate this only, if embedded in the bigger structure
        #self.hardware_counter = self.parent.hardware_counter
        #if self.hardware_counter is True:
        #    self.counter = self.parent.counter     # use self.parent.nameoffunction/class to call from parent

        # ComboBox lists
        self.measureprogrammes = ['fluorescence triaxial magnet, full', 'fluorescence cubic magnet, full',
                                  'fluorescence triaxial magnet, section', 'fluorescence cubic magnet, section']
        self.setreset = False
        self.cubic = False
        self.startz = 0.0
        self.starty = 0.0
        self.startx = 0.0
        self.starttheta = 0.0
        self.endz = 0.0
        self.endy = 0.0
        self.endx = 0.0
        self.endtheta = 0.0
        self.okvalue = False
        self.msrz = 1
        self.msry = 1
        self.msrx = 1
        self.msrt = 1
        #self.data = np.ndarray([[0]])
        self.initUI()

    def initUI(self):
        # -------- create measurement labels, Edits, Buttons -----------------------------------------------------------

        self.labelmeasurementheader = QLabel('choose preprogrammed measurement:')
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

        choosemeasurementlayout = QHBoxLayout()
        choosemeasurementlayout.addWidget(self.labelmeasurementheader)
        choosemeasurementlayout.addWidget(self.choosemeasurement)
        measurementlayout.addLayout(choosemeasurementlayout, 0, 0)

        startmeasurementlayout = QHBoxLayout()
        startmeasurementlayout.addWidget(self.buttonstartmeasurement)
        startmeasurementlayout.addWidget(self.buttonabortmeasurement)
        measurementlayout.addLayout(startmeasurementlayout, 2, 0)

        statusmeasurementlayout = QHBoxLayout()
        statusmeasurementlayout.addWidget(self.labelmeasurementstatus)
        statusmeasurementlayout.addWidget(self.measurementstatus)
        measurementlayout.addLayout(statusmeasurementlayout, 3, 0)

        savemeasurementlayout = QHBoxLayout()
        savemeasurementlayout.addWidget(self.labelsavemeasurement)
        savemeasurementlayout.addWidget(self.savemeasurementfilename)
        savemeasurementlayout.addWidget(self.buttonsavemeasurement)
        measurementlayout.addLayout(savemeasurementlayout, 4, 0)

        # create main layout and show it
        layout = QGridLayout()
        layout.addLayout(measurementlayout, 0, 0)

        self.setLayout(layout)
        self.setGeometry(1500, 200, 800, 300)
        self.setWindowTitle('Measurements')
        self.show()

    def startmeasurement(self):
        text = self.choosemeasurement.currentText()
        if text == 'fluorescence triaxial magnet, full':
            print(text)
            self.cubic = False
            self.setreset = True
            # MSR viy popup window
            print("Opening popup window")
            popupinput = InputMSRPopup.popup_and_get_inputs()
            self.okvalue = popupinput[0]
            self.msrz = popupinput[1]
            self.msry = popupinput[2]
            self.msrx = popupinput[3]
            self.msrt = popupinput[4]
            # start measurement
            if self.okvalue is True:
                self.connectfull()
        if text == 'fluorescence cubic magnet, full':
            print(text)
            self.cubic = True
            self.setreset = True
            print("Opening popup window")
            popupinput = InputMSRPopup.popup_and_get_inputs()
            self.okvalue = popupinput[0]
            self.msrz = popupinput[1]
            self.msry = popupinput[2]
            self.msrx = popupinput[3]
            self.msrt = popupinput[4]
            # start measurement
            if self.okvalue is True:
                self.connectfull()

        if text == 'fluorescence triaxial magnet, section':
            print(text)
            self.cubic = False
            self.resetstage()
            # input range via popup window
            print("Opening popup window")
            popupinput = InputRangePopup.popup_and_get_inputs()
            self.okvalue = popupinput[0]
            self.msr = popupinput[1]
            self.startz = popupinput[2]
            self.endz = popupinput[3]
            self.starty = popupinput[4]
            self.endy = popupinput[5]
            self.startx = popupinput[6]
            self.endx = popupinput[7]
            #start measurement
            if self.okvalue is True:
                self.connectsection()
        if text == 'fluorescence cubic magnet, section':
            print(text)
            self.cubic = True
            self.resetstage()
            # input range via popup window
            print("Opening popup window")
            popupinput = InputRangePopup.popup_and_get_inputs()
            self.okvalue = popupinput[0]
            self.msr = popupinput[1]
            self.startz = popupinput[2]
            self.endz = popupinput[3]
            self.starty = popupinput[4]
            self.endy = popupinput[5]
            self.starttheta = popupinput[6]
            self.endtheta = popupinput[7]
            # start measurement
            if self.okvalue is True:
                self.connectsection()

    def connectfull(self):
        print('full measurement started')
        self.measure = Measure(self.setreset, self.cubic, self.startz, self.endz, self.starty, self.endy, self.startx,
                               self.endx, self.starttheta, self.endtheta, self.msrz, self.msry, self.msrx, self.msrt)     # add self.parent.
        self.measurethread = QThread(self, objectName='MeasureThread')
        self.measure.moveToThread(self.measurethread)
        self.measure.finished.connect(self.measurethread.quit)
        self.measurethread.started.connect(self.measure.fluorescencefull)      # call function
        self.measure.datatosave.connect(self.updatesave)
        #self.measurethread.track.connect(self.parent.trackerwidget.findmaxclicked)
        self.measurethread.finished.connect(self.measurethread.deleteLater)
        self.measure.datatosave.connect(self.updatesave)
        self.measurethread.start()

    def connectsection(self):
        print('section measurement started')
        self.measure = Measure(self.setreset, self.cubic, self.startz, self.endz, self.starty, self.endy, self.startx,
                               self.endx, self.starttheta, self.endtheta, self.msrz, self.msry, self.msrx, self.msrt)
        self.measurethread = QThread(self, objectName='MeasureThread')
        self.measure.moveToThread(self.measurethread)
        self.measure.finished.connect(self.measurethread.quit)
        self.measurethread.started.connect(self.measure.fluorescencesection)      # call function
        self.measure.datatosave.connect(self.updatesave)
        #self.measurethread.track.connect(self.parent.trackerwidget.findmaxclicked)
        self.measurethread.finished.connect(self.measurethread.deleteLater)
        self.measure.datatosave.connect(self.updatesave)
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
        np.savetxt(str(os.getcwd())+'/data/'+str(self.filename)+'.txt', self.data)
        print('file saved to data folder')

    @pyqtSlot(np.ndarray)
    def updatesave(self, datapoint):
        self.data = np.append(self.data, datapoint)

class Measure(QObject):

    finished = pyqtSignal()
    started = pyqtSignal()
    datatosave = pyqtSignal(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    track = pyqtSignal()

    def __init__(self, setreset, cubic, startz, endz, starty, endy, startx, endx, starttheta, endtheta, msrz, msry, msrx, msrt):
        super(Measure, self).__init__()

        self.send = ''
        self.setreset = setreset
        self.cubic = cubic
        self.startz = startz
        self.starty = starty
        self.startx = startx
        self.starttheta = starttheta
        self.endz = endz
        self.endy = endy
        self.endx = endx
        self.endtheta = endtheta
        self.msrz = msrz
        self.msry = msry
        self.msrx = msrx
        self.msrt = msrt
        self._isRunning = True
        self._ZisRunning = True
        self._YisRunning = True
        self._XisRunning = True
        self._TisRunning = True
        self.directz = 0
        self.directy = 0
        self.directx = 0
        self.directtheta = 0
        self.tposition = 0.0     # distance in um
        self.zposition = 0.0     # distance in um
        self.yposition = 0.0     # distance in um
        self.xposition = 0.0     # distance in um
        self.FV = 0.0
        self.waitforfluourescence = 10      # in seconds
        # self.waitformove = 2                # in seconds
        self.waitforreset = 10              # in seconds
        self.updatetime = 100               # in milliseconds
        self.counttime = 100                # in milliseconds
        self.traceMV = 0

    def stop(self):
        self._isRunning = False
        print('stop measurement')

    def tracetimechanged(self):

        if self.hardware_counter is True:
            self.parent.fpga.setcountingtime(self.counttime)
            self.check_counttime = self.parent.fpga.checkcounttime()
            print('\t fpga counttime:', self.check_counttime)
        print('counttime:', self.counttime)

    def fluorescencefull(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('full fluorescence is measured')
            self.arduino = serial.Serial('/dev/ttyACM0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
            print(self.arduino)
            print(self.arduino.isOpen())

            self.directz = 0
            self.directy = 0
            self.directx = 0
            self.directtheta = 0

            if self.setreset is True:
                self.send = '5:1;'
                self.arduino.write(self.send.encode('ASCII'))
                moveit = True
                time.sleep(2)
                while moveit is True:
                    received = self.arduino.readline()
                    time.sleep(0.001)
                    if received == b'motion finished\r\n':
                        print('reset finished')
                        moveit = False

            while self._ZisRunning is True:     # z running
                while self._YisRunning is True:
                    if self.cubic is False:
                        while self._XisRunning is True:
                            self.recorder()
                            self.moverx()
                    if self.cubic is True:
                        while self._TisRunning is True:
                            self.recorder()
                            self.movert()
                    self.movery()
                    self._TisRunning = True
                    self._XisRunning = True

                self.moverz()
                self._YisRunning = True

    def fluorescencesection(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('fluorescence is measured section wise')
            self.arduino = serial.Serial('/dev/ttyACM0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
            print(self.arduino)
            print(self.arduino.isOpen())

            self.directz = 0
            self.directy = 0
            self.directx = 0
            self.directtheta = 0

            for z in range(self.startz, self.endz):
                for y in range(self.starty, self.endy):
                    if self.cubic is False:
                        for x in range(self.startx, self.endx):
                            self.recorder()
                            self.moverx()

                    if self.cubic is True:
                        for theta in range(self.starttheta, self.endtheta):
                            self.recorder()
                            self.movert()

                    self.movery()
                self.moverz()

    def moverz(self):
        self.send = '1:' + str(self.msrz) + ';' + str(self.directz)
        self.arduino.write(self.send.encode('ASCII'))
        moveitz = True
        while moveitz is True:
            received = self.arduino.readline()
            time.sleep(0.001)
            pushz = 0
            if received == b'pushz\r\n':
                # collect push signals, later convert to um
                pushz += 1
            if received == b'stopZend\r\n':
                self._ZisRunning = False
            if received == b'motion finished\r\n':
                moveitz = False
                self.zposition = 5*(pushz/self.msrz)

    def movery(self):
        self.send = '2:' + str(self.msry) + ';' + str(self.directy)
        self.arduino.write(self.send.encode('ASCII'))
        moveity = True
        while moveity is True:
            received = self.arduino.readline()
            time.sleep(0.001)
            pushy = 0
            if received == b'pushy\r\n':
                # collect push signals, later convert to um
                pushy += 1
            if received == b'stopYstart\r\n':
                self.directy = 0
                self._YisRunning = False
            if received == b'stopYend\r\n':
                self.directy = 1
                self._YisRunning = False
            if received == b'motion finished\r\n':
                moveity = False
                if self.directy == 0:
                    self.yposition += 5*(pushy/self.msry)
                if self.directy == 1:
                    self.yposition -= 5*(pushy/self.msry)

    def moverx(self):
        self.send = '3:' + str(self.msrx) + ';' + str(self.directx)
        self.arduino.write(self.send.encode('ASCII'))
        moveitx = True
        # wait for stop signal
        while moveitx is True:
            received = self.arduino.readline()
            time.sleep(0.001)
            pushx = 0
            if received == b'pushx\r\n':
                # collect push signals, later convert to um
                pushx += 1
            if received == b'stopXstart\r\n':
                self.directx = 0
                self._XisRunning = False
            if received == b'stopXend\r\n':
                self.directx = 1
                self._XisRunning = False
            if received == b'motion finished\r\n':
                moveitx = False
                if self.directx == 0:
                    self.xposition += 3.175*(pushx/self.msrx)
                if self.directx == 1:
                    self.xposition -= 3.175*(pushx/self.msrx)

    def movert(self):
        self.send = '4:' + str(self.msrt) + ';' + str(self.directtheta)
        self.arduino.write(self.send.encode('ASCII'))
        moveittheta = True
        # wait for stop signal
        while moveittheta is True:
            received = self.arduino.readline()
            time.sleep(0.001)
            pusht = 0
            if received == b'pusht\r\n':
                # collect push signals, later convert to um
                pusht += 1
            if received == b'motion finished\r\n':
                moveittheta = False
                self._TisRunning = False
                if self.tposition == 360:
                    self.tposition = 0
                else:
                    self.tposition = 1.8*(pusht/self.msrt)

    def recorder(self):
        self.traceaquisition = MinionTraceAquisition(self.parent.fpga, self.updatetime)
        self.tracethread = QThread(self, objectName='TraceThread')
        self.traceaquisition.moveToThread(self.tracethread)
        self.traceaquisition.finished.connect(self.tracethread.quit)
        self.tracethread.started.connect(self.trace.longrun)      # call function
        self.traceaquisition.updatetrace.connect(self.updatedata)
        self.tracethread.finished.connect(self.tracethread.deleteLater)
        self.traceaquisition.updatetrace.connect(self.updatedata)
        self.tracethread.start()

    @pyqtSlot(np.ndarray, np.ndarray, np.ndarray)
    def updatedata(self, newx, newy1, newy2, updateflag=0):
        if updateflag == 0:
            datapoint = np.array([[0]])
            # tracex = np.ndarray([0])
            tracey1 = np.ndarray([0])
            tracey2 = np.ndarray([0])
            # traceysum = np.ndarray([0])
            # tracex = newx
            tracey1 = np.append(tracey1, newy1)
            tracey2 = np.append(tracey2, newy2)
            traceysum = tracey1 + tracey2
            traceMV = np.mean(traceysum)

            datapoint = np.append(datapoint, [[self.Zi, self.Yi, self.Xi, self.Ti, traceMV]])
            self.datatosave.emit(datapoint)

class MinionTraceAquisition(QObject):
    finished = pyqtSignal()
    started = pyqtSignal()
    updatetrace = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, fpga, updatetime, countime):
        super(MinionTraceAquisition, self).__init__()
        self._isRunning = True

        print("[%s] create worker" % QThread.currentThread().objectName())
        self.fpga = fpga
        self.counttime = countime
        self.updatetime = updatetime      # if use, dont't forget to implement in __inti__()

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
            measuretime = time.time()-tstart
            xpart.append(measuretime)
            # COUNT
            apd1_count, apd2_count, apd_sum = self.fpga.count()  # in cps
            ypart1.append(apd1_count)
            ypart2.append(apd2_count)

            if i % self.updatetime == 0:       # not so sure if I really need it
                xpart = np.array(xpart)
                ypart1 = np.array(ypart1)
                ypart2 = np.array(ypart2)
                self.updatetrace.emit(xpart, ypart1, ypart2)
                xpart = []
                ypart1 = []
                ypart2 = []

            if measuretime >= 5:
                xpart = np.array(xpart)
                ypart1 = np.array(ypart1)
                ypart2 = np.array(ypart2)
                self.updatetrace.emit(xpart, ypart1, ypart2)
                xpart = []
                ypart1 = []
                ypart2 = []
                self.stop()

        print('total time measured:', time.time()-tstart)
        print('thread done')
        self.tracestop.emit()
