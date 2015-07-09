import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MinionTrackerUI(QWidget):
    def __init__(self, parent=None):
        super(MinionTrackerUI, self).__init__(parent)

        self.uisetup()

    def uisetup(self):
        # centertracker
        self.button = QPushButton('banane')






        # maptracker
        self.button1 = QPushButton('banane1')

        # layout
        self.tabs = QTabWidget()
        self.centertrackertab = QWidget()
        self.maptrackertab = QWidget()

        # centertracker
        centertrackertablayout = QVBoxLayout()
        centertrackertablayout.addWidget(self.button)


        # maptracker
        maptrackertablayout = QVBoxLayout()
        maptrackertablayout.addWidget(self.button1)




        # unite the tabs
        self.centertrackertab.setLayout(centertrackertablayout)
        self.maptrackertab.setLayout(maptrackertablayout)

        self.tabs.addTab(self.centertrackertab, 'centertracker')
        self.tabs.addTab(self.maptrackertab, 'maptracker')
        trackerlayout = QGridLayout()
        trackerlayout.addWidget(self.tabs)
        self.setLayout(trackerlayout)
