"""
main and module explorer
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
        import minion.minion_trace as trace

        self.confocalwidget = confocal.MinionConfocalUi()

        self.setCentralWidget(self.confocalwidget)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # -------------------------------------------------------------------------------------------------------------
        self.moduleexplorerwidget = MinionModuleexplorerUi()
        self.moduleexplorerwidget.confocalchange.connect(self.confocalchange)
        self.moduleexplorerwidget.tracechange.connect(self.tracechange)
        self.moduleexplorerdockWidget = QDockWidget(self)
        self.moduleexplorerdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.moduleexplorerdockWidget.setWindowTitle('module explorer')
        self.moduleexplorerdockWidget.setWidget(self.moduleexplorerwidget)
        self.moduleexplorerdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.moduleexplorerdockWidget)

        self.tracewidget = trace.MinionTraceUi()
        self.tracewidgetdockWidget = QDockWidget(self)
        self.tracewidgetdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.tracewidgetdockWidget.setWindowTitle('trace')
        self.tracewidgetdockWidget.setWidget(self.tracewidget)
        self.tracewidgetdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.RightDockWidgetArea, self.tracewidgetdockWidget)

        # -------------------------------------------------------------------------------------------------------------
        self.setWindowTitle("minion")
        self.setWindowIcon(QIcon('media/minions_icon.png'))
        self.showMaximized()
        self.move(0, 0)
        self.show()
        print('show modules')

    @pyqtSlot()
    def confocalchange(self):
        if self.confocalwidget.isVisible():
            self.confocalwidget.hide()
        else:
            self.confocalwidget.show()

    @pyqtSlot()
    def tracechange(self):
        if self.tracewidget.isVisible():
            self.tracewidget.hide()
        else:
            self.tracewidget.show()



class MinionModuleexplorerUi(QWidget):
    confocalchange = pyqtSignal()
    tracechange = pyqtSignal()

    def __init__(self, parent=None):
        super(MinionModuleexplorerUi, self).__init__(parent)
        # self.setWindowTitle('modules')
        # create buttons and connect them to functions
        self.open_confocal = QPushButton('confocal')
        self.open_confocal.clicked.connect(self.confocalclicked)
        self.open_tracker = QPushButton('tracker')
        self.open_trace = QPushButton('trace')
        self.open_trace.clicked.connect(self.traceclicked)
        self.open_odmr = QPushButton('odmr')
        self.open_pulsepattern = QPushButton('pulsepattern')
        self.open_pulsed = QPushButton('pulsed')
        self.open_nuclearops = QPushButton('nuclearops')
        self.open_3dscan = QPushButton('3d-scan')
        self.open_magnet = QPushButton('magnet')
        self.open_gated_counter = QPushButton('gated_counter')

        # add buttons to layout

        moduleexplorer_layout = QGridLayout()
        moduleexplorer_layout.addWidget(self.open_confocal, 0, 0)
        moduleexplorer_layout.addWidget(self.open_tracker, 7, 0)
        moduleexplorer_layout.addWidget(self.open_trace, 1, 0)
        moduleexplorer_layout.addWidget(self.open_odmr, 3, 0)
        moduleexplorer_layout.addWidget(self.open_pulsepattern, 4, 0)
        moduleexplorer_layout.addWidget(self.open_pulsed, 5, 0)
        moduleexplorer_layout.addWidget(self.open_nuclearops, 6, 0)
        moduleexplorer_layout.addWidget(self.open_3dscan, 2, 0)
        moduleexplorer_layout.addWidget(self.open_magnet, 8, 0)
        moduleexplorer_layout.addWidget(self.open_gated_counter, 9, 0)
        moduleexplorer_layout.setSpacing(1)
        self.setLayout(moduleexplorer_layout)
        self.setFixedSize(160, 250)

    def confocalclicked(self):
        self.confocalchange.emit()

    def traceclicked(self):
        self.tracechange.emit()


def build_minion_main_window():
    app = QApplication(sys.argv)
    app.setStyle('plastique')
    print('\tbuilding MinionMainWindow')
    QThread.currentThread().setObjectName('mainThread')
    minion_main = MinionMainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    build_minion_main_window()
