print('executing minion.minion_magnetstage_control')

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import time
import serial


# main Class with GUI and controller functions
class MinionMagnetStage(QWidget):
    def __init__(self, parent=None):
        super(MinionMagnetStage, self).__init__(parent)
        self.parent = parent

        # ComboBox lists
        self.units = ['mm', 'um']
        self.directions = ['forward', 'backward']
        self.measureprogrammes = ['gs LAC', 'es LAC', '100G']
        self.msr = ['1', '2', '4', '8', '16', '32', '64', '128']

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
        self.progress = 0
        self.pushz = 0
        self.pushy = 0
        self.pushx = 0
        self.pusht = 0
        self.msrz = 1
        self.msry = 1
        self.msrx = 1
        self.msrt = 1

        # import last saved stage position
        if os.path.isfile('last_position.txt') is True:
            self.last_position = open('last_position.txt', 'r+')
            positions = self.last_position.readlines()
            print(positions)
            self.positionz = float(positions[0])
            self.positiony = float(positions[1])
            self.positionx = float(positions[2])
            self.positiontheta = float(positions[3])
            #poszfloat = isinstance(self.positionz, float)
            #print('positionz is float:' + str(poszfloat))
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

        self.labelstatusstopperzstart = QLabel('z start')
        self.statusstopperzstart = QLineEdit()
        self.statusstopperzstart.setReadOnly(True)

        self.labelstatusstopperzend = QLabel('z end')
        self.statusstopperzend = QLineEdit()
        self.statusstopperzend.setReadOnly(True)

        self.labelstatusstopperystart = QLabel('y start')
        self.statusstopperystart = QLineEdit()
        self.statusstopperystart.setReadOnly(True)

        self.labelstatusstopperyend = QLabel('y end')
        self.statusstopperyend = QLineEdit()
        self.statusstopperyend.setReadOnly(True)

        self.labelstatusstopperxstart = QLabel('x start')
        self.statusstopperxstart = QLineEdit()
        self.statusstopperxstart.setReadOnly(True)

        self.labelstatusstopperxend = QLabel('x end')
        self.statusstopperxend = QLineEdit()
        self.statusstopperxend.setReadOnly(True)

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
        self.choosemsrz = QComboBox()
        self.choosemsrz.addItems(self.msr)
        self.choosemsrz.currentIndexChanged.connect(self.changemsrz)

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
        self.choosemsry = QComboBox()
        self.choosemsry.addItems(self.msr)
        self.choosemsry.currentIndexChanged.connect(self.changemsry)

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
        self.choosemsrx = QComboBox()
        self.choosemsrx.addItems(self.msr)
        self.choosemsrx.currentIndexChanged.connect(self.changemsrx)

        # theta
        self.labelinputtheta = QLabel(u'\u03B8')
        self.inputtheta = QLineEdit()
        self.labelinputintheta = QLabel('in °')
        self.choosedirectionthetabox = QComboBox()
        self.choosedirectionthetabox.addItems(self.directions)
        self.choosedirectionthetabox.currentIndexChanged.connect(self.changedirectiontheta)
        self.choosemsrtheta = QComboBox()
        self.choosemsrtheta.addItems(self.msr)
        self.choosemsrtheta.currentIndexChanged.connect(self.changemsrtheta)

        # reset
        self.resetbutton = QPushButton('Reset')
        self.resetbutton.clicked.connect(self.resetpressed)
        self.resetZbutton = QPushButton('Reset Z')
        self.resetZbutton.clicked.connect(self.resetZpressed)
        self.resetYbutton = QPushButton('Reset Y')
        self.resetYbutton.clicked.connect(self.resetYpressed)
        self.resetXbutton = QPushButton('Reset X')
        self.resetXbutton.clicked.connect(self.resetXpressed)
        self.resetTbutton = QPushButton('Reset T')
        self.resetTbutton.clicked.connect(self.resetTpressed)

        # -------- create measurement labels, Edits, Buttons -----------------------------------------------------------

        self.labelmeasurementheader = QLabel('choose pre-programmed path')
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

        # layout stopper
        stopperlayout = QVBoxLayout()

        # layout individual resets
        resetlayout = QHBoxLayout()
        resetlayout.addWidget(self.resetZbutton)
        resetlayout.addWidget(self.resetYbutton)
        resetlayout.addWidget(self.resetXbutton)
        resetlayout.addWidget(self.resetTbutton)
        stopperlayout.addLayout(resetlayout)

        # layout stopper status
        stopperlayout.addWidget(self.labelstatusstopper)

        stopperlayoutz = QHBoxLayout()
        stopperlayoutz.addWidget(self.labelstatusstopperzstart)
        stopperlayoutz.addWidget(self.statusstopperzstart)
        stopperlayoutz.addWidget(self.labelstatusstopperzend)
        stopperlayoutz.addWidget(self.statusstopperzend)
        stopperlayout.addLayout(stopperlayoutz)

        stopperlayouty = QHBoxLayout()
        stopperlayouty.addWidget(self.labelstatusstopperystart)
        stopperlayouty.addWidget(self.statusstopperystart)
        stopperlayouty.addWidget(self.labelstatusstopperyend)
        stopperlayouty.addWidget(self.statusstopperyend)
        stopperlayout.addLayout(stopperlayouty)

        stopperlayoutx = QHBoxLayout()
        stopperlayoutx.addWidget(self.labelstatusstopperxstart)
        stopperlayoutx.addWidget(self.statusstopperxstart)
        stopperlayoutx.addWidget(self.labelstatusstopperxend)
        stopperlayoutx.addWidget(self.statusstopperxend)
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
        inputzlayout.addWidget(self.choosemsrz)
        inputlayout.addLayout(inputzlayout, 1, 0)

        # y
        inputylayout = QHBoxLayout()
        inputylayout.addWidget(self.labelinputy)
        inputylayout.addWidget(self.inputy)
        inputylayout.addWidget(self.labelinputiny)
        inputylayout.addWidget(self.chooseunitybox)
        inputylayout.addWidget(self.choosedirectionybox)
        inputylayout.addWidget(self.choosemsry)
        inputlayout.addLayout(inputylayout, 2, 0)

        # x
        inputxlayout = QHBoxLayout()
        inputxlayout.addWidget(self.labelinputx)
        inputxlayout.addWidget(self.inputx)
        inputxlayout.addWidget(self.labelinputinx)
        inputxlayout.addWidget(self.chooseunitxbox)
        inputxlayout.addWidget(self.choosedirectionxbox)
        inputxlayout.addWidget(self.choosemsrx)
        inputlayout.addLayout(inputxlayout, 3, 0)

        # theta
        inputthetalayout = QHBoxLayout()
        inputthetalayout.addWidget(self.labelinputtheta)
        inputthetalayout.addWidget(self.inputtheta)
        inputthetalayout.addWidget(self.labelinputintheta)
        inputthetalayout.addWidget(self.choosedirectionthetabox)
        inputthetalayout.addWidget(self.choosemsrtheta)
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

        # layout individual resets
        resetlayout = QHBoxLayout()
        resetlayout.addWidget(self.resetZbutton)
        resetlayout.addWidget(self.resetYbutton)
        resetlayout.addWidget(self.resetXbutton)
        resetlayout.addWidget(self.resetTbutton)

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
        # self.buttonmovestagex.setEnabled(False)        # if I disable the input here, I would not need to check in the
        # self.buttonmovestagetheta.setEnabled(True)     # input function...

    def triaxialactive(self):
        print('triaxial magnet in use')
        self.cubicmagnet = False
        self.triaxialmagnet = True
        self.currentstatusmagnet = 'triaxial magnet activated'
        self.currentstatus.setText(self.currentstatusmagnet)
        # self.buttonmovestagex.setEnabled(True)
        # self.buttonmovestagetheta.setEnabled(False)

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

    # microstep resolution ---------------------------------------------------------------------------------------------
    def changemsrz(self):
        text = self.choosemsrz.currentText()
        if text == '1':
            self.msrz = 1
        if text == '2':
            self.msrz = 2
        if text == '4':
            self.msrz = 4
        if text == '8':
            self.msrz = 8
        if text == '16':
            self.msrz = 16
        if text == '32':
            self.msrz = 32
        if text == '64':
            self.msrz = 64
        if text == '128':
            self.msrz = 128

    def changemsry(self):
        text = self.choosemsry.currentText()
        if text == '1':
            self.msry = 1
        if text == '2':
            self.msry = 2
        if text == '4':
            self.msry = 4
        if text == '8':
            self.msry = 8
        if text == '16':
            self.msry = 16
        if text == '32':
            self.msry = 32
        if text == '64':
            self.msry = 64
        if text == '128':
            self.msry = 128

    def changemsrx(self):
        text = self.choosemsrx.currentText()
        if text == '1':
            self.msrx = 1
        if text == '2':
            self.msrx = 2
        if text == '4':
            self.msrx = 4
        if text == '8':
            self.msrx = 8
        if text == '16':
            self.msrx = 16
        if text == '32':
            self.msrx = 32
        if text == '64':
            self.msrx = 64
        if text == '128':
            self.msrx = 128

    def changemsrtheta(self):
        text = self.choosemsrtheta.currentText()
        if text == '1':
            self.msrt = 1
        if text == '2':
            self.msrt = 2
        if text == '4':
            self.msrt = 4
        if text == '8':
            self.msrt = 8
        if text == '16':
            self.msrt = 16
        if text == '32':
            self.msrt = 32
        if text == '64':
            self.msrt = 64
        if text == '128':
            self.msrt = 128

    # move stage functions for all inputs. conversion and connection to Move Class -------------------------------------
    def movestage(self):
        # take all inputs, check and transform to correct format
        self.movestagezsteps = 0.0
        self.movestageysteps = 0.0
        self.movestagexsteps = 0.0
        self.movestagethetasteps = 0.0
        self.measurementstatus.setRange(0, 100)
        self.measurementstatus.setValue(0)

        # z
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('z input empty')
            else:
                if self.directionz == 0 and self.endz is True or self.directionz == 1 and self.startz is True:
                    print('motion not possible. stage at stopper.')
                else:
                    inputvaluez = float(newinput)
                    movestagezby = inputvaluez*self.unitz   # in um
                    print(movestagezby)
                    stepsize = self.stepsizezy/self.msrz
                    mod = movestagezby % stepsize   # multiple of step size
                    mod = round(mod, 3)

                    if movestagezby >= stepsize:      # check minimum of input
                        if mod == 0:  # check multiple of step size
                            print('z length is possible.')
                            self.movestagezsteps = movestagezby / stepsize
                            self.sendx = '1:' + str(self.movestagezsteps) + ';' + str(self.directionz) + '&'
                        else:
                            print('Given z length not multiple of step size. Step size is' + str(stepsize) + 'um.')
                    else:
                        print('Given z length is to small. Minimum ' + str(stepsize) + 'um.')
        except:
            print('input distance')

        # y
        try:
            newinput = self.inputy.text()
            if not newinput:
                print('y input empty')
            else:
                if self.directiony == 0 and self.endy is True or self.directiony == 1 and self.starty is True:
                    print('motion not possible. stage at stopper.')
                else:
                    inputvaluey = float(newinput)
                    movestageyby = inputvaluey*self.unity   # in um
                    print(movestageyby)
                    stepsize = self.stepsizezy/self.msry
                    mod = movestageyby % stepsize    # multiple of step size
                    mod = round(mod, 3)

                    if movestageyby >= stepsize:      # check minimum of input
                        if mod == 0:  # check multiple of step size
                            print('y length is possible.')
                            self.movestageysteps = movestageyby / stepsize
                            self.sendy = '2:' + str(self.movestageysteps) + ';' + str(self.directiony) + '&'
                        else:
                            print('Given y length not multiple of step size. Step size is ' + str(stepsize) + 'um.')
                    else:
                        print('Given y length is to small. Minimum ' + str(stepsize) + 'um.')
        except:
            print('input distance')

        # x
        try:
            newinput = self.inputz.text()
            if not newinput:
                print('z input empty')
            else:
                if self.directionx == 0 and self.endx is True or self.directionx == 1 and self.startx is True:
                    print('motion not possible. stage at stopper.')
                else:
                    inputvaluex = float(newinput)
                    if inputvaluex != 0:
                        if self.triaxialmagnet is True:
                            movestagexby = inputvaluex*self.unitx   # in um m
                            print(movestagexby)
                            stepsize = self.stepsizex/self.msrx
                            mod = movestagexby % stepsize    # multiple of step size
                            mod = round(mod, 3)

                            if movestagexby >= stepsize:       # check minimum of input
                                if mod == 0:   # check multiple of step size
                                    print('x length is possible.')
                                    self.movestagexsteps = movestagexby / stepsize
                                    self.sendx = '3:' + str(self.movestagexsteps) + ';' + str(self.directionx) + '&'
                                else:
                                    print('Given x length not multiple of step size. Step size is ' + str(stepsize) + 'um.')
                            else:
                                print('Given x length is to small. Minimum ' + str(stepsize) + 'um.')
                        else:
                            print('Triaxial magnet not in use! Check the mode you are using')
        except:
            print('input distance')

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
                        stepsize = self.stepsizetheta/self.msrt
                        mod = movestagethetaby % stepsize
                        mod = round(mod, 3)

                        if movestagethetaby >= stepsize:       # check minimum of input
                            if mod == 0:   # check multiple of step size
                                print('Angle is possible.')
                                self.movestagethetasteps = movestagethetaby / stepsize
                                if self.movestagethetasteps > 200:
                                    self.movestagethetasteps -= 200
                                if self.positiontheta < 0:
                                    self.positiontheta += 200
                                self.sendtheta = '4:' + str(self.movestagethetasteps) + ';' + str(self.directiontheta) + '&'
                            else:
                                print('Given angle not multiple of step size. Step size is ' + str(stepsize) + '°.')
                        else:
                            print('Given angle is to small. Minimum ' + str(stepsize) + '°.')
                    else:
                        print('Cubic magnet not in use! Check the mode you are using!')
        except:
            print('input distance')

        # calling connector
        self.send = self.sendz + self.sendy + self.sendx + self.sendtheta
        self.connectmover()

    def resetpressed(self):
        # make stage move to reset position
        self.send = '5:1;' + str(self.positiontheta)
        self.connectmover()

        self.positionz = 0.0
        self.positiony = 0.0
        self.positionx = 0.0
        self.positiontheta = 0.0
        self.cubicmagnet = False
        self.triaxialmagnet = False

        self.buttonmovestage.setEnabled(True)
        self.buttonmovestage.setEnabled(True)
        self.currentstatusmagnet = 'no magnet chosen'
        self.QApplication.processEvents()
        self.display()

    def resetZpressed(self):

        self.send = '5:2;1'
        self.connectmover()
        self.positionz = 0.0
        self.QApplication.processEvents()
        self.display()

    def resetYpressed(self):

        self.send = '5:2;2'
        self.connectmover()
        self.positiony = 0.0
        self.QApplication.processEvents()
        self.display()

    def resetXpressed(self):

        self.send = '5:2;3'
        self.connectmover()
        self.positionx = 0.0
        self.QApplication.processEvents()
        self.display()

    def resetTpressed(self):

        self.send = '5:2;4'
        self.connectmover()
        self.positiontheta = 0.0
        self.QApplication.processEvents()
        self.display()

    def connectmover(self):
        # calling mover Class, creating thread and call movetheta function
        #self.buttonmovestage.setEnabled(False)
        self.mover = Move(self.send)
        self.moverthread = QThread(self, objectName='moverThread')
        self.mover.moveToThread(self.moverthread)
        self.mover.finished.connect(self.moverthread.quit)
        self.mover.push.connect(self.updatepositions)
        self.moverthread.started.connect(self.mover.move)
        self.moverthread.finished.connect(self.moverthread.deleteLater)
        self.mover.display.connect(self.display)
        self.mover.stopper.connect(self.updatestopper)
        self.moverthread.start()
        QApplication.processEvents()
        #self.buttonmovestage.setEnabled(True)

        # when signal from arduino that motion is finished: enable buttonmovestage again
        # self.buttonmovestage.setEnabled(True)

    # receive and display positions and stopper values -----------------------------------------------------------------
    @pyqtSlot(float, float, float, float)
    def updatepositions(self, pushz, pushy, pushx, pusht):
        # print(pushz)                      # delete later; variable check
        # print('pushz is float:' + str(isinstance(pushz, float)))
        # print('positionz is float:' + str(isinstance(self.positionz, float)))
        self.pushz = pushz
        self.pushy = pushy
        self.pushx = pushx
        self.pusht = pusht
        progresssteps = pushz + pushy + pushx + pusht
        totalsteps = self.movestagezsteps + self.movestageysteps + self.movestageysteps + self.movestagethetasteps
        progress = (progresssteps / totalsteps) * 100
        self.measurementstatus.setValue(progress)

    @pyqtSlot()
    def display(self):
        if self.directionz == 0:
            self.positionz += self.pushz
        else:
            self.positionz -= self.pushz
        if self.directiony == 0:
            self.positiony += self.pushy
        else:
            self.positiony -= self.pushy
        if self.directionx == 0:
            self.positionx += self.pushx
        else:
            self.positionx -= self.pushx
        if self.directiontheta == 0:
            self.positiontheta += self.pusht
        else:
            self.positiontheta -= self.pusht

        # display positions
        print(str(self.positionz) + ', ' + str(self.positiony) +
              ', ' + str(self.positionx) + ', ' + str(self.positiontheta))
        self.statusz.setText(str(self.positionz))
        self.statusy.setText(str(self.positiony))
        self.statusx.setText(str(self.positionx))
        self.statustheta.setText(str(self.positiontheta))
        self.currentstatus.setText(self.currentstatusmagnet)

        # display stopper status
        self.statusstopperzstart.setText(str(self.startz))
        self.statusstopperzend.setText(str(self.endz))
        self.statusstopperystart.setText(str(self.starty))
        self.statusstopperyend.setText(str(self.endy))
        self.statusstopperxstart.setText(str(self.startx))
        self.statusstopperxend.setText(str(self.endx))

        self.currentstatus.append('moving finished')

    @pyqtSlot(bool, bool, bool, bool, bool, bool)
    def updatestopper(self, stopZstart, stopZend, stopYstart, stopYend, stopXstart, stopXend):
        # read in and update stopper values
        self.endz = stopZend
        self.startz = stopZstart
        self.endy = stopYend
        self.starty = stopYstart
        self.endx = stopXend
        self.startx = stopXstart

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
        self.measure = Measure(self.positiontheta)
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
        self.QApplication.processEvents()

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
    display = pyqtSignal()
    push = pyqtSignal(float, float, float, float)
    stopper = pyqtSignal(bool, bool, bool, bool, bool, bool)

    def __init__(self, send, ):
        super(Move, self).__init__()

        self.send = send
        self._isRunning = True

        self.pushz = 0.0
        self.pushy = 0.0
        self.pushx = 0.0
        self.pusht = 0.0
        self.stopZstart = False
        self.stopZend = False
        self.stopYstart = False
        self.stopYend = False
        self.stopXstart = False
        self.stopXend = False
        self.stopTstart = False
        self.stopTend = False

        self.arduino = serial.Serial('/dev/ttyACM2', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
        print(self.arduino)
        print(self.arduino.isOpen())

    def move(self):
        # check if abortion is indicated
        if not self._isRunning:
            self.finished.emit()
        else:
            QApplication.processEvents()
            print('move stage')
            print(self.send)
            time.sleep(1)
            self.arduino.write(self.send.encode('ASCII'))
            time.sleep(1)
            moveit = True

            while moveit is True:
                received = self.arduino.readline()
                time.sleep(0.001)
                if received == b'pushz\r\n':
                    self.pushz += 1
                if received == b'pushy\r\n':
                    self.pushy += 1
                if received == b'pushx\r\n':
                    self.pushx += 1
                if received == b'pusht\r\n':
                    self.pusht += 1
                if received == b'stopZstart\r\n':
                    self.stopZstart = True
                else:
                    self.stopZstart = False
                if received == b'stopZend\r\n':
                    self.stopZend = True
                else:
                    self.stopZend = False
                if received == b'stopYstart\r\n':
                    self.stopYstart = True
                else:
                    self.stopYstart = False
                if received == b'stopYend\r\n':
                    self.stopYend = True
                else:
                    self.stopYend = False
                if received == b'stopXstart\r\n':
                    self.stopXstart = True
                else:
                    self.stopXstart = False
                if received == b'stopXend\r\n':
                    self.stopXend = True
                else:
                    self.stopXend = False
                if received == b'stopTstart\r\n':
                    self.stopTstart = True
                else:
                    self.stopTstart = False
                if received == b'stopTend\r\n':
                    self.stopTend = True
                else:
                    self.stopTend = False
                if received == b'motion finished\r\n':
                    print('motion finished')
                    moveit = False

                    self.stop()
                self.push.emit(self.pushz, self.pushy, self.pushx, self.pusht)
                self.stopper.emit(self.stopZstart, self.stopZend, self.stopYstart, self.stopYend,
                                  self.stopXstart, self.stopXend)

    def stop(self):
        self._isRunning = False
        print('stop motion')
        QApplication.processEvents()
        opened = self.arduino.isOpen()
        if opened is True:
            stopper = 's'
            self.arduino.write(stopper.encode('ASCII'))
            self.arduino.close()
        self.display.emit()
        self.finished.emit()


# Measure Class, controlling and doing ex-ante-defined measurements
class Measure(QObject):

    finished = pyqtSignal()
    started = pyqtSignal()

    def __init__(self, positiontheta):
        super(Measure, self).__init__()

        self._isRunning = True
        self.send = ''
        self.positiontheta = positiontheta

    def fullreset(self):
        self.send = '5:1;' + str(self.positiontheta)
        self.connectmover()

    def movegsLAC(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to ground state LAC')
            self.QApplication.processEvents()
            self.fullreset()

            self.send = ''
            self.connectmover()

    def moveesLAC(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to excited state LAC')
            self.QApplication.processEvents()
            self.fullreset()

            self.send = ''
            self.connectmover()

    def onehundred(self):
        if not self._isRunning:
            self.finished.emit()
        else:
            print('move to 100 G')
            self.QApplication.processEvents()
            self.fullreset()

            self.send = ''
            self.connectmover()

    def stop(self):
        self._isRunning = False
        print('stop measurement')

    def connectmover(self):
        self.mover = Move(self.send)
        self.moverthread = QThread(self, objectName='moverThread')
        self.mover.moveToThread(self.moverthread)
        self.mover.finished.connect(self.moverthread.quit)
        self.moverthread.started.connect(self.mover.move)
        self.moverthread.finished.connect(self.moverthread.deleteLater)
        self.moverthread.start()
        self.QApplication.processEvents()

    @pyqtSlot()
    def checkfinish(self):
        print('finished')

    @pyqtSlot(float, float, float, float)
    def updateposition(self):
        print('update')
