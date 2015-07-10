print('executing minion.minion_tracker')
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
        self.resolution1 = 51  # x
        self.resolution2 = 51  # y
        self.mapdata = np.zeros((self.resolution2, self.resolution1))
        self.referencedata = np.zeros((self.resolution2, self.resolution1))

        self.patchlist = []
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

        self.map = self.mapaxes.matshow(self.mapdata, origin='lower', extent=[0, self.resolution1, 0, self.resolution2])
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

        # control
        self.loadlastscanbutton = QPushButton('load last scan')
        self.loadlastscanbutton.clicked.connect(self.loadlastscan)
        self.clearreferencebutton = QPushButton('clear reference')
        self.clearreferencebutton.clicked.connect(self.clearreference)

        self.contexttrackerstartbutton = QPushButton('start context tracker')
        self.contexttrackerstartbutton.clicked.connect(self.contexttrackerstartclicked)

        self.contexttrackerstopbutton = QPushButton('stop context tracker')
        self.contexttrackerstopbutton.clicked.connect(self.contexttrackerstopclicked)

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
        maptrackertablayout.addWidget(self.referencecanvas, 11, 0, 10, 10)
        maptrackertablayout.addWidget(self.referencetoolbar, 21, 0, 1, 10)
        maptrackertablayout.addWidget(self.loadlastscanbutton)
        maptrackertablayout.addWidget(self.clearreferencebutton)
        maptrackertablayout.addWidget(self.contexttrackerstartbutton)
        maptrackertablayout.addWidget(self.contexttrackerstopbutton)

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
        self.resolution2, self.resolution1 = np.shape(self.mapdata)
        self.referencedata = np.zeros((self.resolution2, self.resolution1))

        self.map.set_data(self.mapdata)
        self.map.set_extent([0, self.resolution1, 0, self.resolution2])
        self.referencemap.set_extent([0, self.resolution1, 0, self.resolution2])
        self.map.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.draw_all()
        self.mapcanvas.draw()

    def onselect(self, eclick, erelease):
        """eclick and erelease are matplotlib events at press and release"""
        xspan = np.round((np.min([eclick.xdata, erelease.xdata]), np.max([eclick.xdata, erelease.xdata]))).astype(int)
        yspan = np.round((np.min([eclick.ydata, erelease.ydata]), np.max([eclick.ydata, erelease.ydata]))).astype(int)
        self.patchlist.append(Rectangle((xspan[0], yspan[0]), xspan[1]-xspan[0], yspan[1]-yspan[0], fill=False, ec='r', lw=2))
        self.mapaxes.add_patch(self.patchlist[-1])
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

    def clearreference(self):
        self.referencedata = np.zeros((self.resolution2, self.resolution1))
        self.referencemap.set_data(self.referencedata)
        self.referencemap.set_clim(vmin=self.referencedata.min(), vmax=self.referencedata.max())
        self.referencecolorbar.set_clim(vmin=self.referencedata.min(), vmax=self.referencedata.max())
        self.referencecolorbar.draw_all()
        self.referencecanvas.draw()

        # remove patches
        for patch in self.patchlist:
            patch.remove()
        self.patchlist = []
        self.mapcanvas.draw()

    def contexttrackerstartclicked(self):
        print("[%s] start tracker" % QThread.currentThread().objectName())
        self.contexttracker = MinionContextTracker(self.referencedata, self.mapdata)
        self.contexttrackerthread = QThread(self, objectName='workerThread')
        self.contexttracker.moveToThread(self.contexttrackerthread)
        self.contexttracker.finished.connect(self.contexttrackerthread.quit)

        self.contexttrackerthread.started.connect(self.contexttracker.longrun)
        self.contexttrackerthread.finished.connect(self.contexttrackerthread.deleteLater)
        self.contexttracker.update.connect(self.updatemap)
        self.contexttrackerthread.start()

    def contexttrackerstopclicked(self):
        try:
            print('abort context tracker')
            self.contexttracker.stop()
            self.contexttrackerthread.quit()
        except:
            print('no context tracker running')

    def updatemap(self, correlation, xcorr, ycorr, maxval):
        self.map.set_data(correlation)
        self.map.set_clim(vmin=correlation.min(), vmax=correlation.max())
        self.mapcolorbar.set_clim(vmin=correlation.min(), vmax=correlation.max())
        self.mapcolorbar.draw_all()
        self.mapcanvas.draw()

        # remove patches
        for patch in self.patchlist:
            patch.remove()
        self.patchlist = []
        self.mapcanvas.draw()


class MinionContextTracker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, float, float, float)  # floats are corrections in x y z
    wait = pyqtSignal()
    goon = pyqtSignal()

    def __init__(self, referencedata, data,  parent=None): # remove data as not needed
        super(MinionContextTracker, self).__init__(parent)
        self.referencedata = referencedata
        self.data = data
        self.resolution2, self.resolution1 = np.shape(self.referencedata)

        self._isRunning = True

    def stop(self):
        self._isRunning = False
        self.contexttrackertimer.stop()
        print('total time tracked:', time.time()-self.tstart)
        print('thread done')
        self.finished.emit()

    def longrun(self):
        if self._isRunning:
            self.contexttrackertimer = QTimer()
            self.contexttrackertimer.setInterval(1000*5)  # ms
            self.contexttrackertimer.timeout.connect(self.contexttrack)
            self.tstart = time.time()
            self.contexttrackertimer.start()

    def contexttrack(self):
        print("[%s] tracking" % QThread.currentThread().objectName())
        if self._isRunning:
            self.wait.emit()
            t_trackerstart = time.time()
            print('\t start context tracking')
            dx, dy = np.random.randint(-30, 30, size=2)
            self.data = np.roll(self.data, dx, axis=0)
            self.data = np.roll(self.data, dy, axis=1)
            self.correlation = sig.fftconvolve(self.data, self.referencedata[::-1, ::-1], 'same')  # best solution!!! - 100 times faster
            maxposy, maxposx = np.unravel_index(self.correlation.argmax(), self.correlation.shape)
            print(maxposx, maxposy, self.correlation.argmax())
            xcorrect = int(np.round(self.resolution1/2-maxposx))
            ycorrect = int(np.round(self.resolution2/2-maxposy))
            print(xcorrect, ycorrect)
            self.data = np.roll(self.data, ycorrect, axis=0)
            self.data = np.roll(self.data, xcorrect, axis=1)
            # check result
            self.correlation1 = sig.fftconvolve(self.data, self.referencedata[::-1, ::-1], 'same')  # best solution!!! - 100 times faster
            maxposx, mayposy = np.unravel_index(self.correlation1.argmax(), self.correlation1.shape)
            print(maxposx, mayposy, self.correlation1.argmax())
            self.update.emit(self.correlation, xcorrect, ycorrect, self.correlation.argmax())

            print('tracking took ', time.time()-t_trackerstart, 's')
            print('\t context tracking done')

            self.goon.emit()



