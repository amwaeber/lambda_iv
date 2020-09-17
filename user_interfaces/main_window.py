import ctypes
import os
from PyQt5 import QtWidgets, QtGui

from user_interfaces.main_widget import MainWidget
from utility import config
from utility.version import __version__


# noinspection PyAttributeOutsideInit
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        myappid = 'Lambda IV'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        config.read_config()
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QtGui.QIcon(os.path.join(config.paths['icons'], 'lambda_iv.png')))
        self.setWindowTitle("%s %s" % (config.global_confs['progname'], __version__))

        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)
        self.showMaximized()

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)

        # Disconnect sensor before shutdown
        self.main_widget.stop_sensor()

        # Update config ini with current paths
        config.write_config(save_path=str(self.main_widget.directory),
                            arduino=str(self.main_widget.sensor_cb.currentText()),
                            keithley=str(self.main_widget.source_cb.currentText()))
