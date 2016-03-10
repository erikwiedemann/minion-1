print('executing minion.minion_magnetstage_control')

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import time
import serial
from ctypes import *

# main Class with GUI and controller functions
class MinionMagnetStage(QWidget):
    def __init__(self, parent=None):
        super(MinionMagnetStage, self).__init__(parent)
        self.parent = parent

        # ComboBox lists
        self.units = ['mm', 'um']
        self.directions = ['forward', 'backward']
        self.measureprogrammes = ['gs LAC', 'es LAC', '100G']

        self.initUI()

        # variables
        self.unitz = 1000.0
        self.unity = 1000.0
        self.unitx = 1000.0
        self.stepsizezy = 5.0
        self.stepsizex = 3.175
        self.stepsizetheta = 1.8
        self.cubicmagnet = False
        self.triaxialmagnet = False
        self.endz = False
        self.startz = False
        self.endy = False
        self.starty = False
        self.endx = False
        self.startx = False
        self.currentstatusmagnet = 'no magnet chosen'
        self.movervariable = ''
        self.movestagezsteps = 0.0
        self.movestageysteps = 0.0
        self.movestagexsteps = 0.0
        self.movestagethetasteps = 0.0
        self.sendz = ''
        self.sendy = ''
        self.sendx = ''
        self.sendtheta = ''
        self.send = ''
        self.directionz = 0
        self.directiony = 0
        self.directionx = 0
        self.directiontheta = 0

        # import last saved stage position
        if os.path.isfile('last_position.txt') is True:
            self.last_position = open('last_position.txt', 'r+')
            positions = self.last_position.readlines()
            print(positions)
            self.positionz = float(positions[0])
            self.positiony = float(positions[1])
            self.positionx = float(positions[2])
            self.positiontheta = float(positions[3])
            self.last_position.close()
            self.display()

            self.last_position = open('last_position.txt', 'w+')

        else:
            self.last_position = open('last_position.txt', 'w+')
            self.resetpressed()

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # save last position
            self.last_position.write(str(self.positionz) + '\n' + str(self.positiony) + '\n' + str(self.positionx) +
                                     '\n' + str(self.positiontheta) + '\n')
            self.last_position.close()
            event.accept()
        else:
            event.ignore()

    def initUI(self):

        # -------- create mode buttons ---------------------------------------------------------------------------------
        self.buttoncubicmagnet = QPushButton("cubic", self)
        # self.buttoncubicmagnet.setCheckable(True)
        self.buttoncubicmagnet.clicked.connect(self.cubicmagnetfunc)

        self.buttontriaxialmagnet = QPushButton("triaxial", self)
        # self.buttontriaxialmagnet.setCheckable(True)
        self.buttontriaxialmagnet.clicked.connect(self.triaxialmagnetfunc)

        # -------- display status --------------------------------------------------------------------------------------
        # display stage position
        self.labelstageposition = QLabel('current stage position')

        self.labelstatusz = QLabel('z')
        self.statusz = QLineEdit('')
        self.statusz.setReadOnly(True)

        self.labelstatusy = QLabel('y')
        self.statusy = QLineEdit('')
        self.statusy.setReadOnly(True)

        self.labelstatusx = QLabel('x')
        self.statusx = QLineEdit('')
        self.statusx.setReadOnly(True)

        self.labelstatustheta = QLabel(u"\u03B8")
        self.statustheta = QLineEdit('')
        self.statustheta.setReadOnly(True)

        # display stopper status
        self.labelstatusstopper = QLabel('status of stoppers')

        self.labelstatusstopperz1 = QLabel('z start')
        self.statusstopperz1 = QLineEdit()
        self.statusstopperz1.setReadOnly(True)

        self.labelstatusstopperz2 = QLabel('z end')
        self.statusstopperz2 = QLineEdit()
        self.statusstopperz2.setReadOnly(True)

        self.labelstatusstoppery1 = QLabel('y start')
        self.statusstoppery1 = QLineEdit()
        self.statusstoppery1.setReadOnly(True)

        self.labelstatusstoppery2 = QLabel('y end')
        self.statusstoppery2 = QLineEdit()
        self.statusstoppery2.setReadOnly(True)

        self.labelstatusstopperx1 = QLabel('x start')
        self.statusstopperx1 = QLineEdit()
        self.statusstopperx1.setReadOnly(True)

        self.labelstatusstopperx2 = QLabel('x end')
        self.statusstopperx2 = QLineEdit()
        self.statusstopperx2.setReadOnly(True)

        # display working status
        self.labelcurrentstatus = QLabel('current status')
        self.currentstatus = QTextEdit()
        self.currentstatus.setReadOnly(True)

        # -------- create input labels, windows and buttons ------------------------------------------------------------

        self.labelinput = QLabel('input displacement')

        # start and stop motion buttons
        self.buttonmovestage = QPushButton('move stage')
        self.buttonmovestage.clicked.connect(self.movestage)
        self.buttonstopstage = QPushButton('stop stage')
        self.buttonstopstage.clicked.connect(self.stopstage)

        # z
        self.labelinputz = QLabel('z')
        self.inputz = QLineEdit()
        self.labelinputinz = QLabel('in')
        self.chooseunitzbox = QComboBox()
        self.chooseunitzbox.addItems(self.units)
        self.chooseunitzbox.currentIndexChanged.connect(self.chooseunitz)
        self.choosedirectionzbox = QComboBox()
        self.choosedirectionzbox.addItems(self.directions)
        self.choosedirectionzbox.currentIndexChanged.connect(self.changedirectionz)

        # y
        self.labelinputy = QLabel('y')
        self.inputy = QLineEdit()
        self.labelinputiny = QLabel('in')
        self.chooseunitybox = QComboBox()
        self.chooseunitybox.addItems(self.units)
        self.chooseunitybox.currentIndexChanged.connect(self.chooseunity)
        self.choosedirectionybox = QComboBox()
        self.choosedirectionybox.addItems(self.directions)
        self.choosedirectionybox.currentIndexChanged.connect(self.changedirectiony)

        # x
        self.labelinputx = QLabel('x')
        self.inputx = QLineEdit()
        self.labelinputinx = QLabel('in')
        self.chooseunitxbox = QComboBox()
        self.chooseunitxbox.addItems(self.units)
        self.chooseunitxbox.currentIndexChanged.connect(self.chooseunitx)
        self.choosedirectionxbox = QComboBox()
        self.choosedirectionxbox.addItems(self.directions)
        self.choosedirectionxbox.currentIndexChanged.connect(self.changedirectionx)

        # theta
        self.labelinputtheta = QLabel(u'\u03B8')
        self.inputtheta = QLineEdit()
        self.labelinputintheta = QLabel('in °')
        self.choosedirectionthetabox = QComboBox()
        self.choosedirectionthetabox.addItems(self.directions)
        self.choosedirectionthetabox.currentIndexChanged.connect(self.changedirectiontheta)

        # reset
        self.resetbutton = QPushButton('Reset')
        self.resetbutton.clicked.connect(self.resetpressed)

        # -------- create measurement labels, Edits, Buttons -----------------------------------------------------------

        self.labelmeasurementheader = QLabel('choose preprogrammed path')
        self.choosemeasurement = QComboBox()
        self.choosemeasurement.addItems(self.measureprogrammes)
        self.buttonstartmeasurement = QPushButton('start process')
        self.buttonstartmeasurement.clicked.connect(self.startmeasurement)
        self.buttonabortmeasurement = QPushButton('abort process')
        self.buttonabortmeasurement.clicked.connect(self.abortmeasurment)
        self.labelmeasurementstatus = QLabel('process status')
        self.measurementstatus = QProgressBar()
        #self.measurementstatus.setGeometry()

        # -------- create layout ---------------------------------------------------------------------------------------

        modebuttonlayout = QHBoxLayout()
        modebuttonlayout.addWidget(self.buttoncubicmagnet)
        modebuttonlayout.addWidget(self.buttontriaxialmagnet)

        # layout stage postion
        stagepostionlayout = QGridLayout()
        stagepostionlayout.addWidget(self.labelstageposition, 0, 0)

        stagepostionlayoutz = QHBoxLayout()
        stagepostionlayoutz.addWidget(self.labelstatusz)
        stagepostionlayoutz.addWidget(self.statusz)
        stagepostionlayout.addLayout(stagepostionlayoutz, 1, 0)

        stagepostionlayouty = QHBoxLayout()
        stagepostionlayouty.addWidget(self.labelstatusy)
        stagepostionlayouty.addWidget(self.statusy)
        stagepostionlayout.addLayout(stagepostionlayouty, 2, 0)

        stagepostionlayoutx = QHBoxLayout()
        stagepostionlayoutx.addWidget(self.labelstatusx)
        stagepostionlayoutx.addWidget(self.statusx)
        stagepostionlayout.addLayout(stagepostionlayoutx, 3, 0)

        stagepostionlayouttheta = QHBoxLayout()
        stagepostionlayouttheta.addWidget(self.labelstatustheta)
        stagepostionlayouttheta.addWidget(self.statustheta)
        stagepostionlayout.addLayout(stagepostionlayouttheta, 4, 0)

        # layout stopper status
        stopperlayout = QVBoxLayout()
        stopperlayout.addWidget(self.labelstatusstopper)

        stopperlayoutz = QHBoxLayout()
        stopperlayoutz.addWidget(self.labelstatusstopperz1)
        stopperlayoutz.addWidget(self.statusstopperz1)
        stopperlayoutz.addWidget(self.labelstatusstopperz2)
        stopperlayoutz.addWidget(self.statusstopperz2)
        stopperlayout.addLayout(stopperlayoutz)

        stopperlayouty = QHBoxLayout()
        stopperlayouty.addWidget(self.labelstatusstoppery1)
        stopperlayouty.addWidget(self.statusstoppery1)
        stopperlayouty.addWidget(self.labelstatusstoppery2)
        stopperlayouty.addWidget(self.statusstoppery2)
        stopperlayout.addLayout(stopperlayouty)

        stopperlayoutx = QHBoxLayout()
        stopperlayoutx.addWidget(self.labelstatusstopperx1)
        stopperlayoutx.addWidget(self.statusstopperx1)
        stopperlayoutx.addWidget(self.labelstatusstopperx2)
        stopperlayoutx.addWidget(self.statusstopperx2)
        stopperlayout.addLayout(stopperlayoutx)

        # layout current status
        currentstatuslayout = QVBoxLayout()
        currentstatuslayout.addWidget(self.labelcurrentstatus)
        currentstatuslayout.addWidget(self.currentstatus)

        # layout input
        inputlayout = QGridLayout()
        inputlayout.addWidget(self.labelinput, 0, 0)

        # z
        inputzlayout = QHBoxLayout()
        inputzlayout.addWidget(self.labelinputz)
        inputzlayout.addWidget(self.inputz)
        inputzlayout.addWidget(self.labelinputinz)
        inputzlayout.addWidget(self.chooseunitzbox)
        inputzlayout.addWidget(self.choosedirectionzbox)
        inputlayout.addLayout(inputzlayout, 1, 0)

        # y
        inputylayout = QHBoxLayout()
        inputylayout.addWidget(self.labelinputy)
        inputylayout.addWidget(self.inputy)
        inputylayout.addWidget(self.labelinputiny)
        inputylayout.addWidget(self.chooseunitybox)
        inputylayout.addWidget(self.choosedirectionybox)
        inputlayout.addLayout(inputylayout, 2, 0)

        # x
        inputxlayout = QHBoxLayout()
        inputxlayout.addWidget(self.labelinputx)
        inputxlayout.addWidget(self.inputx)
        inputxlayout.addWidget(self.labelinputinx)
        inputxlayout.addWidget(self.chooseunitxbox)
        inputxlayout.addWidget(self.choosedirectionxbox)
        inputlayout.addLayout(inputxlayout, 3, 0)

        # theta
        inputthetalayout = QHBoxLayout()
        inputthetalayout.addWidget(self.labelinputtheta)
        inputthetalayout.addWidget(self.inputtheta)
        inputthetalayout.addWidget(self.labelinputintheta)
        inputthetalayout.addWidget(self.choosedirectionthetabox)
        inputlayout.addLayout(inputthetalayout, 4, 0)

        # move buttons
        movelayout = QHBoxLayout()
        movelayout.addWidget(self.buttonmovestage)
        movelayout.addWidget(self.buttonstopstage)
        inputlayout.addLayout(movelayout, 5, 0)

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

        # create main layout and show it
        layout = QGridLayout()
        layout.addLayout(modebuttonlayout, 0, 0)
        layout.addLayout(inputlayout, 2, 0)
        layout.addLayout(measurementlayout, 3, 0)
        layout.addLayout(stagepostionlayout, 1, 0)
        layout.addLayout(stopperlayout, 1, 1)
        layout.addLayout(currentstatuslayout, 2, 1)
        layout.addWidget(self.resetbutton, 0, 1)

        self.setLayout(layout)
        self.setGeometry(1500, 200, 800, 300)
        self.setWindowTitle('Message box')
        self.show()

    # mode functions ---------------------------------------------------------------------------------------------------
    def cubicmagnetfunc(self):
        if self.triaxialmagnet is True:
            self.changemode()
        else:
            self.cubicactive()

    def triaxialmagnetfunc(self):
        if self.cubicmagnet is True:
            self.changemode()
        else:
            self.triaxialactive()

    def changemode(self):
        replychangemode = QMessageBox.question(self, 'Change Magnet?', 'Are you sure you want to exchange the magnet?',
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if replychangemode == QMessageBox.Yes:
            if self.triaxialmagnet is True:
                self.cubicactive()
            if self.cubicmagnet is True:
                self.triaxialactive()

    def cubicactive(self):
        print('cubic magnet in use')
        self.cubicmagnet = True
        self.triaxialmagnet = False
        self.currentstatusmagnet = 'cubic magnet activated'
        self.currentstatus.setText(self.currentstatusmagnet)
        #self.buttonmovestagex.setEnabled(False)        # if I disable the input here, I would not need to check in the
        #self.buttonmovestagetheta.setEnabled(True)     # input function...

    def triaxialactive(self):
        print('triaxial magnet in use')
        self.cubicmagnet = False
        self.triaxialmagnet = True
        self.currentstatusmagnet = 'triaxial magnet activated'
        self.currentstatus.setText(self.currentstatusmagnet)
        #self.buttonmovestagex.setEnabled(True)
        #self.buttonmovestagetheta.setEnabled(False)

    # input unit conversion for all three translational inputs ---------------------------------------------------------
    def chooseunitz(self):
        text = self.chooseunitzbox.currentText()
        if text == 'mm':
            self.unitz = 1000.0
        if text == 'um':
            self.unitz = 1.0

    def chooseunity(self):
        text = self.chooseunitybox.currentText()
        if text == 'mm':
            self.unity = 1000.0
        if text == 'um':
            self.unity = 1.0

    def chooseunitx(self):
        text = self.chooseunitxbox.currentText()
        if text == 'mm':
            self.unitx = 1000.0
        if text == 'um':
            self.unitx = 1.0

    # directions -------------------------------------------------------------------------------------------------------
    def changedirectionz(self):
        text = self.choosedirectionzbox.currentText()
        if text == 'forward':
            self.directionz = 0
        if text == 'backward':
            self.directionz = 1

    def changedirectiony(self):
        text = self.choosedirectionybox.currentText()
        if text == 'forward':
            self.directiony = 0
        if text == 'backward':
            self.directiony = 1

    def changedirectionx(self):
        text = self.choosedirectionxbox.currentText()
        if text == 'forward':
            self.directionx = 0
        if text == 'backward':
            self.directionx = 1

    def changedirectiontheta(self):
        text = self.choosedirectionthetabox.currentText()
        if text == 'forward':
            self.directiontheta = 0
        if text == 'backward':
            self.directiontheta = 1

    # move stage functions for all inputs. conversion and connection to Move Class -------------------------------------
    def movestage(self):
        # take all inputs, check and transform to correct format
        self.movestagezsteps = 0.0
        self.movestageysteps = 0.0
        self.movestagexsteps = 0.0
        self.movestagethetasteps = 0.0

        # z
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('z input empty')
            else:
                inputvaluez = float(newinput)
                movestagezby = inputvaluez*self.unitz   # in um
                print(movestagezby)
                mod = movestagezby % self.stepsizezy    # multiple of step size
                mod = round(mod, 3)

                if movestagezby >= self.stepsizezy:      # check minimum of input
                    if mod == 0:  # check multiple of step size
                        print('z length is possible.')
                        self.movestagezsteps = movestagezby / self.stepsizezy
                        self.sendx = '1:' + str(self.movestagezsteps) + ';' + str(self.directionz)
                    else:
                        print('Given z length not multiple of step size. Step size is 5um.')
                else:
                    print('Given z length is to small. Minimum 5um.')
        except:
            print('nope')

        # y
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('y input empty')
            else:
                inputvaluey = float(newinput)
                movestageyby = inputvaluey*self.unity   # in um
                print(movestageyby)
                mod = movestageyby % self.stepsizezy    # multiple of step size
                mod = round(mod, 3)

                if movestageyby >= self.stepsizezy:      # check minimum of input
                    if mod == 0:  # check multiple of step size
                        print('y length is possible.')
                        self.movestageysteps = movestageyby / self.stepsizezy
                        self.sendy = '&2:' + str(self.movestageysteps) + ';' + str(self.directiony)
                    else:
                        print('Given y length not multiple of step size. Step size is 5um.')
                else:
                    print('Given y length is to small. Minimum 5um.')
        except:
            print('nope')

        # x
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('z input empty')
            else:
                inputvaluex = float(newinput)
                if inputvaluex != 0:
                    if self.triaxialmagnet is True:
                        movestagexby = inputvaluex*self.unitx   # in um m
                        print(movestagexby)
                        mod = movestagexby % self.stepsizex     # multiple of step size
                        mod = round(mod, 3)

                        if movestagexby >= self.stepsizex:       # check minimum of input
                            if mod == 0:   # check multiple of step size
                                print('x length is possible.')
                                self.movestagexsteps = movestagexby / self.stepsizex
                                self.sendx = '&3:' + str(self.movestagexsteps) + ';' + str(self.directionx)
                            else:
                                print('Given x length not multiple of step size. Step size is 3.175um.')
                        else:
                            print('Given x length is to small. Minimum 3.175um.')
                    else:
                        print('Triaxial magnet not in use! Check the mode you are using')
        except:
            print('nope')

        # theta
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('z input empty')
            else:
                inputvaluetheta = float(newinput)
                if inputvaluetheta != 0:
                    if self.cubicmagnet is True:
                        movestagethetaby = inputvaluetheta
                        print(movestagethetaby)
                        mod = movestagethetaby % self.stepsizetheta
                        mod = round(mod, 3)

                        if movestagethetaby >= self.stepsizetheta:       # check minimum of input
                            if mod == 0:   # check multiple of step size
                                print('Angle is possible.')
                                self.movestagethetasteps = movestagethetaby / self.stepsizetheta
                                if self.movestagethetasteps > 200:
                                    self.movestagethetasteps -= 200
                                if self.positiontheta < 0:
                                    self.positiontheta += 200
                                self.sendtheta = '&4:' + str(self.movestagethetasteps) + ';' + str(self.directiontheta)
                            else:
                                print('Given angle not multiple of step size. Step size is 1.8°.')
                        else:
                            print('Given angle is to small. Minimum 1.8°.')
                    else:
                        print('Cubic magnet not in use! Check the mode you are using!')
        except:
            print('nope')

        # calling connector
        self.send = self.sendz + self.sendy + self.sendx + self.sendtheta
        self.connectmover()
        self.currentposition()

    def currentposition(self):

        if self.directionz == 0:
            self.positionz += self.movestagezsteps
        else:
            self.positionz -= self.movestagezsteps

        if self.directiony == 0:
            self.positiony += self.movestageysteps
        else:
            self.positiony -= self.movestageysteps

        if self.directionx == 0:
            self.positionx += self.movestagexsteps
        else:
            self.positionx -= self.movestagezsteps

        if self.directiontheta == 0:
            self.positiontheta += self.movestagethetasteps
        else:
            self.positiontheta -= self.movestagethetasteps

    def resetpressed(self):
        # make stage move to reset position
        self.send = 'r:' + str(self.positiontheta)

        self.positionz = 0.0
        self.positiony = 0.0
        self.positionx = 0.0
        self.positiontheta = 0.0
        self.cubicmagnet = False
        self.triaxialmagnet = False

        self.buttonmovestagex.setEnabled(True)
        self.buttonmovestagetheta.setEnabled(True)
        self.currentstatusmagnet = 'no magnet chosen'
        QApplication.processEvents()
        self.display()

    def connectmover(self):
        # calling mover Class, creating thread and call movetheta function
        self.buttonmovestage.setEnabled(False)
        self.mover = Move(self.send)
        self.moverthread = QThread(self, objectName='moverThread')
        self.mover.moveToThread(self.moverthread)
        self.mover.finished.connect(self.moverthread.quit)
        self.moverthread.started.connect(self.mover.move)
        self.moverthread.finished.connect(self.moverthread.deleteLater)
        self.moverthread.start()
        QApplication.processEvents()

        # when signal from arduino that motion is finished: enable buttonmovestage again
        # self.buttonmovestage.setEnabled(True)

    # display positions -----------------------------------------------------------------------------------------------
    def display(self):
        print(str(self.positionz) + ', ' + str(self.positiony) +
              ', ' + str(self.positionx) + ', ' + str(self.positiontheta))
        self.statusz.setText(str(self.positionz))
        self.statusy.setText(str(self.positiony))
        self.statusx.setText(str(self.positionx))
        self.statustheta.setText(str(self.positiontheta))
        self.currentstatus.setText(self.currentstatusmagnet)
        self.currentstatus.append('moving finished')

    # abort movement threads -------------------------------------------------------------------------------------------
    def stopstage(self):
        try:
            QApplication.processEvents()
            self.mover.stop()
            self.moverthread.quit()
            print('motion stopped')
        except:
            print('no motion running')

    # measurement controls ---------------------------------------------------------------------------------------------
    def startmeasurement(self):
        print('measurement started')
        self.measure = Measure()
        self.measurethread = QThread(self, objectName='MeasureThread')
        self.measure.moveToThread(self.measurethread)
        self.measure.finished.connect(self.measurethread.quit)

        if self.measureprogrammes == 'gs LAC':
            self.measurethread.started.connect(self.measure.movegsLAC)      # call function
            self.measurethread.finished.connect(self.measurethread.deleteLater)
            self.measurethread.start()
        if self.measureprogrammes == 'es LAC':
            self.measurethread.started.connect(self.measure.moveesLAC)       # call function
            self.measurethread.finished.connect(self.measurethread.deleteLater)
            self.measurethread.start()
        if self.measureprogrammes == '100G':
            self.measurethread.started.connect(self.measure.onehundred)   # call function
            self.measurethread.finished.connect(self.measurethread.deleteLater())
            self.measurethread.start()
        QApplication.processEvents()

    def abortmeasurment(self):
        try:
            print('measurement aborted')
            QApplication.processEvents()
            self.measure.stop()
            self.measurethread.quit()
        except:
            print('no measurement running')


# Move Class, controlling Arduino communication
class Move(QObject):

    finished = pyqtSignal()
    started = pyqtSignal()

    def __init__(self, send):
        super(Move, self).__init__()

        self.send = send

        self._isRunning = True
        self.arduino = serial.Serial('/dev/ttyACM0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
        print(self.arduino)
        print(self.arduino.isOpen())

    def move(self):
        # check if abortion is indicated
        if not self._isRunning:
            self.finished.emit()
        else:
            QApplication.processEvents()
            print('move stage')
            time.sleep(1)
            self.arduino.write(self.send.encode('ASCII'))

    def stop(self):
        self._isRunning = False
        print('stop motion')
        stopper = 's'
        self.arduino.write(stopper.encode('ASCII'))
        self.arduino.close()


# Measure Class, controlling and doing ex-ante-defined measurements
class Measure(QObject):

    finished = pyqtSignal()
    started = pyqtSignal()

    def __init__(self):
        super(Measure, self).__init__()

        self._isRunning = True

    def movegsLAC(self):

        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to ground state LAC')
            QApplication.processEvents()

    def moveesLAC(self):

        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to excited state LAC')
            QApplication.processEvents()

    def onehundred(self):

        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to 100 G')
            QApplication.processEvents()


    def stop(self):
        self._isRunning = False
        print('stop measurement')
