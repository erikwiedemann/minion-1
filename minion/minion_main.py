"""
main and module explorer
"""
print('executing minion.minion_main')

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import time
import serial

class MinionMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MinionMainWindow, self).__init__(parent)
        import minion.minion_confocal as confocal
        import minion.minion_trace as trace
        import minion.minion_3dscan as volumescan
        import minion.minion_tracker as tracker
        import minion.minion_cwodmr as cwodmr
        import minion.minion_counter as fpga_control

        # self.fpga = fpga_control.MinionCounter()
        self.counter = []#self.fpga.counter
        # hardware initialization etc
        from minion.minion_hardware_check import CheckHardware
        self.hardware_counter, self.hardware_laser, self.laser, self.hardware_stage, self.stage, self.stagelib = [],[],[],[],[],[]#CheckHardware.check(CheckHardware)
        # -------------------------------------------------------------------------------------------------------------
        self.confocalwidget = confocal.MinionConfocalUi(self)

        self.setCentralWidget(self.confocalwidget)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # -------------------------------------------------------------------------------------------------------------
        self.moduleexplorerwidget = MinionModuleexplorerUi()

        # click events
        self.moduleexplorerwidget.confocalchange.connect(self.confocalchange)
        self.moduleexplorerwidget.tracechange.connect(self.tracechange)
        self.moduleexplorerwidget.volumescanchange.connect(self.volumescanchange)
        self.moduleexplorerwidget.trackerchange.connect(self.trackerchange)
        self.moduleexplorerwidget.cwodmrchange.connect(self.cwodmrchange)

        # initialize module UIs
        self.moduleexplorerdockWidget = QDockWidget(self)
        self.moduleexplorerdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.moduleexplorerdockWidget.setWindowTitle('module explorer')
        self.moduleexplorerdockWidget.setWidget(self.moduleexplorerwidget)
        self.moduleexplorerdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.moduleexplorerdockWidget)

        self.tracewidget = trace.MinionTraceUi(self)
        self.tracewidgetdockWidget = QDockWidget(self)
        self.tracewidgetdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.tracewidgetdockWidget.setWindowTitle('trace')
        self.tracewidgetdockWidget.setWidget(self.tracewidget)
        self.tracewidgetdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.RightDockWidgetArea, self.tracewidgetdockWidget)
        self.tracewidgetdockWidget.hide()

        self.volumescanwidget = volumescan.Minion3dscanUI(self)
        self.volumescanwidgetdockWidget = QDockWidget(self)
        self.volumescanwidgetdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.volumescanwidgetdockWidget.setWindowTitle('3d scan')
        self.volumescanwidgetdockWidget.setWidget(self.volumescanwidget)
        self.volumescanwidgetdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.RightDockWidgetArea, self.volumescanwidgetdockWidget)
        self.volumescanwidgetdockWidget.hide()

        self.trackerwidget = tracker.MinionTrackerUI(self)
        self.trackerwidgetdockWidget = QDockWidget(self)
        self.trackerwidgetdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.trackerwidgetdockWidget.setWindowTitle('tracker')
        self.trackerwidgetdockWidget.setWidget(self.trackerwidget)
        self.trackerwidgetdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.RightDockWidgetArea, self.trackerwidgetdockWidget)
        self.trackerwidgetdockWidget.hide()

        self.cwodmrwidget = cwodmr.MinionCwodmrUI(self)
        self.cwodmrwidgetdockWidget = QDockWidget(self)
        self.cwodmrwidgetdockWidget.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.cwodmrwidgetdockWidget.setWindowTitle('cwodmr')
        self.cwodmrwidgetdockWidget.setWidget(self.cwodmrwidget)
        self.cwodmrwidgetdockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.addDockWidget(Qt.RightDockWidgetArea, self.cwodmrwidgetdockWidget)
        self.cwodmrwidgetdockWidget.hide()

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
        if self.tracewidgetdockWidget.isVisible():
            self.tracewidgetdockWidget.hide()
        else:
            self.tracewidgetdockWidget.show()

    @pyqtSlot()
    def volumescanchange(self):
        if self.volumescanwidgetdockWidget.isVisible():
            self.volumescanwidgetdockWidget.hide()
        else:
            self.volumescanwidgetdockWidget.show()

    @pyqtSlot()
    def trackerchange(self):
        if self.trackerwidgetdockWidget.isVisible():
            self.trackerwidgetdockWidget.hide()
        else:
            self.trackerwidgetdockWidget.show()

    @pyqtSlot()
    def cwodmrchange(self):
        if self.cwodmrwidgetdockWidget.isVisible():
            self.cwodmrwidgetdockWidget.hide()
        else:
            self.cwodmrwidgetdockWidget.show()



class MinionModuleexplorerUi(QWidget):
    confocalchange = pyqtSignal()
    tracechange = pyqtSignal()
    volumescanchange = pyqtSignal()
    trackerchange = pyqtSignal()
    cwodmrchange = pyqtSignal()

    def __init__(self, parent=None):
        super(MinionModuleexplorerUi, self).__init__(parent)
        # self.setWindowTitle('modules')
        # create buttons and connect them to functions

        self.open_confocal = QPushButton('confocal')
        self.open_confocal.clicked.connect(self.confocalclicked)

        self.open_tracker = QPushButton('tracker')
        self.open_tracker.clicked.connect(self.trackerclicked)

        self.open_trace = QPushButton('trace')
        self.open_trace.clicked.connect(self.traceclicked)

        self.open_cwodmr = QPushButton('cwodmr')
        self.open_cwodmr.clicked.connect(self.cwodmrclicked)

        self.open_pulsepattern = QPushButton('pulsepattern')

        self.open_pulsed = QPushButton('pulsed')

        self.open_nuclearops = QPushButton('nuclearops')

        self.open_3dscan = QPushButton('3d-scan')
        self.open_3dscan.clicked.connect(self.volumescanclicked)

        self.open_magnet = QPushButton('magnet')

        self.open_gated_counter = QPushButton('gated_counter')

        # add buttons to layout

        moduleexplorer_layout = QVBoxLayout()
        moduleexplorer_layout.addWidget(self.open_confocal)
        moduleexplorer_layout.addWidget(self.open_trace)
        moduleexplorer_layout.addWidget(self.open_3dscan)
        moduleexplorer_layout.addWidget(self.open_tracker)
        moduleexplorer_layout.addWidget(self.open_cwodmr)
        moduleexplorer_layout.addWidget(self.open_pulsepattern)
        moduleexplorer_layout.addWidget(self.open_pulsed)
        moduleexplorer_layout.addWidget(self.open_nuclearops)
        moduleexplorer_layout.addWidget(self.open_magnet)
        moduleexplorer_layout.addWidget(self.open_gated_counter)
        moduleexplorer_layout.setSpacing(1)
        self.setLayout(moduleexplorer_layout)
        self.setFixedSize(160, 250)

    def confocalclicked(self):
        self.confocalchange.emit()

    def traceclicked(self):
        self.tracechange.emit()

    def volumescanclicked(self):
        self.volumescanchange.emit()

    def trackerclicked(self):
        self.trackerchange.emit()

    def cwodmrclicked(self):
        self.cwodmrchange.emit()


def build_minion_main_window():
    app = QApplication(sys.argv)
    app.setStyle('plastique')
    print('\tbuilding MinionMainWindow')
    QThread.currentThread().setObjectName('mainThread')
    minion_main = MinionMainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    build_minion_main_window()
