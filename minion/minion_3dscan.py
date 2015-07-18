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

# TODO get min max pos zeug from parent via button click
class Minion3dscanUI(QWidget):
    def __init__(self, parent):
        super(Minion3dscanUI, self).__init__(parent)
        self.parent = parent
        self.hardware_counter = self.parent.hardware_counter
        self.hardware_laser = self.parent.hardware_laser
        self.hardware_stage = self.parent.hardware_stage
        if self.hardware_counter is True:
            self.counter = self.parent.counter
        if self.hardware_laser is True:
            self.laser = self.parent.laser
        if self.hardware_stage is True:
            self.stage = self.parent.stage
            self.stagelib = self.parent.stagelib
        self.xmin = 5.
        self.xmax = 10.
        self.xpos = 39.
        self.ymin = 5.
        self.ymax = 10.
        self.ypos = 28.
        self.zmin = 5.
        self.zmax = 40.
        self.zpos = 34.
        self.xlim = 75.
        self.ylim = 75.
        self.zlim = 50.

        self.slice = 0

        self.resolution1 = 21  # x
        self.resolution2 = 21  # y
        self.resolution3 = 21  # z
        self.volumemapdata = np.zeros((self.resolution3, self.resolution2, self.resolution1))
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

        self.volumemap = self.volumemapaxes.matshow(self.volumemapdata[self.slice, :, :], origin='lower')
        self.volumecolorbar = self.volumemapfigure.colorbar(self.volumemap, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.volumecolorbar.formatter.set_scientific(True)
        self.volumecolorbar.formatter.set_powerlimits((0, 3))
        self.volumecolorbar.update_ticks()
        self.volumemapaxes.xaxis.set_ticks_position('bottom')
        self.volumemapaxes.xaxis.set_tick_params(direction='out')
        self.volumemapaxes.yaxis.set_ticks_position('left')
        self.volumemapaxes.yaxis.set_tick_params(direction='out')

        # SLIDER
        self.sliderlabel = QLabel('z:')

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.resolution3-1)  # slide trough xy plane
        self.slider.setTickInterval(int((self.resolution3)/10))
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

        self.resolution1label = QLabel('res_x:')
        self.resolution1text = QSpinBox()
        self.resolution1text.setRange(1, 1000)
        self.resolution1text.setValue(self.resolution1)
        self.resolution1text.editingFinished.connect(self.resolutiontextchanged)

        self.resolution2label = QLabel('res_y:')
        self.resolution2text = QSpinBox()
        self.resolution2text.setRange(1, 1000)
        self.resolution2text.setValue(self.resolution2)
        self.resolution2text.editingFinished.connect(self.resolutiontextchanged)

        self.resolution3label = QLabel('res_z:')
        self.resolution3text = QSpinBox()
        self.resolution3text.setRange(1, 1000)
        self.resolution3text.setValue(self.resolution3)
        self.resolution3text.editingFinished.connect(self.resolutiontextchanged)

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
        self.volumescanstart.clicked.connect(self.volumemapstartclicked)
        self.volumescanstop = QPushButton('stop scan')
        self.volumescanstop.clicked.connect(self.volumemapstopclicked)
        self.scanprogress = QProgressBar()
        self.scanprogresslabel = QLabel('est. t:')
        self.mapsavenametext = QLineEdit()
        self.mapsavenametext.setText('filename')
        self.mapsavenametext.setFixedWidth(80)
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

        controlboxlabel = QVBoxLayout()
        controlboxtext = QVBoxLayout()
        controlboxlabel.addWidget(self.xminlabel)
        controlboxtext.addWidget(self.xmintext)
        controlboxlabel.addWidget(self.xmaxlabel)
        controlboxtext.addWidget(self.xmaxtext)
        controlboxlabel.addWidget(self.resolution1label)
        controlboxtext.addWidget(self.resolution1text)
        controlboxlabel.addWidget(self.yminlabel)
        controlboxtext.addWidget(self.ymintext)
        controlboxlabel.addWidget(self.ymaxlabel)
        controlboxtext.addWidget(self.ymaxtext)
        controlboxlabel.addWidget(self.resolution2label)
        controlboxtext.addWidget(self.resolution2text)
        controlboxlabel.addWidget(self.zminlabel)
        controlboxtext.addWidget(self.zmintext)
        controlboxlabel.addWidget(self.zmaxlabel)
        controlboxtext.addWidget(self.zmaxtext)
        controlboxlabel.addWidget(self.resolution3label)
        controlboxtext.addWidget(self.resolution3text)

        controlboxlabel.addWidget(self.settlingtimelabel)
        controlboxtext.addWidget(self.settlingtimetext)
        controlboxlabel.addWidget(self.counttimelabel)
        controlboxtext.addWidget(self.counttimetext)

        volumescanlayout.addLayout(controlboxlabel, 0, 10)
        volumescanlayout.addLayout(controlboxtext, 0, 11)
        volumescanlayout.setSpacing(2)
        self.setLayout(volumescanlayout)

    def sliderchanged(self):
        self.slice = self.slider.value()
        self.volumemap = self.volumemapaxes.matshow(self.volumemapdata[self.slice, :, :], origin='lower', extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.colormin = self.volumemapdata.min()
        self.colormax = self.volumemapdata.max()
        self.volumemap.set_clim(vmin=self.colormin, vmax=self.colormax)
        self.volumecolorbar.set_clim(vmin=self.colormin, vmax=self.colormax)
        self.colorbar.draw_all()
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


    def resolutiontextchanged(self):
        self.resolution1 = self.resolution1text.value()
        self.resolution2 = self.resolution2text.value()
        self.resolution3 = self.resolution3text.value()

    def volumemapstartclicked(self):
        print("[%s] start scan" % QThread.currentThread().objectName())
        self.volumemapdata = np.zeros((self.resolution3, self.resolution2, self.resolution1))
        self.scanprogress.setRange(0, 100)
        self.scanprogress.setValue(0)
        self.slider.setMaximum(self.resolution3-1)  # slide trough xy plane
        self.slider.setTickInterval(int((self.resolution3)/10))

        if self.hardware_stage is True and self.hardware_counter is True:
            self.volumeaquisition = MinionVolumeMapDataAquisition(self.resolution1, self.resolution2, self.resolution3, self.settlingtime, self.counttime, self.xmin, self.xmax, self. ymin, self.ymax, self.zmin, self.zmax, self.xpos, self.ypos, self.zpos, self.counter, self.stagelib, self.stage)
            self.volumethread = QThread(self, objectName='workerThread')
            self.volumeaquisition.moveToThread(self.volumethread)
            self.volumeaquisition.finished.connect(self.volumethread.quit)

            self.volumethread.started.connect(self.volumeaquisition.longrun)
            self.volumethread.finished.connect(self.volumethread.deleteLater)
            self.volumeaquisition.update.connect(self.updatemap)
            self.volumethread.start()

    def volumemapstopclicked(self):
        try:
            print('abort scan')
            self.volumeaquisition.stop()
            self.volumethread.quit()
        except:
            print('no scan running')

    def volumemapsaveclicked(self):
        self.filename, *rest = self.mapsavenametext.text().split('.')
        np.save(str(os.getcwd())+'/data/'+str(self.filename)+'.npy', self.volumemapdata)
        print('file saved to data folder')

    @pyqtSlot(np.ndarray, int)
    def updatemap(self, mapdataupdate, progress):
        print('update plot')
        self.volumemapdata = mapdataupdate
        self.volumemap.set_extent([self.ymin, self.ymax, self.xmin, self.xmax])
        self.sliderchanged()
        self.scanprogress.setValue(progress)



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

    def __init__(self, resolution1, resolution2, resolution3, settlingtime, counttime, xmin, xmax, ymin, ymax, zmin, zmax, xpos, ypos, zpos, counter, stagelib, stage):
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
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.counter = counter
        self.stagelib = stagelib
        self.stage = stage
        self.poserrorx = 0.
        self.poserrory = 0.
        self.poserrorz = 0.
        self.progress = 0.

        if self.stage == 0:
            print('cannot get a handle to the device')
        else:
            self.axis1 = 2  # x
            self.axis2 = 1  # y
            self.axis3 = 3  # z

            self.startpos1 = self.xmin
            self.startpos2 = self.ymin
            self.startpos3 = self.zmin
            self.pos1 = self.xpos
            self.pos2 = self.ypos
            self.pos3 = self.zpos

            dim1 = np.linspace(self.xmin, self.xmax, self.resolution1)  # 1-x
            dim2 = np.linspace(self.ymin, self.ymax, self.resolution2)  # 2-y
            dim3 = np.linspace(self.zmin, self.zmax, self.resolution3)  # 3-z

            dim1 = np.tile(dim1, (1, resolution2*resolution3))
            dim2 = np.tile(dim2, (resolution1, 1))
            dim2 = dim2.T
            dim2 = np.tile(dim2, (resolution3, 1))
            dim3 = np.tile(dim3, (resolution1*resolution2, 1))
            dim3 = dim3.T

            self.list1 = np.reshape(dim1, (1, resolution1*resolution2*resolution3))
            self.list2 = np.reshape(dim2, (1, resolution1*resolution2*resolution3))
            self.list3 = np.reshape(dim3, (1, resolution1*resolution2*resolution3))

            indexmat = np.indices((resolution3, resolution2, resolution1))
            self.indexlist = indexmat.reshape((1, 3, resolution1*resolution2*resolution3))

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning = False

    def longrun(self):
        volumemapdataupdate = np.zeros((self.resolution3, self.resolution2, self.resolution1))
        print("[%s] start scan" % QThread.currentThread().objectName())
        print('resolution:', self.resolution1, 'x', self.resolution2, 'x', self.resolution3)

        tstart = time.time()
        # MOVE TO START POSITION
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.startpos1), self.axis1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.startpos2), self.axis2, self.stage)
        status3 = self.stagelib.MCL_SingleWriteN(c_double(self.startpos3), self.axis3, self.stage)
        time.sleep(0.5)

        for i in range(0, self.resolution1*self.resolution2*self.resolution3):
            if not self._isRunning:
                self.finished.emit()
            else:
                # MOVE
                status1 = self.stagelib.MCL_SingleWriteN(c_double(self.list1[0, i]), self.axis1, self.stage)
                status2 = self.stagelib.MCL_SingleWriteN(c_double(self.list2[0, i]), self.axis2, self.stage)
                status3 = self.stagelib.MCL_SingleWriteN(c_double(self.list3[0, i]), self.axis3, self.stage)
                time.sleep(self.settlingtime)  # wait
                if (i+1) % self.resolution1 == 0:
                    # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                    time.sleep(self.settlingtime*2)
                    # CHECK POS
                    if (i+i) % (self.resolution1*self.resolution2) == 0:
                        time.sleep(self.settlingtime*3)
                pos1 = self.stagelib.MCL_SingleReadN(self.axis1, self.stage)
                pos2 = self.stagelib.MCL_SingleReadN(self.axis2, self.stage)
                pos3 = self.stagelib.MCL_SingleReadN(self.axis3, self.stage)
                self.poserrorx += (self.list1[0, i] - pos1)
                self.poserrory += (self.list2[0, i] - pos2)
                self.poserrorz += (self.list3[0, i] - pos3)

                # COUNT
                self.counter.write(b'C')
                time.sleep(self.counttime*1.05)
                answer = self.counter.read(8)
                apd1 = answer[:4]
                apd2 = answer[4:]
                apd1_count = int.from_bytes(apd1, byteorder='little')/self.counttime  # in cps
                apd2_count = int.from_bytes(apd2, byteorder='little')/self.counttime  # in cps
                volumemapdataupdate[self.indexlist[0, 0, i], self.indexlist[0, 1, i], self.indexlist[0, 2, i]] = apd1_count + apd2_count  # TODO - check if axis are correct

                if (i+1) % (self.resolution1*self.resolution2) == 0:
                    self.progress = int(100*i/(self.resolution1*self.resolution2*self.resolution3))
                    self.update.emit(volumemapdataupdate, self.progress)
                # print(time.time()-ttemp)

        self.update.emit(volumemapdataupdate, 100)
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.pos1), self.axis1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.pos2), self.axis2, self.stage)
        status3 = self.stagelib.MCL_SingleWriteN(c_double(self.pos3), self.axis3, self.stage)


        print('total time needed:', time.time()-tstart)
        print('average position error (dim1):', self.poserrorx/(self.resolution1*self.resolution2*self.resolution3))
        print('average position error (dim2):', self.poserrory/(self.resolution1*self.resolution2*self.resolution3))
        print('average position error (dim3):', self.poserrorz/(self.resolution1*self.resolution2*self.resolution3))
        print('thread done')
        self.finished.emit()



