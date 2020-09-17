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
        self.table_widget.tab_experiment.stop_sensor()

        # Save newly created experiment analyses
        for experiment in self.table_widget.tab_analysis.experiment_dict.values():
            experiment.save_pickle()

        # Update config ini with current paths
        config.write_config(save_path=str(self.table_widget.tab_experiment.directory),
                            plot_path=str(self.table_widget.tab_analysis.plot_directory),
                            analysis_path=str(self.table_widget.tab_analysis.analysis_directory),
                            export_path=str(self.table_widget.tab_analysis.export_directory),
                            arduino=str(self.table_widget.tab_experiment.sensor_cb.currentText()),
                            keithley=str(self.table_widget.tab_experiment.source_cb.currentText()))
