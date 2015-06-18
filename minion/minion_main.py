"""
main
"""
print('executing minion.minion_main')

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import time

class MinionMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MinionMainWindow, self).__init__(parent)
        import minion.minion_confocal as confocal
        self.confocalwidget = confocal.MinionConfocalUi()

        self.setCentralWidget(self.confocalwidget)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        import minion.minion_trace as trace
        modulelist = [MinionModuleexplorerUi, trace.MinionTraceUi]
        titlelist = ['module explorer', 'module explorer']
        numbermodules = len(modulelist)
        startposition = [Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea]
        self.addmodule(modulelist, titlelist, startposition, numbermodules)

        self.setWindowTitle("minion")
        self.setWindowIcon(QIcon('media/minions_icon.png'))
        self.showMaximized()
        self.move(0, 0)
        self.show()
        print('show modules')

    def addmodule(self, windowcontent, titlelist, startposition, numbermodules):
        self.dockWidget = [None]*2
        self.dockWidgetContents = [None]*2
        for i in range(numbermodules):
            self.dockWidget[i] = QDockWidget(self)
            self.dockWidget[i].setFeatures(QDockWidget.AllDockWidgetFeatures)
            self.dockWidget[i].setWindowTitle(titlelist[i])
            self.dockWidgetContents[i] = windowcontent[i]()
            self.dockWidget[i].setWidget(self.dockWidgetContents[i])
            self.dockWidget[i].setAttribute(Qt.WA_DeleteOnClose)
            self.addDockWidget(startposition[i], self.dockWidget[i])
            time.sleep(0.2)


class MinionModuleexplorerUi(QWidget):
    def __init__(self, parent=None):
        super(MinionModuleexplorerUi, self).__init__(parent)
        # self.setWindowTitle('modules')
        # create buttons and connect them to functions
        self.open_confocal = QPushButton('confocal')
        self.open_tracker = QPushButton('tracker')
        self.open_trace = QPushButton('trace')
        self.open_odmr = QPushButton('odmr')
        self.open_pulsepattern = QPushButton('pulsepattern')
        self.open_pulsed = QPushButton('pulsed')
        self.open_nuclearops = QPushButton('nuclearops')
        self.open_vfg = QPushButton('vfg')
        self.open_magnet = QPushButton('magnet')
        self.open_gated_counter = QPushButton('gated_counter')

        # add buttons to layout

        moduleexplorer_layout = QGridLayout()
        moduleexplorer_layout.addWidget(self.open_confocal, 0, 0)
        moduleexplorer_layout.addWidget(self.open_tracker, 1, 0)
        moduleexplorer_layout.addWidget(self.open_trace, 2, 0)
        moduleexplorer_layout.addWidget(self.open_odmr, 3, 0)
        moduleexplorer_layout.addWidget(self.open_pulsepattern, 4, 0)
        moduleexplorer_layout.addWidget(self.open_pulsed, 5, 0)
        moduleexplorer_layout.addWidget(self.open_nuclearops, 6, 0)
        moduleexplorer_layout.addWidget(self.open_vfg, 7, 0)
        moduleexplorer_layout.addWidget(self.open_magnet, 8, 0)
        moduleexplorer_layout.addWidget(self.open_gated_counter, 9, 0)
        moduleexplorer_layout.setSpacing(1)
        self.setLayout(moduleexplorer_layout)
        self.setFixedSize(160, 250)

def build_minion_main_window():
    app = QApplication(sys.argv)
    app.setStyle('plastique')
    print('\tbuilding MinionMainWindow')
    QThread.currentThread().setObjectName('mainThread')
    minion_main = MinionMainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    build_minion_main_window()
