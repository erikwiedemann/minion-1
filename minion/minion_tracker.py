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
        self.resolution1 = 11  # x
        self.resolution2 = 11  # y
        self.resolution3 = 11  # z

        self.centerdataxy = np.zeros((self.resolution2, self.resolution1))
        self.centerdataxz = np.zeros((self.resolution3, self.resolution1))
        self.centerdatayz = np.zeros((self.resolution3, self.resolution2))

        self.mapdata = np.zeros((self.resolution2, self.resolution1))
        self.correlationdata = np.zeros((self.resolution2, self.resolution1))
        self.referencedata = np.zeros((self.resolution2, self.resolution1))
        self.contexttrackerinfo = []


        self.patchlist = []
        self.uisetup()

    def uisetup(self):
        # CENTER TRACKER
        # xy canvas
        self.centerfigurexy = Figure()
        self.centercanvasxy = FigureCanvas(self.centerfigurexy)
        self.centercanvasxy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.centercanvasxy.setMinimumSize(50, 50)
        self.centertoolbarxy = NavigationToolbar(self.centercanvasxy, self)
        self.centeraxesxy = self.centerfigurexy.add_subplot(111)
        self.centeraxesxy.hold(False)

        self.centermapxy = self.centeraxesxy.matshow(self.centerdataxy, origin='lower', extent=[0, self.resolution1, 0, self.resolution2])
        self.centeraxesxy.set_xlabel('xy')
        self.centeraxesxy.xaxis.set_label_position('top')
        self.centercolorbarxy = self.centerfigurexy.colorbar(self.centermapxy, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.centercolorbarxy.formatter.set_scientific(True)
        self.centercolorbarxy.formatter.set_powerlimits((0, 3))
        self.centercolorbarxy.update_ticks()
        self.centeraxesxy.xaxis.set_ticks_position('bottom')
        self.centeraxesxy.xaxis.set_tick_params(direction='out')
        self.centeraxesxy.yaxis.set_ticks_position('left')
        self.centeraxesxy.yaxis.set_tick_params(direction='out')

        # xz canvas
        self.centerfigurexz = Figure()
        self.centercanvasxz = FigureCanvas(self.centerfigurexz)
        self.centercanvasxz.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.centercanvasxz.setMinimumSize(50, 50)
        self.centertoolbarxz = NavigationToolbar(self.centercanvasxz, self)
        self.centeraxesxz = self.centerfigurexz.add_subplot(111)
        self.centeraxesxz.hold(False)

        self.centermapxz = self.centeraxesxz.matshow(self.centerdataxz, origin='lower', extent=[0, self.resolution1, 0, self.resolution3])
        self.centeraxesxz.set_xlabel('xz')
        self.centeraxesxz.xaxis.set_label_position('top')
        self.centercolorbarxz = self.centerfigurexz.colorbar(self.centermapxz, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.centercolorbarxz.formatter.set_scientific(True)
        self.centercolorbarxz.formatter.set_powerlimits((0, 3))
        self.centercolorbarxz.update_ticks()
        self.centeraxesxz.xaxis.set_ticks_position('bottom')
        self.centeraxesxz.xaxis.set_tick_params(direction='out')
        self.centeraxesxz.yaxis.set_ticks_position('left')
        self.centeraxesxz.yaxis.set_tick_params(direction='out')

        # yz canvas
        self.centerfigureyz = Figure()
        self.centercanvasyz = FigureCanvas(self.centerfigureyz)
        self.centercanvasyz.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.centercanvasyz.setMinimumSize(50, 50)
        self.centertoolbaryz = NavigationToolbar(self.centercanvasyz, self)
        self.centeraxesyz = self.centerfigureyz.add_subplot(111)
        self.centeraxesyz.hold(False)

        self.centermapyz = self.centeraxesyz.matshow(self.centerdatayz, origin='lower', extent=[0, self.resolution2, 0, self.resolution3])
        self.centeraxesyz.set_xlabel('yz')
        self.centeraxesyz.xaxis.set_label_position('top')
        self.centercolorbaryz = self.centerfigureyz.colorbar(self.centermapyz, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.centercolorbaryz.formatter.set_scientific(True)
        self.centercolorbaryz.formatter.set_powerlimits((0, 3))
        self.centercolorbaryz.update_ticks()
        self.centeraxesyz.xaxis.set_ticks_position('bottom')
        self.centeraxesyz.xaxis.set_tick_params(direction='out')
        self.centeraxesyz.yaxis.set_ticks_position('left')
        self.centeraxesyz.yaxis.set_tick_params(direction='out')


        self.button = QPushButton('banane')



        # -------------------------------------------------------------------------------------------------------------
        # CONTEXT TRACKER
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
        self.mapaxes.xaxis.set_label_position('top')
        self.mapcolorbar = self.mapfigure.colorbar(self.map, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.mapcolorbar.formatter.set_scientific(True)
        self.mapcolorbar.formatter.set_powerlimits((0, 3))
        self.mapcolorbar.update_ticks()
        self.mapaxes.xaxis.set_ticks_position('bottom')
        self.mapaxes.xaxis.set_tick_params(direction='out')
        self.mapaxes.yaxis.set_ticks_position('left')
        self.mapaxes.yaxis.set_tick_params(direction='out')

        # correlation plot
        self.correlationfigure = Figure()
        self.correlationcanvas = FigureCanvas(self.correlationfigure)
        self.correlationcanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.correlationcanvas.setMinimumSize(50, 50)
        self.correlationtoolbar = NavigationToolbar(self.correlationcanvas, self)
        self.correlationaxes = self.correlationfigure.add_subplot(111)
        self.correlationaxes.hold(False)

        self.correlation = self.correlationaxes.matshow(self.correlationdata, origin='lower', extent=[0, self.resolution1, 0, self.resolution2])
        self.correlationaxes.set_xlabel('autocorrelation')
        self.correlationaxes.xaxis.set_label_position('top')
        self.correlationcolorbar = self.correlationfigure.colorbar(self.correlation, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.correlationcolorbar.formatter.set_scientific(True)
        self.correlationcolorbar.formatter.set_powerlimits((0, 3))
        self.correlationcolorbar.update_ticks()
        self.correlationaxes.xaxis.set_ticks_position('bottom')
        self.correlationaxes.xaxis.set_tick_params(direction='out')
        self.correlationaxes.yaxis.set_ticks_position('left')
        self.correlationaxes.yaxis.set_tick_params(direction='out')

        # reference plot
        self.referencefigure = Figure()
        self.referencecanvas = FigureCanvas(self.referencefigure)
        self.referencecanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.referencecanvas.setMinimumSize(50, 50)
        self.referencetoolbar = NavigationToolbar(self.referencecanvas, self)
        self.referenceaxes = self.referencefigure.add_subplot(111)
        self.referenceaxes.hold(False)

        self.referencemap = self.referenceaxes.matshow(self.referencedata, origin='lower', extent=[0, self.resolution1, 0, self.resolution2])
        self.referenceaxes.set_xlabel('reference')
        self.referenceaxes.xaxis.set_label_position('top')
        self.referencecolorbar = self.referencefigure.colorbar(self.referencemap, fraction=0.046, pad=0.04, cmap=mpl.cm.jet)
        self.referencecolorbar.formatter.set_scientific(True)
        self.referencecolorbar.formatter.set_powerlimits((0, 3))
        self.referencecolorbar.update_ticks()
        self.referenceaxes.xaxis.set_ticks_position('bottom')
        self.referenceaxes.xaxis.set_tick_params(direction='out')
        self.referenceaxes.yaxis.set_ticks_position('left')
        self.referenceaxes.yaxis.set_tick_params(direction='out')

        # control
        self.contexttrackertable = QTableWidget()
        self.contexttrackertable.setColumnCount(4)
        # self.contexttrackertable.setRowCount(1000)
        self.contexttrackertable.setHorizontalHeaderLabels(('xcorr', 'ycorr', 'zcorr', 'status'))
        self.contexttrackertable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contexttrackertable.resizeColumnsToContents()
        self.contexttrackertable.horizontalHeader().setStretchLastSection(True)

        self.loadlastscanbutton = QPushButton('load last scan')
        self.loadlastscanbutton.clicked.connect(self.loadlastscan)
        self.clearreferencebutton = QPushButton('clear reference')
        self.clearreferencebutton.clicked.connect(self.clearreference)

        self.contexttrackerstartbutton = QPushButton('start context tracker')
        self.contexttrackerstartbutton.clicked.connect(self.contexttrackerstartclicked)

        self.contexttrackerstopbutton = QPushButton('stop context tracker')
        self.contexttrackerstopbutton.clicked.connect(self.contexttrackerstopclicked)

        # LAYOUT
        self.tabs = QTabWidget()
        self.centertrackertab = QWidget()
        self.maptrackertab = QWidget()

        # -------------------------------------------------------------------------------------------------------------
        # centertracker
        centertrackertablayout = QGridLayout()
        centertrackerplotbox = QVBoxLayout()
        centertrackerplotbox.addWidget(self.centercanvasxy)
        centertrackerplotbox.addWidget(self.centertoolbarxy)
        centertrackerplotbox.addWidget(self.centercanvasxz)
        centertrackerplotbox.addWidget(self.centertoolbarxz)
        centertrackerplotbox.addWidget(self.centercanvasyz)
        centertrackerplotbox.addWidget(self.centertoolbaryz)
        centertrackertablayout.addLayout(centertrackerplotbox, 0, 0)


        centertrackertablayout.addWidget(self.button, 0, 1)

        # -------------------------------------------------------------------------------------------------------------
        # maptracker
        maptrackertablayout = QGridLayout()


        maptrackertablayout.addWidget(self.mapcanvas, 0, 0, 10, 10)
        maptrackertablayout.addWidget(self.maptoolbar, 10, 0, 1, 10)
        maptrackertablayout.addWidget(self.correlationcanvas, 0, 10, 10, 10)
        maptrackertablayout.addWidget(self.correlationtoolbar, 10, 10, 1, 10)
        maptrackertablayout.addWidget(self.referencecanvas, 0, 20, 10, 10)
        maptrackertablayout.addWidget(self.referencetoolbar, 10, 20, 1, 10)

        maptrackertablayout.addWidget(self.contexttrackertable, 11, 0, 10, 10)
        maptrackertablayout.addWidget(self.loadlastscanbutton, 11, 10)
        maptrackertablayout.addWidget(self.clearreferencebutton, 12, 10)
        maptrackertablayout.addWidget(self.contexttrackerstartbutton, 13, 10)
        maptrackertablayout.addWidget(self.contexttrackerstopbutton, 14, 10)

        # -------------------------------------------------------------------------------------------------------------
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
        self.correlation.set_extent([0, self.resolution1, 0, self.resolution2])
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
        self.contexttrackerinfo = []
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

    def updatemap(self, mapdata, correlation, xcorr, ycorr, zcorr, status):
        tstart = time.time()
        self.contexttrackerinfo.append([xcorr, ycorr, zcorr, status])
        self.contexttrackertable.clearContents()
        self.contexttrackertable.setRowCount(len(self.contexttrackerinfo))
        for i, element in enumerate(self.contexttrackerinfo):
            for j in range(4):
                self.contexttrackertable.setItem(i, j, QTableWidgetItem(str(element[j])))
        self.contexttrackertable.scrollToBottom()

        self.mapdata = mapdata
        self.correlationdata = correlation

        self.map.set_data(self.mapdata)
        self.map.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.set_clim(vmin=self.mapdata.min(), vmax=self.mapdata.max())
        self.mapcolorbar.draw_all()
        # remove patches
        for patch in self.patchlist:
            patch.remove()
        self.patchlist = []
        self.mapcanvas.draw()

        self.correlation.set_data(self.correlationdata)
        self.correlation.set_clim(vmin=self.correlationdata.min(), vmax=self.correlationdata.max())
        self.correlationcolorbar.set_clim(vmin=self.correlationdata.min(), vmax=self.correlationdata.max())
        self.correlationcolorbar.draw_all()
        self.correlationcanvas.draw()
        print(time.time()-tstart)




class MinionContextTracker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, np.ndarray, float, float, float, str)  # floats are corrections in x y z
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
            dx, dy = np.random.randint(0, 20, size=2)
            self.data = np.roll(self.data, dx, axis=0)
            self.data = np.roll(self.data, dy, axis=1)
            self.data[0:dy, :] = 0.
            self.data[:, 0:dx] = 0.
            self.correlation = sig.fftconvolve(self.data, self.referencedata[::-1, ::-1], 'same')
            maxposy, maxposx = np.unravel_index(self.correlation.argmax(), self.correlation.shape)
            xcorrect = int(np.round(self.resolution1/2-maxposx))
            ycorrect = int(np.round(self.resolution2/2-maxposy))
            self.data = np.roll(self.data, ycorrect, axis=0)
            self.data = np.roll(self.data, xcorrect, axis=1)

            # check result
            self.correlation1 = sig.fftconvolve(self.data, self.referencedata[::-1, ::-1], 'same')
            maxposx, mayposy = np.unravel_index(self.correlation1.argmax(), self.correlation1.shape)

            self.update.emit(self.data, self.correlation, xcorrect, ycorrect, self.correlation.max(), time.strftime('%H:%M:%S')+' - ok')

            print('tracking took ', time.time()-t_trackerstart, 's')
            print('\t context tracking done')

            self.goon.emit()



