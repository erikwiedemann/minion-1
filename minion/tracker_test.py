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
        self.centertrackertab = QTabWidget()
        self.maptrackertab = QTabWidget()



        trackerlayout = QGridLayout()
        trackerlayout.addWidget(self.centertrackertab)
        trackerlayout.addWidget(self.maptrackertab)
