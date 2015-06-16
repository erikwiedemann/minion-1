"""
confocal module that creates the navigation-, tilt- and settings-tab
"""
print('executing minion.minion_confocal')

import os
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import matplotlib as mpl
import serial
from ctypes import *

mpl.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MinionConfocalUi(QWidget):
    def __init__(self, parent=None):
        super(MinionConfocalUi, self).__init__(parent)
        self.confocal = MinionConfocalNavigation()

        # self.setFixedSize(650, 800)
        self.confocallayout = QGridLayout()
        self.confocallayout.addWidget(self.confocal)
        self.setLayout(self.confocallayout)


class MinionConfocalNavigation(QWidget):
    def __init__(self):
        super(MinionConfocalNavigation, self).__init__()
        # initialize hardware / if hardware not there, do nothing
        import minion.minion_hardware_check
        self.hardware_laser = True
        self.hardware_counter = True
        self.hardware_stage = True

        # set and get initial variables
        # TODO - get these values from the hardware
        self.xmin = 5.
        self.xmax = 10.0
        self.xpos = 5.0
        self.ymin = 5.0
        self.ymax = 10.0
        self.ypos = 5.0
        self.zmin = 5.0
        self.zmax = 50.0
        self.zpos = 36.0

        self.resolution = 21
        self.colormin = 0
        self.colormax = 100
        self.mapdata = np.zeros((self.resolution, self.resolution))
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        self.settlingtime = 0.01  # pos error about 10nm - 0.01 results in about 30 nm
        self.counttime = 0.005
        self.laserpowernew = 10.0  # TODO - set to current laser power
        self.laserpowermin = 0.001
        self.laserpowermax = 200.
        self.laserpowertimer = QTimer()
        self.laserpowertimer.timeout.connect(self.checklaserpower)
        self.laserpowertimer.setInterval(1000)
        self.laserpowertimer.start()

        if self.hardware_laser is True:
            self.laser = serial.Serial('/dev/ttyUSB2', baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        else:
            print('laser not found')

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

        if self.hardware_stage is True:
            CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
            self.stagelib = CDLL('libmadlib.so', 1)
            self.stage = self.stagelib.MCL_InitHandleOrGetExisting()
            if self.stage == 0:
                self.hardware_stage = False
                print('cound not get stage handle')

            # define restypes that are not standard (INT)
            self.stagelib.MCL_SingleReadN.restype = c_double
            self.stagelib.MCL_MonitorN.restype = c_double
            self.stagelib.MCL_GetCalibration.restype = c_double
        else:
            print('stage not found')

        self.uisetup()
        self.updatemap(self.mapdata, 0)

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
        # self.mapcanvas.setFixedSize(600, 500)
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
        self.resolutiontext = QSpinBox()
        # self.resolutiontext.setFixedWidth(60)
        self.resolutiontext.setRange(1, 1000)
        self.resolutiontext.setValue(self.resolution)
        self.resolutiontext.editingFinished.connect(self.resolutiontextchanged)

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
        # TODO - add checkboxes to enable scan axis and fix axis
        # X-SLIDER
        self.xsliderlabel = QLabel('x [µm]:')
        self.xslidermintext = QDoubleSpinBox()
        # self.xslidermintext.setFixedWidth(60)
        self.xslidermintext.setValue(self.xmin)
        self.xslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.xslidermaxtext = QDoubleSpinBox()
        # self.xslidermaxtext.setFixedWidth(70)
        self.xslidermaxtext.setRange(0, 100)
        self.xslidermaxtext.setValue(self.xmax)
        self.xslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.xslider = QSlider(Qt.Horizontal, self)
        self.xslider.setMinimum(self.xmin*100)
        self.xslider.setMaximum(self.xmax*100)
        self.xslider.setTickInterval(int((self.xmax-self.xmin)/10*100))
        self.xslider.setValue(int((self.xmin+self.xmax)/2*100))
        self.xslider.setTickPosition(QSlider.TicksBelow)
        self.xslider.valueChanged.connect(self.xsliderchanged)

        self.xslidervaluetext = QDoubleSpinBox()
        # self.xslidervaluetext.setFixedWidth(70)
        self.xslidervaluetext.setRange(0, 100)
        self.xslidervaluetext.setDecimals(2)
        self.xslidervaluetext.setValue(self.xslider.value()/100)
        self.xslidervaluetext.editingFinished.connect(self.xslidervaluetextchanged)

        # Y-SLIDER
        self.ysliderlabel = QLabel('y [µm]:')
        self.yslidermintext = QDoubleSpinBox()
        # self.yslidermintext.setFixedWidth(60)
        self.yslidermintext.setValue(self.ymin)
        self.yslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.yslidermaxtext = QDoubleSpinBox()
        # self.yslidermaxtext.setFixedWidth(70)
        self.yslidermaxtext.setRange(0, 100)
        self.yslidermaxtext.setValue(self.ymax)
        self.yslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.yslider = QSlider(Qt.Horizontal, self)
        self.yslider.setMinimum(self.ymin*100)
        self.yslider.setMaximum(self.ymax*100)
        self.yslider.setTickInterval(int((self.ymax-self.ymin)/10*100))
        self.yslider.setValue(int((self.ymin+self.ymax)/2*100))
        self.yslider.setTickPosition(QSlider.TicksBelow)
        self.yslider.valueChanged.connect(self.ysliderchanged)

        self.yslidervaluetext = QDoubleSpinBox()
        # self.yslidervaluetext.setFixedWidth(70)
        self.yslidervaluetext.setRange(0, 100)
        self.yslidervaluetext.setDecimals(2)
        self.yslidervaluetext.setValue(self.yslider.value()/100)
        self.yslidervaluetext.editingFinished.connect(self.yslidervaluetextchanged)

        # Z-SLIDER
        self.zsliderlabel = QLabel('z [µm]:')
        self.zslidermintext = QDoubleSpinBox()
        # self.yslidermintext.setFixedWidth(60)
        self.zslidermintext.setValue(self.ymin)
        self.zslidermintext.editingFinished.connect(self.sliderminmaxtextchanged)
        self.zslidermaxtext = QDoubleSpinBox()
        # self.zslidermaxtext.setFixedWidth(70)
        self.zslidermaxtext.setRange(0, 50)
        self.zslidermaxtext.setValue(self.zmax)
        self.zslidermaxtext.editingFinished.connect(self.sliderminmaxtextchanged)

        self.zslider = QSlider(Qt.Horizontal, self)
        self.zslider.setMinimum(self.zmin*100)
        self.zslider.setMaximum(self.zmax*100)
        self.zslider.setTickInterval(int((self.zmax-self.zmin)/10*100))
        self.zslider.setValue(int((self.zmin+self.zmax)/2*100))
        self.zslider.setTickPosition(QSlider.TicksBelow)
        self.zslider.valueChanged.connect(self.zsliderchanged)

        self.zslidervaluetext = QDoubleSpinBox()
        # self.zslidervaluetext.setFixedWidth(70)
        self.zslidervaluetext.setRange(0, 50)
        self.zslidervaluetext.setDecimals(2)
        self.zslidervaluetext.setValue(self.zslider.value()/100)
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
        # self.mapsavenametext.setFixedWidth(120)
        self.mapsavenametext.setText('filename')
        self.mapsave = QPushButton('save scan')
        self.mapsave.clicked.connect(self.mapsaveclicked)

        # count and settling time
        self.settlingtimelabel = QLabel('Settling Time [ms]')
        self.settlingtimetext = QDoubleSpinBox()
        self.settlingtimetext.setRange(0, 1000)
        self.settlingtimetext.setValue(int(self.settlingtime*1000))
        self.settlingtimetext.editingFinished.connect(self.timetextchanged)
        self.counttimelabel = QLabel('Count Time [ms]')
        self.counttimetext = QDoubleSpinBox()
        self.counttimetext.setRange(0, 1000)
        self.counttimetext.setValue(int(self.counttime*1000))
        self.counttimetext.editingFinished.connect(self.timetextchanged)

        # laser control widgets
        self.laserpowerinfolabel = QLabel('current power [mW]:')
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

        # create layout
        confocal_layout = QGridLayout()
        confocal_layout.addWidget(self.mapcanvas, 0, 0, 1, 10)
        confocal_layout.addWidget(self.toolbar, 1, 0, 1, 10)

        confocal_layout.addWidget(self.resolutionlabel, 2, 0, 1, 1)
        confocal_layout.addWidget(self.resolutiontext, 2, 1, 1, 1)
        confocal_layout.addWidget(self.colorminlabel, 2, 2, 1, 1)
        confocal_layout.addWidget(self.colormintext, 2, 3, 1, 1)
        confocal_layout.addWidget(self.colormaxlabel, 2, 4, 1, 1)
        confocal_layout.addWidget(self.colormaxtext, 2, 5, 1, 1)
        confocal_layout.addWidget(self.colorautoscale, 2, 6, 1, 1)

        confocal_layout.addWidget(self.hline, 3, 0, 1, 10)

        confocal_layout.addWidget(self.slidermintextlabel, 4, 1)
        confocal_layout.addWidget(self.slidermaxtextlabel, 4, 8)
        confocal_layout.addWidget(self.sliderpostextlabel, 4, 9)

        confocal_layout.addWidget(self.xsliderlabel, 5, 0)
        confocal_layout.addWidget(self.xslidermintext, 5, 1)
        confocal_layout.addWidget(self.xslider, 5, 2, 1, 6)
        confocal_layout.addWidget(self.xslidermaxtext, 5, 8)
        confocal_layout.addWidget(self.xslidervaluetext, 5, 9)

        confocal_layout.addWidget(self.ysliderlabel, 6, 0)
        confocal_layout.addWidget(self.yslidermintext, 6, 1)
        confocal_layout.addWidget(self.yslider, 6, 2, 1, 6)
        confocal_layout.addWidget(self.yslidermaxtext, 6, 8)
        confocal_layout.addWidget(self.yslidervaluetext, 6, 9)

        confocal_layout.addWidget(self.zsliderlabel, 7, 0)
        confocal_layout.addWidget(self.zslidermintext, 7, 1)
        confocal_layout.addWidget(self.zslider, 7, 2, 1, 6)
        confocal_layout.addWidget(self.zslidermaxtext, 7, 8)
        confocal_layout.addWidget(self.zslidervaluetext, 7, 9)

        confocal_layout.addWidget(self.hline1, 8, 0, 1, 10)

        confocal_layout.addWidget(self.mapstart, 9, 0, 2, 1)
        confocal_layout.addWidget(self.mapstop, 9, 1, 2, 1)
        confocal_layout.addWidget(self.scanprogress, 9, 2, 1, 2)
        confocal_layout.addWidget(self.scanprogresslabel, 9, 4, 1, 2)
        confocal_layout.addWidget(self.mapsavenametext, 9, 8, 1, 2)
        confocal_layout.addWidget(self.mapsave, 9, 8, 1, 2)

        confocal_layout.addWidget(self.settlingtimelabel, 2, 10, 1, 1)
        confocal_layout.addWidget(self.settlingtimetext, 2, 11, 1, 1)
        confocal_layout.addWidget(self.counttimelabel, 3, 10, 1, 1)
        confocal_layout.addWidget(self.counttimetext, 3, 11, 1, 1)

        confocal_layout.addWidget(self.laserpowerinfolabel, 4, 10, 1, 1)
        confocal_layout.addWidget(self.laserpowerinfo, 4, 11, 1, 1)
        confocal_layout.addWidget(self.laserpowersetlabel, 5, 10, 1, 1)
        confocal_layout.addWidget(self.laserpowerset, 5, 11, 1, 1)

        confocal_layout.setSpacing(2)
        self.setLayout(confocal_layout)

    def xsliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.xslidervaluetext.setValue(self.xslider.value()/100)
        self.vlinecursor.set_xdata(self.xslider.value()/100)
        self.mapcanvas.draw()
        self.status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xslider.value()/100), 2, self.stage)

    def xslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.xslider.setValue(self.xslidervaluetext.value()*100)
        self.vlinecursor.set_xdata(self.xslidervaluetext.value())
        self.mapcanvas.draw()
        self.status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xslider.value()/100), 2, self.stage)

    def sliderminmaxtextchanged(self):
        self.xmin = self.xslidermintext.value()
        self.xmax = self.xslidermaxtext.value()
        self.ymin = self.yslidermintext.value()
        self.ymax = self.yslidermaxtext.value()
        self.map.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
        self.mapcanvas.draw()
        self.xslider.setMinimum(self.xmin*100)
        self.xslider.setMaximum(self.xmax*100)
        self.xslider.setTickInterval(int((self.xmax-self.xmin)/10*100))
        self.xslider.setValue(int((self.xmin+self.xmax)/2*100))
        self.yslider.setMinimum(self.ymin*100)
        self.yslider.setMaximum(self.ymax*100)
        self.yslider.setTickInterval(int((self.ymax-self.ymin)/10*100))
        self.yslider.setValue(int((self.ymin+self.ymax)/2*100))

    def ysliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.yslidervaluetext.setValue(self.yslider.value()/100)
        self.hlinecursor.set_ydata(self.yslider.value()/100)
        self.mapcanvas.draw()
        self.status1 = self.stagelib.MCL_SingleWriteN(c_double(self.yslider.value()/100), 1, self.stage)

    def yslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.yslider.setValue(self.yslidervaluetext.value()*100)
        self.hlinecursor.set_ydata(self.yslidervaluetext.value())
        self.mapcanvas.draw()
        self.status1 = self.stagelib.MCL_SingleWriteN(c_double(self.yslider.value()/100), 1, self.stage)

    def zsliderchanged(self):
        """
        when the xslider is changed the value is written into the xvaluetext field
        """
        self.zslidervaluetext.setValue(self.zslider.value()/100)
        # self.vlinecursor.set_zdata(self.zslider.value()/100)
        # self.mapcanvas.draw()
        self.status3 = self.stagelib.MCL_SingleWriteN(c_double(self.zslider.value()/100), 3, self.stage)

    def zslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.xslider.setValue(self.xslidervaluetext.value()*100)
        # self.vlinecursor.set_xdata(self.xslidervaluetext.value())
        # self.mapcanvas.draw()
        self.status3 = self.stagelib.MCL_SingleWriteN(c_double(self.zslider.value()/100), 3, self.stage)


    def resolutiontextchanged(self):
        self.resolution = self.resolutiontext.value()

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

        self.aquisition = MinionColfocalMapDataAquisition(self.resolution, self.settlingtime, self.counttime, self.xmin, self.xmax, self. ymin, self.ymax, self.counter, self.stagelib, self.stage)
        self.confocalthread = QThread(self, objectName='workerThread')
        self.aquisition.moveToThread(self.confocalthread)
        self.aquisition.finished.connect(self.confocalthread.quit)

        self.confocalthread.started.connect(self.aquisition.longrun)
        self.confocalthread.finished.connect(self.confocalthread.deleteLater)
        self.aquisition.update.connect(self.updatemap)
        self.confocalthread.start()

    @pyqtSlot(float, float)
    def updatesettings(self):  # TODO - check if this is still needed
        print('update settings')
        print(self.settlingtime, self.counttime)

    @pyqtSlot(np.ndarray, int)
    def updatemap(self, mapdataupdate, progress):
        # print("[%s] update" % QThread.currentThread().objectName())
        self.mapdata = mapdataupdate.T
        # start = time.time()
        self.map.set_data(self.mapdata)
        self.map.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])  # TODO - add 1/2 pixel on each side such that pixels are centered at their position
        self.mapcanvas.draw()
        self.colorautoscalepress()
        self.scanprogress.setValue(progress)
        # print(time.time()-start)

    def mapstopclicked(self):
        # TODO - check if thread is running before quitting
        print('abort scan')
        self.aquisition.stop()
        self.confocalthread.quit()

    def mapsaveclicked(self):
        self.filename, *rest = self.mapsavenametext.text().split('.')
        np.savetxt(str(os.getcwd())+'/data/'+str(self.filename)+'.txt', self.mapdata)
        self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.pdf')
        print('file saved to data folder')

    def timetextchanged(self):
        self.settlingtime = self.settlingtimetext.value()/1000
        self.counttime = self.counttimetext.value()/1000
        if self.hardware_counter is True:
            self.fpgaclock = 80*10**6  # in Hz
            self.counttime_bytes = (int(self.counttime*self.fpgaclock)).to_bytes(4, byteorder='little')
            self.counter.write(b'T'+self.counttime_bytes)  # set counttime at fpga
            self.counter.write(b't')  # check counttime
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')
            print('\t fpga counttime:', self.check_counttime)
        print('changed:', self.settlingtime, self.counttime)

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

    def __init__(self, resolution, settlingtime, counttime, xmin, xmax, ymin, ymax, counter, stagelib, stage):
        super(MinionColfocalMapDataAquisition, self).__init__()
        self.resolution = resolution
        self.settlingtime = settlingtime
        self.counttime = counttime
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.counter = counter
        self.dimension = 2
        self.stagelib = stagelib
        self.stage = stage
        self.poserrorx = 0.
        self.poserrory = 0.
        self.progress = 0.

        if self.stage == 0:
            print('cannot get a handle to the device')
        else:
            if self.dimension == 2:
                mat = np.zeros((self.resolution, self.resolution, 2))  # preallocate

                dim1 = np.linspace(self.xmin, self.xmax, self.resolution)  # 1-x
                dim2 = np.linspace(self.ymin, self.ymax, self.resolution)  # 2-y

                mat[:, :, 0] = dim1
                # mat[1::2, :, 0] = np.fliplr(mat[1::2, :, 0])  # mirror the odd rows such that the scan goes like a snake
                mat[:, :, 1] = dim2
                mat[:, :, 1] = mat[:, :, 1].T

                self.list2 = np.reshape(mat[:, :, 0], (1, self.resolution**2))  # Y list
                self.list1 = np.reshape(mat[:, :, 1], (1, self.resolution**2))  # X list

                indexmat = np.indices((self.resolution, self.resolution))  # 0-x, 1-y,
                indexmat = np.swapaxes(indexmat, 0, 2)

                # indexmat[1::2, :, :] = np.fliplr(indexmat[1::2, :, :])  # mirror the odd rows such that the scan goes like a snake
                # indexmat = np.flipud(indexmat)
                self.indexlist = indexmat.reshape((1, self.resolution**2, 2))

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning=False

    def longrun(self):
        mapdataupdate = np.zeros((self.resolution, self.resolution))
        print("[%s] start scan" % QThread.currentThread().objectName())
        print('resolution', self.resolution)

        tstart = time.time()
        # MOVE TO START POSITION
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xmin), 1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.ymin), 2, self.stage)
        time.sleep(0.5)

        for i in range(0, self.resolution**2):
            if not self._isRunning:
                self.finished.emit()
            else:
                # MOVE
                status1 = self.stagelib.MCL_SingleWriteN(c_double(self.list1[0, i]), 1, self.stage)
                status2 = self.stagelib.MCL_SingleWriteN(c_double(self.list2[0, i]), 2, self.stage)
                time.sleep(self.settlingtime)  # wait
                if (i+1) % self.resolution == 0:
                    # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                    time.sleep(self.settlingtime*2)
                # CHECK POS
                pos1 = self.stagelib.MCL_SingleReadN(1, self.stage)
                pos2 = self.stagelib.MCL_SingleReadN(2, self.stage)
                self.poserrory += (self.list1[0, i] - pos1)
                self.poserrorx += (self.list2[0, i] - pos2)

                # COUNT
                self.counter.write(b'C')
                time.sleep(self.counttime*1.1)
                answer = self.counter.read(8)
                apd1 = answer[:4]
                apd2 = answer[4:]
                apd1_count = int.from_bytes(apd1, byteorder='little')
                apd2_count = int.from_bytes(apd2, byteorder='little')
                mapdataupdate[self.indexlist[0, i, 0], self.indexlist[0, i, 1]] = apd1_count + apd2_count

                if (i+1) % self.resolution == 0:
                    self.progress = int(100*i/(self.resolution**2))
                    self.update.emit(mapdataupdate, self.progress)
                # print(time.time()-ttemp)

        self.update.emit(mapdataupdate, 100)

        print('total time needed:', time.time()-tstart)
        print('average position error (X):', self.poserrorx/(self.resolution**2))
        print('average position error (Y):', self.poserrory/(self.resolution**2))
        print('thread done')
        self.finished.emit()

