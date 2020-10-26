import datetime
from PyQt5 import QtWidgets
from user_interfaces.widgets.separator import Separator
from utility.config import defaults, write_config


class InfoWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(InfoWidget, self).__init__(parent)

        vbox_total = QtWidgets.QVBoxLayout()
        vbox_total.addWidget(QtWidgets.QLabel("Experiment", self))
        grid_experiment = QtWidgets.QGridLayout()
        grid_experiment.addWidget(QtWidgets.QLabel('Name', self), 0, 0)
        self.experiment_name_edit = QtWidgets.QLineEdit('%s' % defaults['info'][0], self)
        self.experiment_name_edit.setFixedWidth(80)
        grid_experiment.addWidget(self.experiment_name_edit, 0, 1)
        grid_experiment.addWidget(QtWidgets.QLabel('Date', self), 0, 2)
        self.experiment_date_edit = QtWidgets.QLineEdit('%s' % datetime.date.today(), self)
        self.experiment_date_edit.setFixedWidth(80)
        grid_experiment.addWidget(self.experiment_date_edit, 0, 3)
        vbox_total.addLayout(grid_experiment)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Sample", self))
        grid_sample = QtWidgets.QGridLayout()
        grid_sample.addWidget(QtWidgets.QLabel('Film ID', self), 0, 0)
        self.film_id_edit = QtWidgets.QLineEdit('%s' % defaults['info'][2], self)
        self.film_id_edit.setFixedWidth(80)
        grid_sample.addWidget(self.film_id_edit, 0, 1)
        grid_sample.addWidget(QtWidgets.QLabel('PV Cell ID', self), 0, 2)
        self.pv_cell_id_edit = QtWidgets.QLineEdit('%s' % defaults['info'][3], self)
        self.pv_cell_id_edit.setFixedWidth(80)
        grid_sample.addWidget(self.pv_cell_id_edit, 0, 3)
        grid_sample.addWidget(QtWidgets.QLabel('Ref. Cell Temperature', self), 1, 0)
        self.ref_temp_edit = QtWidgets.QLineEdit('%s' % defaults['info'][4], self)
        self.ref_temp_edit.setFixedWidth(80)
        grid_sample.addWidget(self.ref_temp_edit, 1, 1)
        vbox_total.addLayout(grid_sample)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Setup", self))
        grid_setup = QtWidgets.QGridLayout()
        grid_setup.addWidget(QtWidgets.QLabel('Setup Location', self), 0, 0)
        self.setup_location_edit = QtWidgets.QLineEdit('%s' % defaults['info'][5], self)
        self.setup_location_edit.setFixedWidth(80)
        grid_setup.addWidget(self.setup_location_edit, 0, 1)
        grid_setup.addWidget(QtWidgets.QLabel('Calibration Date', self), 0, 2)
        self.setup_calibrated_edit = QtWidgets.QLineEdit('%s' % defaults['info'][6], self)
        self.setup_calibrated_edit.setFixedWidth(80)
        grid_setup.addWidget(self.setup_calibrated_edit, 0, 3)
        grid_setup.addWidget(QtWidgets.QLabel('Calibration (suns)', self), 1, 0)
        self.setup_suns_edit = QtWidgets.QLineEdit('%s' % defaults['info'][7], self)
        self.setup_suns_edit.setFixedWidth(80)
        grid_setup.addWidget(self.setup_suns_edit, 1, 1)
        vbox_total.addLayout(grid_setup)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("PID Controller", self))
        grid_pid = QtWidgets.QGridLayout()
        grid_pid.addWidget(QtWidgets.QLabel('Proportional band (%)', self), 0, 0)
        self.pid_prob_band_edit = QtWidgets.QLineEdit('%s' % defaults['info'][8], self)
        self.pid_prob_band_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_prob_band_edit, 0, 1)
        grid_pid.addWidget(QtWidgets.QLabel('Integral time', self), 0, 2)
        self.pid_integral_edit = QtWidgets.QLineEdit('%s' % defaults['info'][9], self)
        self.pid_integral_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_integral_edit, 0, 3)
        grid_pid.addWidget(QtWidgets.QLabel('Derivative time', self), 1, 0)
        self.pid_derivative_edit = QtWidgets.QLineEdit('%s' % defaults['info'][10], self)
        self.pid_derivative_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_derivative_edit, 1, 1)
        grid_pid.addWidget(QtWidgets.QLabel('Fuzzy Overshoot', self), 1, 2)
        self.pid_fuoc_edit = QtWidgets.QLineEdit('%s' % defaults['info'][11], self)
        self.pid_fuoc_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_fuoc_edit, 1, 3)
        grid_pid.addWidget(QtWidgets.QLabel('Heat Cycle TCR1', self), 2, 0)
        self.pid_tcr1_edit = QtWidgets.QLineEdit('%s' % defaults['info'][12], self)
        self.pid_tcr1_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_tcr1_edit, 2, 1)
        grid_pid.addWidget(QtWidgets.QLabel('Cool Cycle TCR2', self), 2, 2)
        self.pid_tcr2_edit = QtWidgets.QLineEdit('%s' % defaults['info'][13], self)
        self.pid_tcr2_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_tcr2_edit, 2, 3)
        grid_pid.addWidget(QtWidgets.QLabel('Setpoint (C)', self), 3, 0)
        self.pid_setpoint_edit = QtWidgets.QLineEdit('%s' % defaults['info'][14], self)
        self.pid_setpoint_edit.setFixedWidth(80)
        grid_pid.addWidget(self.pid_setpoint_edit, 3, 1)
        vbox_total.addLayout(grid_pid)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Environment", self))
        grid_environment = QtWidgets.QGridLayout()
        grid_environment.addWidget(QtWidgets.QLabel('Room Temperature (C)', self), 0, 0)
        self.room_temperature_edit = QtWidgets.QLineEdit('%s' % defaults['info'][15], self)
        self.room_temperature_edit.setFixedWidth(80)
        grid_environment.addWidget(self.room_temperature_edit, 0, 1)
        grid_environment.addWidget(QtWidgets.QLabel('Room Humidity', self), 0, 2)
        self.room_humidity_edit = QtWidgets.QLineEdit('%s' % defaults['info'][16], self)
        self.room_humidity_edit.setFixedWidth(80)
        grid_environment.addWidget(self.room_humidity_edit, 0, 3)
        vbox_total.addLayout(grid_environment)
        vbox_total.addStretch(-1)
        self.setLayout(vbox_total)

    def save_defaults(self):
        defaults['info'] = [self.experiment_name_edit.text(), self.experiment_date_edit.text(),
                            self.film_id_edit.text(), self.pv_cell_id_edit.text(), self.ref_temp_edit.text(),
                            self.setup_location_edit.text(), self.setup_calibrated_edit.text(),
                            self.setup_suns_edit.text(), self.pid_prob_band_edit.text(),
                            self.pid_integral_edit.text(), self.pid_derivative_edit.text(),
                            self.pid_fuoc_edit.text(), self.pid_tcr1_edit.text(),
                            self.pid_tcr2_edit.text(), self.pid_setpoint_edit.text(),
                            self.room_temperature_edit.text(), self.room_humidity_edit.text()]
        write_config()
