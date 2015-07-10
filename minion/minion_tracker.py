import numpy as np
import scipy.optimize as opt
import matplotlib as mpl
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle


class MinionTrackerUI(QWidget):
    def __init__(self, parent=None):
        super(MinionTrackerUI, self).__init__(parent)
        self.resolution1 = 51
        self.resolution2 = 51
        self.mapdata = np.zeros((self.resolution1, self.resolution2))
        self.referencedata = np.zeros((self.resolution1, self.resolution2))
        self.uisetup()

    def uisetup(self):
        # centertracker
        self.button = QPushButton('banane')






        # maptracker
        # map plot
        self.mapfigure = Figure()
        self.mapcanvas = FigureCanvas(self.mapfigure)
        self.mapcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mapcanvas.setMinimumSize(50, 50)



        self.maptoolbar = NavigationToolbar(self.mapcanvas, self)
        self.mapaxes = self.mapfigure.add_subplot(111)
        self.mapaxes.hold(False)
        rectprops = dict(edgecolor='w', fill=False, linewidth=2)
        self.RS = RectangleSelector(self.mapaxes, self.onselect, drawtype='box', minspanx=3, minspany=3, button=1, useblit=True, rectprops=rectprops)

        self.map = self.mapaxes.matshow(self.mapdata, origin='lower')# , extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.mapaxes.set_xlabel('scan')
        self.mapcolorbar = self.mapfigure.colorbar(self.map, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.mapcolorbar.formatter.set_scientific(True)
        self.mapcolorbar.formatter.set_powerlimits((0, 3))
        self.mapcolorbar.update_ticks()
        self.mapaxes.xaxis.set_ticks_position('bottom')
        self.mapaxes.xaxis.set_tick_params(direction='out')
        self.mapaxes.yaxis.set_ticks_position('left')
        self.mapaxes.yaxis.set_tick_params(direction='out')

        # reference plot
        self.referencefigure = Figure()
        self.referencecanvas = FigureCanvas(self.referencefigure)
        self.referencecanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.referencecanvas.setMinimumSize(50, 50)
        self.referencetoolbar = NavigationToolbar(self.referencecanvas, self)
        self.referenceaxes = self.referencefigure.add_subplot(111)
        self.referenceaxes.hold(False)

        self.referencemap = self.referenceaxes.matshow(self.referencedata, origin='lower')# , extent=[self.xmin, self.xmax, self.ymin, self.ymax])
        self.referenceaxes.set_xlabel('reference')
        self.referencecolorbar = self.referencefigure.colorbar(self.referencemap, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.referencecolorbar.formatter.set_scientific(True)
        self.referencecolorbar.formatter.set_powerlimits((0, 3))
        self.referencecolorbar.update_ticks()
        self.referenceaxes.xaxis.set_ticks_position('bottom')
        self.referenceaxes.xaxis.set_tick_params(direction='out')
        self.referenceaxes.yaxis.set_ticks_position('left')
        self.referenceaxes.yaxis.set_tick_params(direction='out')





        self.loadlastscanbutton = QPushButton('load last scan')
        self.loadlastscanbutton.clicked.connect(self.loadlastscan)





        # layout
        self.tabs = QTabWidget()
        self.centertrackertab = QWidget()
        self.maptrackertab = QWidget()

        # centertracker
        centertrackertablayout = QVBoxLayout()
        centertrackertablayout.addWidget(self.button)


        # maptracker
        maptrackertablayout = QGridLayout()
        maptrackertablayout.addWidget(self.mapcanvas, 0, 0, 10, 10)
        maptrackertablayout.addWidget(self.maptoolbar, 10, 0, 1, 10)
        maptrackertablayout.addWidget(self.referencecanvas, 0, 10, 10, 10)
        maptrackertablayout.addWidget(self.referencetoolbar, 10, 10, 1, 10)
        maptrackertablayout.addWidget(self.loadlastscanbutton)




        # unite the tabs
        self.centertrackertab.setLayout(centertrackertablayout)
        self.maptrackertab.setLayout(maptrackertablayout)

        self.tabs.addTab(self.centertrackertab, 'centertracker')
        self.tabs.addTab(self.maptrackertab, 'maptracker')
        trackerlayout = QGridLayout()
        trackerlayout.addWidget(self.tabs)
        self.setLayout(trackerlayout)

    def loadlastscan(self):
        filelist = os.listdir(os.getcwd()+'/scanhistory/')
        fname = max(filelist, key=lambda x: os.stat('scanhistory/'+x).st_mtime)
        self.mapdata = np.loadtxt('scanhistory/'+fname)
        print('\t load: '+fname)
        self.resolution2, self.resolution = np.shape(self.mapdata)
        self.map.set_data(self.mapdata)
        self.map.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.draw_all()
        self.mapcanvas.draw()

    def onselect(self, eclick, erelease):
        'eclick and erelease are matplotlib events at press and release'
        xspan = np.round((np.min([eclick.xdata, erelease.xdata]), np.max([eclick.xdata, erelease.xdata]))).astype(int)
        yspan = np.round((np.min([eclick.ydata, erelease.ydata]), np.max([eclick.ydata, erelease.ydata]))).astype(int)
        self.mapaxes.add_patch(Rectangle((xspan[0], yspan[0]), xspan[1]-xspan[0], yspan[1]-yspan[0], fill=False, ec='r', lw=2))
        self.mapcanvas.draw()
        print(' x: '+str(xspan))
        print(' y: '+str(yspan))
        self.mapdata_cut = self.mapdata[yspan[0]:yspan[1], xspan[0]:xspan[1]]
        self.referencedata[yspan[0]:yspan[1], xspan[0]:xspan[1]] = self.mapdata_cut
        self.referencemap.set_data(self.referencedata)
        self.referencemap.set_clim(vmin=self.referencedata.min(), vmax=self.referencedata.max())
        self.referencecolorbar.set_clim(vmin=self.referencedata.min(), vmax=self.referencedata.max())
        self.referencecolorbar.draw_all()
        self.referencecanvas.draw()




