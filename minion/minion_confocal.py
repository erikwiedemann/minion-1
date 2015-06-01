"""
confocal module that creates the navigation-, tilt- and settings-tab
"""
print('executing minion.minion_confocal')

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import sys
import numpy as np
import scipy as sp
import matplotlib as mpl
mpl.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import ticker
import matplotlib.animation as animation


class MinionConfocalUi(QWidget):
    def __init__(self, parent=None):
        super(MinionConfocalUi, self).__init__(parent)

        self.confocaltabs = QTabWidget()
        self.navigationtab = MinionConfocalNavigation()
        self.tilttab = MinionConfocalTilt()
        self.settingtab = MinionConfocalSetting()

        self.confocaltabs.addTab(self.navigationtab, 'Navigation')
        self.confocaltabs.addTab(self.tilttab, 'Tilt')
        self.confocaltabs.addTab(self.settingtab, 'Settings')

        # self.setFixedSize(650, 800)
        confocallayout = QGridLayout()
        confocallayout.addWidget(self.confocaltabs)
        self.setLayout(confocallayout)


class MinionConfocalNavigation(QWidget):
    def __init__(self, parent=None):
        super(MinionConfocalNavigation, self).__init__(parent)

        # set and get initial variables
        # TODO - get these values from the hardware
        self.xmin = 0.0
        self.xmax = 100.0
        self.xpos = 50.0
        self.ymin = 0.0
        self.ymax = 100.0
        self.ypos = 50.0
        self.resolution = 100
        self.colormin = 0
        self.colormax = 100
        self.mapdata = np.zeros((self.resolution, self.resolution))
        self.colormin = self.mapdata.min()
        self.colormax = self.mapdata.max()
        # TODO - for loop to change mapdata values

        self.uisetup()

    def uisetup(self):
        # create map canvas
        self.mapfigure = Figure()
        self.mapcanvas = FigureCanvas(self.mapfigure)
        self.mapcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.mapcanvas.setFixedSize(600, 500)
        self.toolbar = NavigationToolbar(self.mapcanvas, self)
        self.mapaxes = self.mapfigure.add_subplot(111)
        self.mapaxes.hold(False)

        self.mapdata = MinionColfocalMapDataAquisition().mapdatatemp  #delete later when datastream works

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
        print('resolutiontextchanged')

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
        pass

    def mapstopclicked(self):
        pass

    def mapsaveclicked(self):
        self.filename, *rest = self.mapsavenametext.text().split('.')
        np.savetxt(str(os.getcwd())+'/data/'+str(self.filename)+'.txt', self.mapdata)
        self.mapfigure.savefig(str(os.getcwd())+'/data/'+str(self.filename)+'.pdf')
        print('file saved to data folder')





class MinionConfocalSetting(QWidget):
    def __init__(self, parent=None):
        super(MinionConfocalSetting, self).__init__(parent)

        self.open_confocal = QPushButton('open_confocal')
        confocalsetting_layout = QGridLayout()
        confocalsetting_layout.addWidget(self.open_confocal, 0, 0)
        # confocalsetting_layout.setSpacing(1)
        self.setLayout(confocalsetting_layout)


class MinionConfocalTilt(QWidget):
    def __init__(self, parent=None):
        super(MinionConfocalTilt, self).__init__(parent)

        self.open_confocal = QPushButton('open_confocal')
        confocalsetting_layout = QGridLayout()
        confocalsetting_layout.addWidget(self.open_confocal, 0, 0)
        # confocalsetting_layout.setSpacing(1)
        self.setLayout(confocalsetting_layout)


class MinionColfocalMapDataAquisition(QObject):
    def __init__(self, parent=None):
        super(MinionColfocalMapDataAquisition, self).__init__(parent)

        self.mapdatatemp = np.random.rand(100, 100)*100
