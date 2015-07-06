"""
3dscan module
"""
print('executing minion.minion_3dscan')

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
# mplstyle.use('ggplot')  # 'ggplot', 'dark_background', 'bmh', 'fivethirtyeight'

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Minion3dscanUI(QWidget):
    def __init__(self, parent=None):
        super(Minion3dscanUI, self).__init__(parent)
        self.xmin = 5.
        self.xmax = 10.
        self.xpos = 10.
        self.ymin = 5.
        self.ymax = 10.
        self.ypos = 10.
        self.zmin = 5.
        self.zmax = 40.
        self.zpos = 25.
        self.xlim = 75.
        self.ylim = 75.
        self.zlim = 50.

        self.slice = 0

        self.resolution1 = 21
        self.resolution2 = 21
        self.resolution3 = 21
        self.volumemapdata = np.random.randn(self.resolution1, self.resolution2, self.resolution3)
        # self.volumemapdata = np.zeros((self.resolution1, self.resolution2, self.resolution3))
        self.colormin = self.volumemapdata.min()
        self.colormax = self.volumemapdata.max()
        self.settlingtime = 0.01  # pos error about 10nm - 0.01 results in about 30 nm
        self.counttime = 0.005

        self.uisetup()

    def uisetup(self):
        # create map canvas
        self.volumemapfigure = Figure()
        self.volumemapcanvas = FigureCanvas(self.volumemapfigure)
        self.volumemapcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.volumemapcanvas.setMinimumSize(50, 50)
        self.volumetoolbar = NavigationToolbar(self.volumemapcanvas, self)
        self.volumemapaxes = self.volumemapfigure.add_subplot(111)
        self.volumemapaxes.hold(False)

        self.volumemap = self.volumemapaxes.matshow(self.volumemapdata[:, :, self.slice], origin='lower')# , extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.volumecolorbar = self.volumemapfigure.colorbar(self.volumemap, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.volumecolorbar.formatter.set_scientific(True)
        self.volumecolorbar.formatter.set_powerlimits((0, 3))
        self.volumecolorbar.update_ticks()
        self.volumemapaxes.xaxis.set_ticks_position('bottom')
        self.volumemapaxes.xaxis.set_tick_params(direction='out')
        self.volumemapaxes.yaxis.set_ticks_position('left')
        self.volumemapaxes.yaxis.set_tick_params(direction='out')

        # SLIDER
        self.sliderlabel = QLabel('y:')

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.resolution2-1)  # slide trough xz plane
        self.slider.setTickInterval(int((self.resolution2)/10))
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.sliderchanged)


        # SETTINGS
        self.xminlabel = QLabel('xmin:')
        self.xmintext = QDoubleSpinBox()
        self.xmintext.setRange(0, 100)
        self.xmintext.setValue(self.xmin)
        self.xmintext.editingFinished.connect(self.minmaxtextchanged)

        self.xmaxlabel = QLabel('xmax:')
        self.xmaxtext = QDoubleSpinBox()
        self.xmaxtext.setRange(0, 100)
        self.xmaxtext.setValue(self.xmax)
        self.xmaxtext.editingFinished.connect(self.minmaxtextchanged)

        self.yminlabel = QLabel('ymin:')
        self.ymintext = QDoubleSpinBox()
        self.ymintext.setRange(0, 100)
        self.ymintext.setValue(self.ymin)
        self.ymintext.editingFinished.connect(self.minmaxtextchanged)

        self.ymaxlabel = QLabel('ymax:')
        self.ymaxtext = QDoubleSpinBox()
        self.ymaxtext.setRange(0, 100)
        self.ymaxtext.setValue(self.ymax)
        self.ymaxtext.editingFinished.connect(self.minmaxtextchanged)

        self.zminlabel = QLabel('zmin:')
        self.zmintext = QDoubleSpinBox()
        self.zmintext.setRange(0, 100)
        self.zmintext.setValue(self.zmin)
        self.zmintext.editingFinished.connect(self.minmaxtextchanged)

        self.zmaxlabel = QLabel('zmax:')
        self.zmaxtext = QDoubleSpinBox()
        self.zmaxtext.setRange(0, 100)
        self.zmaxtext.setValue(self.zmax)
        self.zmaxtext.editingFinished.connect(self.minmaxtextchanged)

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

        # Control and save
        self.volumescanstart = QPushButton('start scan')
        self.volumescanstop = QPushButton('stop scan')
        self.scanprogress = QProgressBar()
        self.scanprogresslabel = QLabel('est. t:')
        self.mapsavenametext = QLineEdit()
        self.mapsavenametext.setText('filename')
        self.mapsave = QPushButton('save scan')
        self.mapsave.clicked.connect(self.volumemapsaveclicked)

        # Create Layout
        volumescanlayout = QGridLayout()
        volumescanlayout.addWidget(self.volumemapcanvas, 0, 0, 10, 10)
        volumescanlayout.addWidget(self.volumetoolbar, 10, 0, 1, 10)
        volumescanlayout.addWidget(self.sliderlabel, 11, 0, 1, 1)
        volumescanlayout.addWidget(self.slider, 11, 1, 1, 9)
        volumescanlayout.addWidget(self.volumescanstart, 12, 0)
        volumescanlayout.addWidget(self.volumescanstop, 12, 1)
        volumescanlayout.addWidget(self.scanprogress, 12, 2)
        volumescanlayout.addWidget(self.scanprogresslabel, 12, 3)
        volumescanlayout.addWidget(self.mapsavenametext, 12, 4)
        volumescanlayout.addWidget(self.mapsave, 12, 5)

        volumescanlayout.addWidget(self.xminlabel, 0, 10)
        volumescanlayout.addWidget(self.xmintext, 0, 11)
        volumescanlayout.addWidget(self.xmaxlabel, 1, 10)
        volumescanlayout.addWidget(self.xmaxtext, 1, 11)
        volumescanlayout.addWidget(self.yminlabel, 2, 10)
        volumescanlayout.addWidget(self.ymintext, 2, 11)
        volumescanlayout.addWidget(self.ymaxlabel, 3, 10)
        volumescanlayout.addWidget(self.ymaxtext, 3, 11)
        volumescanlayout.addWidget(self.zminlabel, 4, 10)
        volumescanlayout.addWidget(self.zmintext, 4, 11)
        volumescanlayout.addWidget(self.zmaxlabel, 5, 10)
        volumescanlayout.addWidget(self.zmaxtext, 5, 11)

        volumescanlayout.addWidget(self.settlingtimelabel, 6, 10)
        volumescanlayout.addWidget(self.settlingtimetext, 6, 11)
        volumescanlayout.addWidget(self.counttimelabel, 7, 10)
        volumescanlayout.addWidget(self.counttimetext, 7, 11)

        volumescanlayout.setSpacing(2)
        self.setLayout(volumescanlayout)

    def sliderchanged(self):
        self.slice = self.slider.value()
        self.volumemap = self.volumemapaxes.matshow(self.volumemapdata[:, :, self.slice], origin='lower')
        self.volumemapcanvas.draw()

    def minmaxtextchanged(self):
        self.xmin = self.xmintext.value()
        self.xmax = self.xmaxtext.value()
        self.ymin = self.ymintext.value()
        self.ymax = self.ymaxtext.value()
        self.zmin = self.zmintext.value()
        self.zmax = self.zmaxtext.value()

        # check for stage limit violations
        if not 0. <= self.xmin < self.xmax:
            self.xmin = 0.
            self.xmintext.setValue(self.xmin)
        if not self.xmin < self.xmax < self.xlim:
            self.xmax = self.xlim
            self.xmaxtext.setValue(self.xmax)
        if not 0. <= self.ymin < self.ymax:
            self.ymin = 0.
            self.ymintext.setValue(self.ymin)
        if not self.ymin < self.ymax < self.ylim:
            self.ymax = self.ylim
            self.ymaxtext.setValue(self.ymax)
        if not 0. <= self.zmin < self.zmax:
            self.zmin = 0.
            self.zmintext.setValue(self.zmin)
        if not self.zmin < self.zmax < self.zlim:
            self.zmax = self.zlim
            self.zmaxtext.setValue(self.zmax)

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

    def volumemapstartclicked(self):
        print("[%s] start scan" % QThread.currentThread().objectName())
        self.scanprogress.setRange(0, 100)
        self.scanprogress.setValue(0)

        if self.hardware_stage is True and self.hardware_counter is True:
            self.aquisition = MinionVolumeMapDataAquisition(self.resolution1, self.resolution2, self.settlingtime, self.counttime, self.xmin, self.xmax, self. ymin, self.ymax, self.zmin, self.zmax, self.counter, self.stagelib, self.stage, self.scanmode, self.xpos, self.ypos, self.zpos)
            self.confocalthread = QThread(self, objectName='workerThread')
            self.aquisition.moveToThread(self.confocalthread)
            self.aquisition.finished.connect(self.confocalthread.quit)

            self.confocalthread.started.connect(self.aquisition.longrun)
            self.confocalthread.finished.connect(self.confocalthread.deleteLater)
            self.aquisition.update.connect(self.updatemap)
            self.confocalthread.start()

    def volumemapsaveclicked(self):
        pass



class MinionVolumeMapDataAquisition(QObject):
    """
    Note that the stage is oriented such that the axis are
    1 - Y
    2 - X
    3 - Z
    """
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, int)

    def __init__(self, resolution1, resolution2, resolution3, settlingtime, counttime, xmin, xmax, ymin, ymax, zmin, zmax, counter, stagelib, stage):
        super(MinionVolumeMapDataAquisition, self).__init__()
        self.resolution1 = resolution1
        self.resolution2 = resolution2
        self.resolution3 = resolution3
        self.settlingtime = settlingtime
        self.counttime = counttime
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.zmin = zmin
        self.zmax = zmax
        self.counter = counter
        self.stagelib = stagelib
        self.stage = stage
        self.poserrorx = 0.
        self.poserrory = 0.
        self.poserrorz = 0.
        self.progress = 0.