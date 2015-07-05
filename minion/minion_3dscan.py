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
mplstyle.use('ggplot')  # 'ggplot', 'dark_background', 'bmh', 'fivethirtyeight'

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Minion3dscanUI(QWidget):
    def __init__(self, parent=None):
        super(Minion3dscanUI, self).__init__(parent)
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
        self.resolution3 = 21
        self.volumemapdata = np.zeros((self.resolution1, self.resolution2, self.resolution3))
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

        self.volumemap = self.volumemapaxes.matshow(self.volumemapdata[:,:,0], origin='lower')# , extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.volumecolorbar = self.volumemapfigure.colorbar(self.volumemap, fraction=0.046, pad=0.04, cmap=mpl.cm.rainbow)
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
        self.slider.setMaximum(self.resolution2)  # slide trough xz plane
        self.slider.setTickInterval(int((self.resolution2)/10))
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        # self.slider.valueChanged.connect(self.xsliderchanged)





        self.volumescanstart = QPushButton('start scan')

        volumescanlayout = QGridLayout()
        volumescanlayout.addWidget(self.volumemapcanvas, 0, 0, 10, 10)
        volumescanlayout.addWidget(self.volumetoolbar, 10, 0, 1, 10)
        volumescanlayout.addWidget(self.sliderlabel, 11, 0, 1, 1)
        volumescanlayout.addWidget(self.slider, 11, 1, 1, 9)
        volumescanlayout.addWidget(self.volumescanstart, 12, 0)

        volumescanlayout.setSpacing(2)
        self.setLayout(volumescanlayout)
