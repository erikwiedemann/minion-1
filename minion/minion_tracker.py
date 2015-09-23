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

from ctypes import *
import serial



class MinionTrackerUI(QWidget):
    def __init__(self, parent):
        super(MinionTrackerUI, self).__init__(parent)
        self.parent = parent

        self.resolution1 = 11  # x
        self.resolution2 = 11  # y
        self.resolution3 = 21  # z

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


        self.findcenterbutton = QPushButton('find center at crosshair pos')
        self.findcenterbutton.clicked.connect(self.findcenterclicked)
        self.findcenterabortbutton = QPushButton('abort')
        self.findcenterabortbutton.clicked.connect(self.findcenterabortclicked)

        self.findmaxbutton = QPushButton('find max at crosshair pos')
        self.findmaxbutton.clicked.connect(self.findmaxclicked)


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
        centertrackertablayout.addLayout(centertrackerplotbox, 0, 0, 5, 1)


        centertrackertablayout.addWidget(self.findcenterbutton, 0, 1)
        centertrackertablayout.addWidget(self.findmaxbutton, 1, 1)
        centertrackertablayout.addWidget(self.findcenterabortbutton, 2, 1)

        # -------------------------------------------------------------------------------------------------------------
        # maptracker
        maptrackertablayout = QGridLayout()

        maptrackerplotbox = QHBoxLayout()
        plotbox1 = QVBoxLayout()
        plotbox1.addWidget(self.mapcanvas)
        plotbox1.addWidget(self.maptoolbar)
        plotbox2 = QVBoxLayout()
        plotbox2.addWidget(self.correlationcanvas)
        plotbox2.addWidget(self.correlationtoolbar)
        plotbox3 = QVBoxLayout()
        plotbox3.addWidget(self.referencecanvas)
        plotbox3.addWidget(self.referencetoolbar)
        maptrackerplotbox.addLayout(plotbox1)
        maptrackerplotbox.addLayout(plotbox2)
        maptrackerplotbox.addLayout(plotbox3)
        maptrackertablayout.addLayout(maptrackerplotbox, 0, 0, 10, 30)
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

    def findcenterclicked(self):
        print("[%s] start scan" % QThread.currentThread().objectName())
        if self.parent.hardware_stage is True and self.parent.hardware_counter is True:
            self.findcenter = MinionFindCenter(self.parent.fpga, self.parent.stagelib, self.parent.stage, self.parent.confocalwidget.xpos, self.parent.confocalwidget.ypos, self.parent.confocalwidget.zpos)
            self.findcenterthread = QThread(self, objectName='workerThread')
            self.findcenter.moveToThread(self.findcenterthread)
            self.findcenter.finished.connect(self.findcenterthread.quit)

            self.findcenterthread.started.connect(self.findcenter.longrun)
            self.findcenterthread.finished.connect(self.findcenterthread.deleteLater)
            self.findcenter.update.connect(self.updatefindcentermaps)
            self.findcenterthread.start()

    def findmaxclicked(self):
        print("[%s] start search for max" % QThread.currentThread().objectName())
        if self.parent.hardware_stage is True and self.parent.hardware_counter is True:
            self.findmax = MinionCenterTracker(self.parent.fpga, self.parent.stagelib, self.parent.stage, self.parent.confocalwidget.xpos, self.parent.confocalwidget.ypos, self.parent.confocalwidget.zpos)
            self.findmaxthread = QThread(self, objectName='workerThread')
            self.findmax.moveToThread(self.findmaxthread)
            self.findmax.finished.connect(self.findmaxthread.quit)

            self.findmaxthread.started.connect(self.findmax.longrun)
            self.findmaxthread.finished.connect(self.findmaxthread.deleteLater)
            # self.findmax.update.connect(self.updatefindcentermaps)
            self.findmaxthread.start()

    def findcenterabortclicked(self):
        try:
            print('abort center find')
            self.findcenter.stop()
            self.findcenterthread.quit()
        except:
            print('no center finder running')
        try:
            print('abort max find')
            self.findmax.stop()
            self.findmaxthread.quit()
        except:
            print('no max finder running')


    @pyqtSlot(np.ndarray, np.ndarray, np.ndarray, float, float, float)
    def updatefindcentermaps(self, xymapdataupdate, xzmapdataupdate, yzmapdataupdate, pos1, pos2, pos3):
        # print("[%s] update" % QThread.currentThread().objectName())
        self.xymapdata, self.xzmapdata, self.yzmapdata = xymapdataupdate.T, xzmapdataupdate.T, yzmapdataupdate.T
        self.centermapxy.set_data(self.xymapdata)
        self.xycolormin = self.xymapdata.min()
        self.xycolormax = self.xymapdata.max()
        self.centermapxy.set_clim(vmin=self.xycolormin, vmax=self.xycolormax)
        self.centercolorbarxy.set_clim(vmin=self.xycolormin, vmax=self.xycolormax)
        self.centercolorbarxy.draw_all()

        self.centermapxz.set_data(self.xzmapdata)
        self.xzcolormin = self.xzmapdata.min()
        self.xzcolormax = self.xzmapdata.max()
        self.centermapxz.set_clim(vmin=self.xzcolormin, vmax=self.xzcolormax)
        self.centercolorbarxz.set_clim(vmin=self.xzcolormin, vmax=self.xzcolormax)
        self.centercolorbarxz.draw_all()

        self.centermapyz.set_data(self.yzmapdata)
        self.yzcolormin = self.yzmapdata.min()
        self.yzcolormax = self.yzmapdata.max()
        self.centermapyz.set_clim(vmin=self.yzcolormin, vmax=self.yzcolormax)
        self.centercolorbaryz.set_clim(vmin=self.yzcolormin, vmax=self.yzcolormax)
        self.centercolorbaryz.draw_all()

        self.centermapxy.set_extent([self.parent.confocalwidget.xpos-0.5, self.parent.confocalwidget.xpos+0.5, self.parent.confocalwidget.xpos-0.5, self.parent.confocalwidget.xpos+0.5])
        self.centermapxz.set_extent([self.parent.confocalwidget.xpos-0.5, self.parent.confocalwidget.xpos+0.5, self.parent.confocalwidget.zpos-1., self.parent.confocalwidget.zpos+1.])
        self.centermapyz.set_extent([self.parent.confocalwidget.ypos-0.5, self.parent.confocalwidget.ypos+0.5, self.parent.confocalwidget.zpos-1., self.parent.confocalwidget.zpos+1.])
        self.centercanvasxy.draw()
        self.centercanvasxz.draw()
        self.centercanvasyz.draw()

        # print(time.time()-start)

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
        self.contexttracker.update.connect(self.updatecontextmap)
        self.contexttrackerthread.start()

    def contexttrackerstopclicked(self):
        try:
            print('abort context tracker')
            self.contexttracker.stop()
            self.contexttrackerthread.quit()
        except:
            print('no context tracker running')

    def updatecontextmap(self, mapdata, correlation, xcorr, ycorr, zcorr, status):
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

    def __init__(self, referencedata, data,  parent=None):  # remove data as not needed
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


class MinionCenterTracker(QObject):  # currently only greedy climbing hill
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, np.ndarray, float, float, float, str)  # floats are corrections in x y z
    wait = pyqtSignal()
    goon = pyqtSignal()

    def __init__(self, fpga, stagelib, stage, xpos, ypos, zpos,  parent=None):  # TODO - get all variables to ui for tracker
        super(MinionCenterTracker, self).__init__(parent)
        self.fpga, self.stagelib, self.stage, self.xpos, self.ypos, self.zpos = fpga, stagelib, stage, xpos, ypos, zpos
        self.stepsize = 0.1  # um - change to 0.05
        self.stepsize_decrease = 0.5  # factor to which the stepsize decreases - i.e. 0.5 = 50 %
        self.stepsize_corse = 0.1  # um
        self.stepsize_fine = 0.005  # um
        self.stepsize_restart = 0.05  # um
        self.restart_max = 2
        self.counttime = 0.01  # s
        self.settletime = 0.005  # s
        self.tolerance = 0.01  # how much bigger has the new value to be
        self.distlimit = 2  # abort tracker if distance between initial and new coord is bigger this
        self.average_over_measurement = 5

    def longrun(self):
        self.fpga.setcountingtime(counttime=self.counttime)
        # backup values
        self.init_coord = [self.xpos, self.ypos, self.zpos]  # current stage pos
        self.init_node = 0
        for countrun in range(self.average_over_measurement):  # for reference
            apd1, apd2, apd_sum = self.fpga.count()
            self.init_node += apd_sum
        self.init_node /= self.average_over_measurement

        print('init coord and value:', self.init_coord, self.init_node)

        self.kernel = np.zeros((3, 3, 3))  # preallocate
        # measure adjacent coords
        self.current_node = self.init_node
        self.current_coord = self.init_coord
        self.new_node = self.current_node
        self.new_coord = [0., 0., 0.]
        self.success = False
        self.error = False
        self.number_restarts = 0
        self.run_number = 0
        t0=time.time()
        while self.success is not True and self.error is not True:
            self.run_number += 1
            self.kernel *= 0
            for (i, j, k), value in np.ndenumerate(self.kernel):
                self.new_coord = [self.current_coord[0]+(i-1)*self.stepsize, self.current_coord[1]+(j-1)*self.stepsize, self.current_coord[2]+(k-1)*self.stepsize]
                # print('new coord in kernel:', self.new_coord)
                # go to new pos
                status1 = self.stagelib.MCL_SingleWriteN(c_double(self.new_coord[0]), 2, self.stage)  #x
                status2 = self.stagelib.MCL_SingleWriteN(c_double(self.new_coord[1]), 1, self.stage)  #y
                status3 = self.stagelib.MCL_SingleWriteN(c_double(self.new_coord[2]), 3, self.stage)  #z
                time.sleep(self.settletime)
                for countrun in range(self.average_over_measurement):
                    apd1, apd2, apd_sum = self.fpga.count()
                    self.kernel[i, j, k] += apd_sum
                self.kernel[i, j, k] /= self.average_over_measurement
            maxpos = np.asarray(np.unravel_index(self.kernel.argmax(), self.kernel.shape))
            self.new_coord = [self.current_coord[0]+(maxpos[0]-1)*self.stepsize, self.current_coord[1]+(maxpos[1]-1)*self.stepsize, self.current_coord[2]+(maxpos[2]-1)*self.stepsize]
            self.new_node = self.kernel[maxpos[0], maxpos[1], maxpos[2]]
            # print('____________')
            # print(maxpos)
            # print(self.kernel)
            # print('stepsize:', self.stepsize_corse)
            # print('new coord:', self.new_coord)
            # print('new value:', self.new_node)
            # print('previous value:', self.current_node)
            # print('restarts:', self.number_restarts)

            if abs(np.linalg.norm(np.array(self.init_coord)-np.array(self.new_coord))) > self.distlimit:
                self.error = True
                print('max dist from init. position reached - aborting tracking')
            else:
                if self.new_node > self.current_node+self.current_node*self.tolerance:
                    self.current_node = self.new_node
                    self.current_coord = self.new_coord
                else:
                    self.stepsize_corse *= self.stepsize_decrease
                    if self.stepsize_corse < self.stepsize_fine:
                        self.stepsize_corse = self.stepsize_restart
                        if self.number_restarts >= self.restart_max:
                            self.success = True
                        self.number_restarts += 1

        if self.success is True:
            print('optimized coord and counts:', self.current_coord, self.current_node)
            print('success after:', time.time()-t0)
            # go to optimized coord
            status1 = self.stagelib.MCL_SingleWriteN(c_double(self.current_coord[0]), 2, self.stage)  #x
            status2 = self.stagelib.MCL_SingleWriteN(c_double(self.current_coord[1]), 1, self.stage)  #y
            status3 = self.stagelib.MCL_SingleWriteN(c_double(self.current_coord[2]), 3, self.stage)  #z

        if self.error is True:
            print('going to initial coord:', self.init_coord)
            print('error after:', time.time()-t0)
            self.current_coord = self.init_coord
            status1 = self.stagelib.MCL_SingleWriteN(c_double(self.init_coord[0]), 2, self.stage)  #x
            status2 = self.stagelib.MCL_SingleWriteN(c_double(self.init_coord[1]), 1, self.stage)  #y
            status3 = self.stagelib.MCL_SingleWriteN(c_double(self.init_coord[2]), 3, self.stage)  #z

        return self.current_coord




class MinionFindCenter(QObject): # fit ellipses to maps and center them in 3d
    started = pyqtSignal()
    finished = pyqtSignal()
    update = pyqtSignal(np.ndarray, np.ndarray, np.ndarray, float, float, float)  # floats are corrections in x y z
    wait = pyqtSignal()
    goon = pyqtSignal()

    def __init__(self, fpga, stagelib, stage, xpos, ypos, zpos,  parent=None):
        super(MinionFindCenter, self).__init__(parent)
        self.fpga, self.stagelib, self.stage, self.xpos, self.ypos, self.zpos = fpga, stagelib, stage, xpos, ypos, zpos
        self.resolution1 = 9
        self.resolution2 = 9
        self.resolution3 = 11
        self.counttime = 0.005
        self.settlingtime = 0.01

        # set count and settle times
        self.fpga.setcountingtime(self.counttime)
        self.check_counttime = self.fpga.checkcounttime()
        print('\t fpga counttime:', self.check_counttime)
        print('\t counttime:', self.counttime)
        print('\t settlingtime:', self.settlingtime)

        self._isRunning = True
        print("[%s] create worker" % QThread.currentThread().objectName())

    def stop(self):
        self._isRunning = False


    def longrun(self):
        x = np.linspace(0, self.resolution1-1, self.resolution1)
        y = np.linspace(0, self.resolution2-1, self.resolution2)
        x, y = np.meshgrid(x, y)
        def creategaussian(x, y, height, x0, y0, sigmax, sigmay, rot, offset):
            phi = np.deg2rad(rot)
            a = np.cos(phi)**2/(2.*sigmax**2) + np.sin(phi)**2/(2.*sigmay**2)
            b = - np.sin(2.*phi)/(4.*sigmax**2) + np.sin(2.*phi)/(4.*sigmay**2)
            c = np.sin(phi)**2/(2.*sigmax**2) + np.cos(phi)**2/(2.*sigmay**2)

            fn = offset + height*np.exp(-(a*(x-x0)**2 + 2*b*(x-x0)*(y-y0) + c*(y-y0)**2))
            return fn

        def fit_fun(data, height, x0, y0, sigmax, sigmay, rot, offset):
            guess = creategaussian(x, y, height, x0, y0, sigmax, sigmay, rot, offset)
            return np.ravel(guess)

        xymapdataupdate = np.zeros((self.resolution1, self.resolution2))
        xzmapdataupdate = np.zeros((self.resolution1, self.resolution3))
        yzmapdataupdate = np.zeros((self.resolution2, self.resolution3))
        print("[%s] start scan" % QThread.currentThread().objectName())
        print('looking for center at \t x:', self.xpos, 'y:', self.ypos, 'z:', self.zpos)
        findstatus = False

        tstart = time.time()
        while not findstatus:
            # self.poserrorx = 0.
            # self.poserrory = 0.
            # self.poserrorz = 0.
            # xy input prep
            xydim1 = np.linspace(self.xpos-0.5, self.xpos+0.5, self.resolution1)  # 1-x
            xydim2 = np.linspace(self.ypos-0.5, self.ypos+0.5, self.resolution2)  # 2-y
            self.xyaxis1 = 2
            self.xyaxis2 = 1
            self.xyaxis3 = 3

            xydim1 = np.tile(xydim1, (1, self.resolution2))
            xydim2 = np.tile(xydim2, (self.resolution1, 1))
            xydim2 = xydim2.T
            self.xylist1 = np.reshape(xydim1, (1, self.resolution1*self.resolution2))
            self.xylist2 = np.reshape(xydim2, (1, self.resolution1*self.resolution2))
            xyindexmat = np.indices((self.resolution1, self.resolution2))
            xyindexmat = np.swapaxes(xyindexmat, 0, 2)
            self.xyindexlist = xyindexmat.reshape((1, self.resolution1*self.resolution2, 2))

            # XY scan
            # MOVE TO START POSITION
            status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xylist1[0, 0]), self.xyaxis1, self.stage)
            status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xylist2[0, 0]), self.xyaxis2, self.stage)
            status3 = self.stagelib.MCL_SingleWriteN(c_double(self.zpos), self.xyaxis3, self.stage)
            time.sleep(0.01)

            for i in range(0, self.resolution1*self.resolution2):
                if not self._isRunning:
                    self.finished.emit()
                    findstatus = True
                else:
                    # MOVE
                    status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xylist1[0, i]), self.xyaxis1, self.stage)
                    status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xylist2[0, i]), self.xyaxis2, self.stage)
                    time.sleep(self.settlingtime)  # wait
                    # pos1 = self.stagelib.MCL_SingleReadN(self.xyaxis1, self.stage)
                    # pos2 = self.stagelib.MCL_SingleReadN(self.xyaxis2, self.stage)
                    # pos3 = self.stagelib.MCL_SingleReadN(self.xyaxis3, self.stage)
                    # self.poserrorx += (self.xylist1[0, i] - pos1)
                    # self.poserrory += (self.xylist2[0, i] - pos2)
                    # self.poserrorz += (self.zpos - pos3)
                    if (i+1) % self.resolution1 == 0:
                        # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                        time.sleep(self.settlingtime*2)

                    # COUNT
                    apd1_count, apd2_count, apd_sum = self.fpga.count()  # in cps
                    xymapdataupdate[self.xyindexlist[0, i, 0], self.xyindexlist[0, i, 1]] = apd_sum
            # print('error:', self.poserrorx/(11*11), self.poserrory/(11*11), self.poserrorz/(11*11))

            p0 = [1., self.resolution2/2., self.resolution1/2., self.resolution2/4., self.resolution1/4., 45., 0.1]
            fitdata = xymapdataupdate/xymapdataupdate.max()
            try:
                popt, pcov = opt.curve_fit(fit_fun, fitdata, np.ravel(fitdata), p0)
                maxposx, maxposy = self.xpos-0.5+(popt[2])*1./self.resolution1, self.ypos-0.5+(popt[1])*1./self.resolution2
                if abs(self.xpos-maxposx)<=0.1 and abs(self.ypos-maxposy)<=0.1:
                    self.xpos = maxposx
                    self.ypos = maxposy
                    print('new pos:', self.xpos, self.ypos)
                else:
                    if abs(self.xpos-maxposx) <= 0.1:
                        self.xpos = maxposx
                    else:
                        if maxposx < self.xpos:
                            self.xpos -= 0.1
                        else:
                            self.xpos += 0.1
                    if abs(self.ypos-maxposy) <= 0.1:
                        self.ypos = maxposy
                    else:
                        if maxposy < self.ypos:
                            self.ypos -= 0.1
                        else:
                            self.ypos += 0.1

                    print('new pos too far off')
                    print('new pos:', self.xpos, self.ypos)

            except:
                print('fit did not converge')

            # maxposx, maxposy = np.unravel_index(xymapdataupdate.argmax(), xymapdataupdate.shape)

            self.update.emit(xymapdataupdate, xzmapdataupdate, yzmapdataupdate, self.xpos, self.ypos, 0.)

            # xz input prep
            xzdim1 = np.linspace(self.xpos-0.5, self.xpos+0.5, self.resolution1)  # 1-x
            xzdim2 = np.linspace(self.zpos-1., self.zpos+1., self.resolution3)  # 2-z
            self.xzaxis1 = 2
            self.xzaxis2 = 1
            self.xzaxis3 = 3

            xzdim1 = np.tile(xzdim1, (1, self.resolution3))
            xzdim2 = np.tile(xzdim2, (self.resolution1, 1))
            xzdim2 = xzdim2.T
            self.xzlist1 = np.reshape(xzdim1, (1, self.resolution1*self.resolution3))
            self.xzlist2 = np.reshape(xzdim2, (1, self.resolution1*self.resolution3))
            xzindexmat = np.indices((self.resolution1, self.resolution3))
            xzindexmat = np.swapaxes(xzindexmat, 0, 2)
            self.xzindexlist = xzindexmat.reshape((1, self.resolution1*self.resolution3, 2))

            # XZ scan
            # MOVE TO START POSITION
            status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xzlist1[0, 0]), self.xzaxis1, self.stage)
            status2 = self.stagelib.MCL_SingleWriteN(c_double(self.ypos), self.xzaxis2, self.stage)
            status3 = self.stagelib.MCL_SingleWriteN(c_double(self.xzlist2[0, 0]), self.xzaxis3, self.stage)
            time.sleep(0.01)

            for i in range(0, self.resolution1*self.resolution3):
                if not self._isRunning:
                    self.finished.emit()
                    findstatus = True
                else:
                    # MOVE
                    status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xzlist1[0, i]), self.xzaxis1, self.stage)
                    status2 = self.stagelib.MCL_SingleWriteN(c_double(self.xzlist2[0, i]), self.xzaxis3, self.stage)
                    time.sleep(self.settlingtime)  # wait
                    if (i+1) % self.resolution1 == 0:
                        # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                        time.sleep(self.settlingtime*2)

                    # COUNT
                    apd1_count, apd2_count, apd_sum = self.fpga.count()  # in cps
                    xzmapdataupdate[self.xzindexlist[0, i, 0], self.xzindexlist[0, i, 1]] = apd_sum
            self.update.emit(xymapdataupdate, xzmapdataupdate, yzmapdataupdate, 0., 0., 0.)

            # yz input prep
            yzdim1 = np.linspace(self.ypos-0.5, self.ypos+0.5, self.resolution2)  # 1-y
            yzdim2 = np.linspace(self.zpos-1., self.zpos+1., self.resolution3)  # 2-z
            self.yzaxis1 = 2
            self.yzaxis2 = 1
            self.yzaxis3 = 3

            yzdim1 = np.tile(yzdim1, (1, self.resolution3))
            yzdim2 = np.tile(yzdim2, (self.resolution2, 1))
            yzdim2 = yzdim2.T
            self.yzlist1 = np.reshape(yzdim1, (1, self.resolution2*self.resolution3))
            self.yzlist2 = np.reshape(yzdim2, (1, self.resolution2*self.resolution3))
            yzindexmat = np.indices((self.resolution2, self.resolution3))
            yzindexmat = np.swapaxes(yzindexmat, 0, 2)
            self.yzindexlist = yzindexmat.reshape((1, self.resolution2*self.resolution3, 2))

            # YZ scan
            # MOVE TO START POSITION
            status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xpos), self.yzaxis1, self.stage)
            status2 = self.stagelib.MCL_SingleWriteN(c_double(self.yzlist1[0, 0]), self.yzaxis2, self.stage)
            status3 = self.stagelib.MCL_SingleWriteN(c_double(self.yzlist2[0, 0]), self.yzaxis3, self.stage)
            time.sleep(0.01)

            for i in range(0, self.resolution2*self.resolution3):
                if not self._isRunning:
                    self.finished.emit()
                    findstatus = True
                else:
                    # MOVE
                    status1 = self.stagelib.MCL_SingleWriteN(c_double(self.yzlist1[0, i]), self.yzaxis2, self.stage)
                    status2 = self.stagelib.MCL_SingleWriteN(c_double(self.yzlist2[0, i]), self.yzaxis3, self.stage)
                    time.sleep(self.settlingtime)  # wait
                    if (i+1) % self.resolution2 == 0:
                        # when start new line wait a total of 3 x settlingtime before starting to count - TODO - add to gui
                        time.sleep(self.settlingtime*2)

                    # COUNT
                    apd1_count, apd2_count, apd_sum = self.fpga.count()  # in cps
                    yzmapdataupdate[self.yzindexlist[0, i, 0], self.yzindexlist[0, i, 1]] = apd_sum
            self.update.emit(xymapdataupdate, xzmapdataupdate, yzmapdataupdate, 0., 0., 0.)
            print('one round done')

        self.update.emit(xymapdataupdate, xzmapdataupdate, yzmapdataupdate, 0., 0., 0.)
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.xpos), self.xyaxis1, self.stage)
        status2 = self.stagelib.MCL_SingleWriteN(c_double(self.ypos), self.xyaxis2, self.stage)
        status1 = self.stagelib.MCL_SingleWriteN(c_double(self.zpos), self.xyaxis3, self.stage)
        xyfname = time.strftime('scanhistory/'+'%Y-%m-%d_%H-%M-%S')+'_scan_xy.txt'
        xzfname = time.strftime('scanhistory/'+'%Y-%m-%d_%H-%M-%S')+'_scan_xz.txt'
        yzfname = time.strftime('scanhistory/'+'%Y-%m-%d_%H-%M-%S')+'_scan_yz.txt'
        np.savetxt(xyfname, xymapdataupdate)
        np.savetxt(xzfname, xzmapdataupdate)
        np.savetxt(yzfname, yzmapdataupdate)

        print('total time needed:', time.time()-tstart)
        print('thread done')
        self.finished.emit()