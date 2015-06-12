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
        self.hardware_laser = False
        self.hardware_counter = False

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
            self.check_counttime = int.from_bytes(self.counter.read(4), byteorder='little')
            print('\t fpga counttime:', self.check_counttime)
        else:
            print('counter not found')

        # set and get initial variables
        # TODO - get these values from the hardware
        self.xmin = 0.0
        self.xmax = 100.0
        self.xpos = 50.0
        self.ymin = 0.0
        self.ymax = 100.0
        self.ypos = 50.0
        self.resolution = 20
        self.colormin = 0
        self.colormax = 100
        self.mapdata = np.zeros((self.resolution, self.resolution))
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        self.settlingtime = 0.001
        self.counttime = 0.005
        self.laserpowernew = 10.0  # TODO - set to current laser power
        self.laserpowermin = 0.001
        self.laserpowermax = 200.
        self.laserpowertimer = QTimer()
        self.laserpowertimer.timeout.connect(self.checklaserpower)
        self.laserpowertimer.setInterval(1000)
        self.laserpowertimer.start()
        self.uisetup()

    def __del__(self):
        self.laserpowertimer.stop()
        if self.hardware_laser is True:
            self.laser.close()
            print(self.laser)

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

        confocal_layout.addWidget(self.hline1, 7, 0, 1, 10)

        confocal_layout.addWidget(self.mapstart, 8, 0, 2, 1)
        confocal_layout.addWidget(self.mapstop, 8, 1, 2, 1)
        confocal_layout.addWidget(self.scanprogress, 8, 2, 1, 2)
        confocal_layout.addWidget(self.scanprogresslabel, 8, 4, 1, 2)
        confocal_layout.addWidget(self.mapsavenametext, 8, 8, 1, 2)
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

    def xslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.xslider.setValue(self.xslidervaluetext.value()*100)
        self.vlinecursor.set_xdata(self.xslidervaluetext.value())
        self.mapcanvas.draw()

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

    def yslidervaluetextchanged(self):
        """
        when the xvaluetext is changed and enter is hit the value is set on the xslider
        """
        self.yslider.setValue(self.yslidervaluetext.value()*100)
        self.hlinecursor.set_ydata(self.yslidervaluetext.value())
        self.mapcanvas.draw()

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
        self.scanprogress.setRange(0, self.resolution-1)
        self.scanprogress.setValue(0)

        self.aquisition = MinionColfocalMapDataAquisition(self.resolution, self.settlingtime, self.counttime, self.xmin, self.xmax, self. ymin, self.ymax, self.hardware_counter)
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
    def updatemap(self, mapdataupdate, col):
        # print("[%s] update" % QThread.currentThread().objectName())
        self.mapdata = mapdataupdate
        # start = time.time()
        self.map.set_data(self.mapdata)
        self.mapcanvas.draw()
        self.colorautoscalepress()
        self.scanprogress.setValue(col)
        # print(time.time()-start)

    def mapstopclicked(self):
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
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, int)

    def __init__(self, resolution, settlingtime, counttime, xmin, xmax, ymin, ymax, hardware_counter):
        super(MinionColfocalMapDataAquisition, self).__init__()
        self.resolution = resolution
        self.settlingtime = settlingtime
        self.counttime = counttime
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.hardware_counter = hardware_counter

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning=False

    def longrun(self):
        mapdataupdate = np.zeros((self.resolution, self.resolution))
        print("[%s] start scan" % QThread.currentThread().objectName())
        print('resolution', self.resolution)

        tstart = time.time()
        for i in np.ndindex((self.resolution, self.resolution)):
            if not self._isRunning:
                self.finished.emit()
            else:

                time.sleep(self.settlingtime)  # wait

                time.sleep(self.counttime)  # measure

                self.value = np.random.randint(1, 1000)

                mapdataupdate[i] += self.value
                if i[1] == self.resolution-1:
                    self.update.emit(mapdataupdate, i[0])
                # print(time.time()-ttemp)

        self.update.emit(mapdataupdate, i[0])

        print('total time needed:', time.time()-tstart)

        print('thread done')
        self.finished.emit()

