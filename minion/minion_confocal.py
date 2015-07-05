"""
confocal module that creates the navigation widget
"""
print('executing minion.minion_confocal')

import os
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import matplotlib as mpl
import matplotlib.style as mplstyle
import serial
from ctypes import *

mpl.use("Qt5Agg")
mplstyle.use('ggplot')  # 'ggplot', 'dark_background', 'bmh', 'fivethirtyeight'

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MinionConfocalUi(QWidget):
    def __init__(self, hardware_counter, counter, hardware_laser, laser, hardware_stage, stage, stagelib):
        super(MinionConfocalUi, self).__init__()

        self.hardware_counter = hardware_counter
        self.hardware_laser = hardware_laser
        self.hardware_stage = hardware_stage
        if self.hardware_counter is True:
            self.counter = counter
        if self.hardware_laser is True:
            self.laser = laser
        if hardware_stage is True:
            self.stage = stage
            self.stagelib = stagelib

        # self.hardware_laser = True
        # self.hardware_counter = True
        # self.hardware_stage = True

        self.scanmodi = ['xy', 'xz', 'yz']
        self.scanmode = 'xy'

        # set backup initial variables
        self.xmin = 5.0
        self.xmax = 10.0
        self.xpos = 10
        self.ymin = 5.0
        self.ymax = 10.0
        self.ypos = 10
        self.zmin = 0.0
        self.zmax = 50.0
        self.zpos = 25.0
        self.xlim = 75.0
        self.ylim = 75.0
        self.zlim = 50.0

        self.resolution1 = 21
        self.resolution2 = 21
        self.mapdata = np.zeros((self.resolution1, self.resolution2))
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        self.settlingtime = 0.01  # pos error about 10nm - 0.01 results in about 30 nm
        self.counttime = 0.005
        self.laserpowernew = 10.0
        self.laserpowermin = 0.001
        self.laserpowermax = 200.
        self.laserpowertimer = QTimer()
        self.laserpowertimer.timeout.connect(self.checklaserpower)
        self.laserpowertimer.setInterval(1000)
        self.laserpowertimer.start()

        # TODO - move hardware initiation to minion_main and spread handles - PRIORITY

        if self.hardware_stage is True:
            # define restypes that are not standard (INT)
            self.stagelib.MCL_SingleReadN.restype = c_double
            self.stagelib.MCL_MonitorN.restype = c_double
            self.stagelib.MCL_GetCalibration.restype = c_double

            # get stage limits - recall X=2, Y=1, Z=3, lower limits all 0 - and set initial position
            self.xlim = self.stagelib.MCL_GetCalibration(2, self.stage)
            self.ylim = self.stagelib.MCL_GetCalibration(1, self.stage)
            self.zlim = self.stagelib.MCL_GetCalibration(3, self.stage)
            self.xlim, self.ylim, self.zlim = self.xlim-1., self.ylim-1., self.zlim-1.  # for safety reason
            self.xpos = self.stagelib.MCL_SingleReadN(2, self.stage)
            self.ypos = self.stagelib.MCL_SingleReadN(1, self.stage)
            self.zpos = self.stagelib.MCL_SingleReadN(3, self.stage)
            self.xmin = self.xpos - 5.
            self.ymin = self.ypos - 5.
            self.zmin = self.zpos - 5.
            self.xmax = self.xpos + 5.
            self.ymax = self.ypos + 5.
            self.zmax = self.zpos + 5.
            print('\t stage position updated')
        else:
            print('stage not found')

        self.uisetup()
        self.updatemap(self.mapdata, 0)
        self.xslidervaluetextchanged()
        self.yslidervaluetextchanged()
        self.sliderminmaxtextchanged()

    def __del__(self):
        self.laserpowertimer.stop()
        if self.hardware_laser is True:
            self.laser.close()
            print(self.laser)
        if self.hardware_counter is True:
            self.counter.close()
            print(self.counter)
        if self.hardware_stage is True:
            self.stagelib.MCL_ReleaseHandle(self.stage)
            print('stage handle released')

    def uisetup(self):
        # create map canvas
        self.mapfigure = Figure()
        self.mapcanvas = FigureCanvas(self.mapfigure)
        self.mapcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mapcanvas.setMinimumSize(50, 50)
        self.toolbar = NavigationToolbar(self.mapcanvas, self)
        self.mapaxes = self.mapfigure.add_subplot(111)
        self.mapaxes.hold(False)

        # self.mapdata = np.random.rand(100, 100)*100  #delete later when datastream works

        self.map = self.mapaxes.matshow(self.mapdata, origin='lower', extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.colorbar = self.mapfigure.colorbar(self.map, fraction=0.046, pad=0.04, cmap=mpl.cm.rainbow)
        self.colorbar.formatter.set_scientific(True)
        self.colorbar.formatter.set_powerlimits((0, 3))
        self.colorbar.update_ticks()
        self.mapaxes.xaxis.set_ticks_position('bottom')
        self.mapaxes.xaxis.set_tick_params(direction='out')
        self.mapaxes.yaxis.set_ticks_position('left')
        self.mapaxes.yaxis.set_tick_params(direction='out')

        # initialize cursor
        self.hlinecursor = self.mapaxes.axhline(color='w', linewidth=2)
        self.hlinecursor.set_ydata(self.xpos)
        self.vlinecursor = self.mapaxes.axvline(color='w', linewidth=2)
        self.vlinecursor.set_xdata(self.ypos)

        # create control area
        self.resolutionlabel = QLabel('resolution:')
        self.resolution1text = QSpinBox()
        self.resolution1text.setRange(1, 1000)
        self.resolution1text.setValue(self.resolution1)
        self.resolution1text.editingFinished.connect(self.resolutiontextchanged)
        self.resolution2text = QSpinBox()
        self.resolution2text.setRange(1, 1000)
        self.resolution2text.setValue(self.resolution2)
        self.resolution2text.editingFinished.connect(self.resolutiontextchanged)

        self.colorminlabel = QLabel('color_min')
        self.colormintext = QSpinBox()
        self.colormintext.setRange(0, 10000000)
        self.colormintext.setValue(self.colormin)
        self.colormintext.editingFinished.connect(self.colormintextchanged)
        self.colormaxlabel = QLabel('color_max')
        self.colormaxtext = QSpinBox()
        self.colormaxtext.setRange(0, 10000000)
        self.colormaxtext.setValue(self.colormax)
        self.colormaxtext.editingFinished.connect(self.colormaxtextchanged)
        self.colorautoscale = QPushButton('autoscale')
        self.colorautoscale.pressed.connect(self.colorautoscalepress)

        self.slidermintextlabel = QLabel('min')
        self.slidermaxtextlabel = QLabel('max')
        self.sliderpostextlabel = QLabel('pos')

        # create x,y,z sliders and textedits
        # X-SLIDER
        self.xsliderlabel = QLabel('x [µm]:')
        self.xslidermintext = QDoubleSpinBox()
        self.xslidermintext.setRange(0, 100)
        self.xslidermintext.setValue(self.xmin)
        self.xslidermintext.setToolTip('xmin')
        self.xslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.xslidermaxtext = QDoubleSpinBox()
        self.xslidermaxtext.setRange(0, 100)
        self.xslidermaxtext.setValue(self.xmax)
        self.xslidermaxtext.setToolTip('xmax')
        self.xslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.xslider = QSlider(Qt.Horizontal, self)
        self.xslider.setMinimum(self.xmin*100)
        self.xslider.setMaximum(self.xmax*100)
        self.xslider.setTickInterval(int((self.xmax-self.xmin)/10*100))
        self.xslider.setValue(int((self.xmin+self.xmax)/2*100))
        self.xslider.setTickPosition(QSlider.TicksBelow)
        self.xslider.valueChanged.connect(self.xsliderchanged)

        self.xslidervaluetext = QDoubleSpinBox()
        self.xslidervaluetext.setRange(0, 100)
        self.xslidervaluetext.setDecimals(2)
        self.xslidervaluetext.setValue(self.xslider.value()/100)
        self.xslidervaluetext.setToolTip('xpos')
        self.xslidervaluetext.editingFinished.connect(self.xslidervaluetextchanged)

        # Y-SLIDER
        self.ysliderlabel = QLabel('y [µm]:')
        self.yslidermintext = QDoubleSpinBox()
        self.yslidermintext.setRange(0, 100)
        self.yslidermintext.setValue(self.ymin)
        self.yslidermintext.setToolTip('ymin')
        self.yslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.yslidermaxtext = QDoubleSpinBox()
        self.yslidermaxtext.setRange(0, 100)
        self.yslidermaxtext.setValue(self.ymax)
        self.yslidermaxtext.setToolTip('ymin')
        self.yslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.yslider = QSlider(Qt.Horizontal, self)
        self.yslider.setMinimum(self.ymin*100)
        self.yslider.setMaximum(self.ymax*100)
        self.yslider.setTickInterval(int((self.ymax-self.ymin)/10*100))
        self.yslider.setValue(int((self.ymin+self.ymax)/2*100))
        self.yslider.setTickPosition(QSlider.TicksBelow)
        self.yslider.valueChanged.connect(self.ysliderchanged)

        self.yslidervaluetext = QDoubleSpinBox()
        self.yslidervaluetext.setRange(0, 100)
        self.yslidervaluetext.setDecimals(2)
        self.yslidervaluetext.setValue(self.yslider.value()/100)
        self.yslidervaluetext.setToolTip('ypos')
        self.yslidervaluetext.editingFinished.connect(self.yslidervaluetextchanged)

        # Z-SLIDER
        self.zsliderlabel = QLabel('z [µm]:')
        self.zslidermintext = QDoubleSpinBox()
        self.zslidermintext.setRange(0, 100)
        self.zslidermintext.setValue(self.ymin)
        self.zslidermintext.setToolTip('zmin')
        self.zslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.zslidermaxtext = QDoubleSpinBox()
        self.zslidermaxtext.setRange(0, 100)
        self.zslidermaxtext.setValue(self.zmax)
        self.zslidermaxtext.setToolTip('zmax')
        self.zslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.zslider = QSlider(Qt.Horizontal, self)
        self.zslider.setMinimum(self.zmin*100)
        self.zslider.setMaximum(self.zmax*100)
        self.zslider.setTickInterval(int((self.zmax-self.zmin)/10*100))
        self.zslider.setValue(int((self.zmin+self.zmax)/2*100))
        self.zslider.setTickPosition(QSlider.TicksBelow)
        self.zslider.valueChanged.connect(self.zsliderchanged)

        self.zslidervaluetext = QDoubleSpinBox()
        self.zslidervaluetext.setRange(0, 100)
        self.zslidervaluetext.setDecimals(2)
        self.zslidervaluetext.setValue(self.zslider.value()/100)
        self.zslidervaluetext.setToolTip('zpos')
        self.zslidervaluetext.editingFinished.connect(self.zslidervaluetextchanged)

        # create start, stop, save, progressbar
        self.mapstart = QPushButton('start\nscan')
        self.mapstart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mapstart.clicked.connect(self.mapstartclicked)
        self.mapstop = QPushButton('stop\nscan')
        self.mapstop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mapstop.clicked.connect(self.mapstopclicked)
        self.scanprogress = QProgressBar()
        self.scanprogresslabel = QLabel('est. t:')

        self.mapsavenametext = QLineEdit()
        self.mapsavenametext.setText('filename')
        self.mapsave = QPushButton('save scan')
        self.mapsave.clicked.connect(self.mapsaveclicked)

        # count and settling time
        self.settlingtimelabel = QLabel('t_settle [ms]:')
        self.settlingtimetext = QDoubleSpinBox()
        self.settlingtimetext.setRange(0, 1000)
        self.settlingtimetext.setValue(int(self.settlingtime*1000))
        self.settlingtimetext.editingFinished.connect(self.timetextchanged)
        self.counttimelabel = QLabel('t_count [ms]:')
        self.counttimetext = QDoubleSpinBox()
        self.counttimetext.setRange(0, 1000)
        self.counttimetext.setValue(int(self.counttime*1000))
        self.counttimetext.editingFinished.connect(self.timetextchanged)

        # laser control widgets
        self.laserpowerinfolabel = QLabel('power [mW]:')
        self.laserpowerinfo = QDoubleSpinBox()
        self.laserpowerinfo.setReadOnly(True)

        self.laserpowersetlabel = QLabel('set power [mW]:')
        self.laserpowerset = QDoubleSpinBox()
        self.laserpowerset.setRange(self.laserpowermin, self.laserpowermax)
        self.laserpowerset.setValue(self.laserpowernew)
        self.laserpowerset.editingFinished.connect(self.setlaserpower)

        # create horizontal line widgets
        self.hline = QFrame()
        self.hline.setFrameShape(QFrame.HLine)
        self.hline.setFrameShadow(QFrame.Sunken)
        self.hline1 = QFrame()
        self.hline1.setFrameShape(QFrame.HLine)
        self.hline1.setFrameShadow(QFrame.Sunken)

        # select scan modus
        self.scanselect = QComboBox()
        self.scanselect.addItems(self.scanmodi)
        self.scanselect.currentIndexChanged.connect(self.scanmodechange)
        self.scanselectlabel = QLabel('scan mode')

        # create layout
        confocal_layout = QGridLayout()
        confocal_layout.addWidget(self.mapcanvas, 0, 0, 10, 11)
        confocal_layout.addWidget(self.toolbar, 10, 0, 1, 11)

        resscancolor = QHBoxLayout()
        resscancolor.setAlignment(Qt.AlignLeft)
        resscancolor.addWidget(self.resolutionlabel)
        resscancolor.addWidget(self.resolution1text)
        resscancolor.addWidget(self.resolution2text)
        resscancolor.addWidget(self.scanselectlabel)
        resscancolor.addWidget(self.scanselect)
        resscancolor.addWidget(self.colorminlabel)
        resscancolor.addWidget(self.colormintext)
        resscancolor.addWidget(self.colormaxlabel)
        resscancolor.addWidget(self.colormaxtext)
        resscancolor.addWidget(self.colorautoscale)
        confocal_layout.addLayout(resscancolor, 11, 0, 1, 11)

        timeslaser = QHBoxLayout()
        timeslaser.setAlignment(Qt.AlignLeft)
        timeslaser.addWidget(self.settlingtimelabel)
        timeslaser.addWidget(self.settlingtimetext)
        timeslaser.addWidget(self.counttimelabel)
        timeslaser.addWidget(self.counttimetext)

        timeslaser.addWidget(self.laserpowerinfolabel)
        timeslaser.addWidget(self.laserpowerinfo)
        timeslaser.addWidget(self.laserpowersetlabel)
        timeslaser.addWidget(self.laserpowerset)
        confocal_layout.addLayout(timeslaser, 12, 0, 1, 11)

        confocal_layout.addWidget(self.hline, 13, 0, 1, 11)

        xsliderbox = QHBoxLayout()
        xsliderbox.setAlignment(Qt.AlignLeft)
        xsliderbox.addWidget(self.xsliderlabel)
        xsliderbox.addWidget(self.xslidermintext)
        xsliderbox.addWidget(self.xslider)
        xsliderbox.addWidget(self.xslidermaxtext)
        xsliderbox.addWidget(self.xslidervaluetext)
        confocal_layout.addLayout(xsliderbox, 14, 0, 1, 11)

        ysliderbox = QHBoxLayout()
        ysliderbox.addWidget(self.ysliderlabel)
        ysliderbox.addWidget(self.yslidermintext)
        ysliderbox.addWidget(self.yslider)
        ysliderbox.addWidget(self.yslidermaxtext)
        ysliderbox.addWidget(self.yslidervaluetext)
        confocal_layout.addLayout(ysliderbox, 15, 0, 1, 11)

        zsliderbox = QHBoxLayout()
        zsliderbox.addWidget(self.zsliderlabel)
        zsliderbox.addWidget(self.zslidermintext)
        zsliderbox.addWidget(self.zslider)
        zsliderbox.addWidget(self.zslidermaxtext)
        zsliderbox.addWidget(self.zslidervaluetext)
        confocal_layout.addLayout(zsliderbox, 16, 0, 1, 11)

        confocal_layout.addWidget(self.hline1, 17, 0, 1, 11)

        scanstartstopstatus = QHBoxLayout()
        self.mapstart.setFixedHeight(50)
        scanstartstopstatus.addWidget(self.mapstart)
        self.mapstop.setFixedHeight(50)
        scanstartstopstatus.addWidget(self.mapstop)
        scanstartstopstatus.addWidget(self.scanprogress)
        scanstartstopstatus.addWidget(self.scanprogresslabel)
        scanstartstopstatus.addWidget(self.mapsavenametext)
        scanstartstopstatus.addWidget(self.mapsave)
        confocal_layout.addLayout(scanstartstopstatus, 19, 0, 1, 11)

        confocal_layout.setSpacing(2)
        self.setLayout(confocal_layout)

    def xsliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.xpos = self.xslider.value()/100
        self.xslidervaluetext.setValue(self.xpos)
        if self.scanmode == 'xy' or self.scanmode == 'xz':
            self.vlinecursor.set_xdata(self.xpos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xpos), 2, self.stage)

    def xslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.xpos = self.xslidervaluetext.value()
        if not self.xmin <= self.xpos <= self.xmax:
            self.xpos = (self.xmin+self.xmax)/2.
            self.xslidervaluetext.setValue(self.xpos)
        self.xslider.setValue(self.xpos*100)
        if self.scanmode == 'xy' or self.scanmode == 'xz':
            self.vlinecursor.set_xdata(self.xpos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xpos), 2, self.stage)

    def sliderminmaxtextchanged(self):
        self.xmin = self.xslidermintext.value()
        self.xmax = self.xslidermaxtext.value()
        self.ymin = self.yslidermintext.value()
        self.ymax = self.yslidermaxtext.value()
        self.zmin = self.zslidermintext.value()
        self.zmax = self.zslidermaxtext.value()

        # check for stage limit violations
        if not 0. <= self.xmin < self.xmax:
            self.xmin = 0.
            self.xslidermintext.setValue(self.xmin)
        if not self.xmin < self.xmax < self.xlim:
            self.xmax = self.xlim
            self.xslidermaxtext.setValue(self.xmax)
        if not 0. <= self.ymin < self.ymax:
            self.ymin = 0.
            self.yslidermintext.setValue(self.ymin)
        if not self.ymin < self.ymax < self.ylim:
            self.ymax = self.ylim
            self.yslidermaxtext.setValue(self.ymax)
        if not 0. <= self.zmin < self.zmax:
            self.zmin = 0.
            self.zslidermintext.setValue(self.zmin)
        if not self.zmin < self.zmax < self.zlim:
            self.zmax = self.zlim
            self.zslidermaxtext.setValue(self.zmax)

        if self.scanmode == 'xy':
            self.mapaxes.set_xlim(self.xmin, self.xmax)
            self.mapaxes.set_ylim(self.ymin, self.ymax)
            self.mapcanvas.draw()
        elif self.scanmode == 'xz':
            self.mapaxes.set_xlim(self.xmin, self.xmax)
            self.mapaxes.set_ylim(self.zmin, self.zmax)
            self.mapcanvas.draw()
        elif self.scanmode == 'yz':
            self.mapaxes.set_xlim(self.ymin, self.ymax)
            self.mapaxes.set_ylim(self.zmin, self.zmax)
            self.mapcanvas.draw()

        self.xslider.setMinimum(self.xmin*100)
        self.xslider.setMaximum(self.xmax*100)
        self.xslider.setTickInterval(int((self.xmax-self.xmin)/10*100))
        self.yslider.setMinimum(self.ymin*100)
        self.yslider.setMaximum(self.ymax*100)
        self.yslider.setTickInterval(int((self.ymax-self.ymin)/10*100))
        self.zslider.setMinimum(self.zmin*100)
        self.zslider.setMaximum(self.zmax*100)
        self.zslider.setTickInterval(int((self.zmax-self.zmin)/10*100))

        # check if slider pos get out of its boundaries - if not center pos between min and max
        if not self.xmin < self.xpos < self.xmax:
            self.xslider.setValue(int((self.xmin+self.xmax)/2*100))
        if not self.ymin < self.ypos < self.ymax:
            self.yslider.setValue(int((self.ymin+self.ymax)/2*100))
        if not self.zmin < self.zpos < self.zmax:
            self.zslider.setValue(int((self.zmin+self.zmax)/2*100))

    def ysliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.ypos = self.yslider.value()/100
        self.yslidervaluetext.setValue(self.ypos)
        if self.scanmode == 'xy':
            self.hlinecursor.set_ydata(self.ypos)
            self.mapcanvas.draw()
        elif self.scanmode == 'yz':
            self.vlinecursor.set_xdata(self.ypos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status1 = self.stagelib.MCL_SingleWriteN(c_double(self.ypos), 1, self.stage)

    def yslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.ypos = self.yslidervaluetext.value()
        if not self.ymin <= self.ypos <= self.ymax:
            self.ypos = (self.ymin+self.ymax)/2.
            self.yslidervaluetext.setValue(self.ypos)
        self.yslider.setValue(self.ypos*100)
        if self.scanmode == 'xy':
            self.hlinecursor.set_ydata(self.ypos)
            self.mapcanvas.draw()
        elif self.scanmode == 'yz':
            self.vlinecursor.set_xdata(self.ypos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status1 = self.stagelib.MCL_SingleWriteN(c_double(self.ypos), 1, self.stage)

    def zsliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.zpos = self.zslider.value()/100
        self.zslidervaluetext.setValue(self.zpos)
        if self.scanmode == 'xz':
            self.hlinecursor.set_ydata(self.zpos)
            self.mapcanvas.draw()
        elif self.scanmode == 'yz':
            self.hlinecursor.set_ydata(self.zpos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status3 = self.stagelib.MCL_SingleWriteN(c_double(self.zpos), 3, self.stage)

    def zslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.zpos = self.zslidervaluetext.value()
        if not self.zmin <= self.zpos <= self.zmax:
            self.zpos = (self.zmin+self.zmax)/2.
            self.zslidervaluetext.setValue(self.zpos)
        self.zslider.setValue(self.zpos*100)
        if self.scanmode == 'xz':
            self.hlinecursor.set_ydata(self.zpos)
            self.mapcanvas.draw()
        elif self.scanmode == 'yz':
            self.hlinecursor.set_ydata(self.zpos)
            self.mapcanvas.draw()
        if self.hardware_stage is True:
            self.status3 = self.stagelib.MCL_SingleWriteN(c_double(self.zpos), 3, self.stage)

    def resolutiontextchanged(self):
        self.resolution1 = self.resolution1text.value()
        self.resolution2 = self.resolution2text.value()

    def colormintextchanged(self):
        self.colormin = self.colormintext.value()
        self.map.set_clim(vmin=self.colormin)
        self.colorbar.set_clim(vmin=self.colormin)
        self.colorbar.draw_all()
        self.mapcanvas.draw()

    def colormaxtextchanged(self):
        self.colormax = self.colormaxtext.value()
        self.map.set_clim(vmax=self.colormax)
        self.colorbar.set_clim(vmax=self.colormax)
        self.colorbar.draw_all()
        self.mapcanvas.draw()

    def colorautoscalepress(self):
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        self.colormintext.setValue(self.colormin)
        self.colormaxtext.setValue(self.colormax)
        self.map.set_clim(vmin=self.colormin, vmax=self.colormax)
        self.colorbar.set_clim(vmin=self.colormin, vmax=self.colormax)
        self.colorbar.draw_all()
        self.mapcanvas.draw()

    def mapstartclicked(self):
        print("[%s] start scan" % QThread.currentThread().objectName())
        self.scanprogress.setRange(0, 100)
        self.scanprogress.setValue(0)

        if self.hardware_stage is True and self.hardware_counter is True:
            self.aquisition = MinionColfocalMapDataAquisition(self.resolution1, self.resolution2, self.settlingtime, self.counttime, self.xmin, self.xmax, self. ymin, self.ymax, self.zmin, self.zmax, self.counter, self.stagelib, self.stage, self.scanmode, self.xpos, self.ypos, self.zpos)
            self.confocalthread = QThread(self, objectName='workerThread')
            self.aquisition.moveToThread(self.confocalthread)
            self.aquisition.finished.connect(self.confocalthread.quit)

            self.confocalthread.started.connect(self.aquisition.longrun)
            self.confocalthread.finished.connect(self.confocalthread.deleteLater)
            self.aquisition.update.connect(self.updatemap)
            self.confocalthread.start()

    @pyqtSlot(np.ndarray, int)
    def updatemap(self, mapdataupdate, progress):
        # print("[%s] update" % QThread.currentThread().objectName())
        self.mapdata = mapdataupdate.T
        # start = time.time()
        self.map.set_data(self.mapdata)
        if self.scanmode == 'xy':
            self.map.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])  # TODO - add 1/2 pixel width on each side such that pixels are centered at their position
        elif self.scanmode == 'xz':
            self.map.set_extent([self.xmin, self.xmax, self.zmin, self.zmax])
        elif self.scanmode == 'yz':
            self.map.set_extent([self.ymin, self.ymax, self.zmin, self.zmax])
        self.mapcanvas.draw()
        self.colorautoscalepress()
        self.scanprogress.setValue(progress)
        # print(time.time()-start)

    def mapstopclicked(self):
        try:
            print('abort scan')
            self.aquisition.stop()
            self.confocalthread.quit()
        except:
            print('no scan running')

    def mapsaveclicked(self):
        self.filename, *rest = self.mapsavenametext.text().split('.')
        np.savetxt(str(os.getcwd())+'/data/'+str(self.filename)+'.txt', self.mapdata)
        self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.pdf')
        self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.png')
        print('file saved to data folder')

    def timetextchanged(self):
        self.settlingtime = self.settlingtimetext.value()/1000
        self.counttime = self.counttimetext.value()/1000
        if self.hardware_counter is True:
            self.fpgaclock = 80*10**6  # in Hz
            self.counttime_bytes = (int(self.counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
            self.counter.write(b'T'+self.counttime_bytes)  # set counttime at fpga
            self.counter.write(b't')  # check counttime
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')/self.fpgaclock
            print('\t fpga counttime:', self.check_counttime)
        print('settlingtime:', self.settlingtime, 'counttime:', self.counttime)

    def checklaserpower(self):
        if self.hardware_laser is True:
            self.laser.write(b'POWER?'+b'\r')
            answer = self.laser.readline().rstrip()[:-2]
            if not answer:
                pass
            else:
                self.laserpower = float(answer)
                self.laserpowerinfo.setValue(self.laserpower)
        else:
            print('cannot check laserpower - no laser found')

    def setlaserpower(self):
        if self.hardware_laser is True:
            self.laserpowernew = self.laserpowerset.value()
            cmd = 'POWER=%d' % self.laserpowernew
            self.laser.write(bytes(cmd + '\r', 'UTF-8'))
            print('set new laserpower to [mW]', self.laserpowernew)
        else:
            print('cannot change laserpower - no laser found')

    def scanmodechange(self):
        self.scanmode = self.scanselect.currentText()
        print('new scan mode:', self.scanmode)


class MinionColfocalMapDataAquisition(QObject):
    """
    Note that the stage is oriented such that the axis are
    1 - Y
    2 - X
    3 - Z
    """
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, int)

    def __init__(self, resolution1, resolution2, settlingtime, counttime, xmin, xmax, ymin, ymax, zmin, zmax, counter, stagelib, stage, scanmode, xpos, ypos, zpos):
        super(MinionColfocalMapDataAquisition, self).__init__()
        self.resolution1 = resolution1
        self.resolution2 = resolution2
        self.settlingtime = settlingtime
        self.counttime = counttime
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.zmin = zmin
        self.zmax = zmax
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.scanmode = scanmode
        self.counter = counter
        self.dimension = len(scanmode)
        self.stagelib = stagelib
        self.stage = stage
        self.poserrorx = 0.
        self.poserrory = 0.
        self.poserrorz = 0.
        self.progress = 0.

        if self.stage == 0:
            print('cannot get a handle to the device')
        else:
            if self.dimension == 2:
                if self.scanmode == 'xy':
                    dim1 = np.linspace(self.xmin, self.xmax, self.resolution1)  # 1-x
                    dim2 = np.linspace(self.ymin, self.ymax, self.resolution2)  # 2-y
                    self.axis1 = 2
                    self.axis2 = 1
                    self.startpos1 = self.xmin
                    self.startpos2 = self.ymin
                    self.pos1 = self.xpos
                    self.pos2 = self.ypos
                elif self.scanmode == 'xz':
                    dim1 = np.linspace(self.xmin, self.xmax, self.resolution1)  # 1-x
                    dim2 = np.linspace(self.zmin, self.zmax, self.resolution2)  # 2-z
                    self.axis1 = 2
                    self.axis2 = 3
                    self.startpos1 = self.xmin
                    self.startpos2 = self.zmin
                    self.pos1 = self.xpos
                    self.pos2 = self.zpos
                elif self.scanmode == 'yz':
                    dim1 = np.linspace(self.ymin, self.ymax, self.resolution1)  # 1-y
                    dim2 = np.linspace(self.zmin, self.zmax, self.resolution2)  # 2-z
                    self.axis1 = 1
                    self.axis2 = 3
                    self.startpos1 = self.ymin
                    self.startpos2 = self.zmin
                    self.pos1 = self.ypos
                    self.pos2 = self.zpos

                dim1 = np.tile(dim1, (1, self.resolution2))
                dim2 = np.tile(dim2, (self.resolution1, 1))
                dim2 = dim2.T
                self.list1 = np.reshape(dim1, (1, self.resolution1*self.resolution2))
                self.list2 = np.reshape(dim2, (1, self.resolution1*self.resolution2))
                indexmat = np.indices((self.resolution1, self.resolution2))
                indexmat = np.swapaxes(indexmat, 0, 2)
                self.indexlist = indexmat.reshape((1, self.resolution1*self.resolution2, 2))

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning = False

    def longrun(self):
        mapdataupdate = np.zeros((self.resolution1, self.resolution2))
        print("[%s] start scan" % QThread.currentThread().objectName())
        print('resolution:', self.resolution1, 'x', self.resolution2)

        tstart = time.time()
        # MOVE TO START POSITION
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.startpos1), self.axis1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.startpos2), self.axis2, self.stage)
        time.sleep(0.5)

        for i in range(0, self.resolution1*self.resolution2):
            if not self._isRunning:
                self.finished.emit()
            else:
                # MOVE
                status1 = self.stagelib.MCL_SingleWriteN(c_double(self.list1[0, i]), self.axis1, self.stage)
                status2 = self.stagelib.MCL_SingleWriteN(c_double(self.list2[0, i]), self.axis2, self.stage)
                time.sleep(self.settlingtime)  # wait
                if (i+1) % self.resolution1 == 0:
                    # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                    time.sleep(self.settlingtime*2)
                # CHECK POS
                pos1 = self.stagelib.MCL_SingleReadN(self.axis1, self.stage)
                pos2 = self.stagelib.MCL_SingleReadN(self.axis2, self.stage)
                self.poserrorx += (self.list1[0, i] - pos1)
                self.poserrory += (self.list2[0, i] - pos2)

                # COUNT
                self.counter.write(b'C')
                time.sleep(self.counttime*1.05)
                answer = self.counter.read(8)
                apd1 = answer[:4]
                apd2 = answer[4:]
                apd1_count = int.from_bytes(apd1, byteorder='little')/self.counttime  # in cps
                apd2_count = int.from_bytes(apd2, byteorder='little')/self.counttime  # in cps
                mapdataupdate[self.indexlist[0, i, 0], self.indexlist[0, i, 1]] = apd1_count + apd2_count

                if (i+1) % self.resolution1 == 0:
                    self.progress = int(100*i/(self.resolution1*self.resolution2))
                    self.update.emit(mapdataupdate, self.progress)
                # print(time.time()-ttemp)

        self.update.emit(mapdataupdate, 100)
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.pos1), self.axis1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.pos2), self.axis2, self.stage)

        print('total time needed:', time.time()-tstart)
        print('average position error (X):', self.poserrorx/(self.resolution1*self.resolution2))
        print('average position error (Y):', self.poserrory/(self.resolution1*self.resolution2))
        print('thread done')
        self.finished.emit()

