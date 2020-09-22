import os
from PyQt5 import QtWidgets, QtGui, QtCore

from hardware import serial_ports
from user_interfaces.widgets.separator import Separator
from user_interfaces.widgets.switch_button import Switch
from utility.config import defaults, paths, ports, write_config


class SensorWidget(QtWidgets.QWidget):
    start_sensor = QtCore.pyqtSignal()
    stop_sensor = QtCore.pyqtSignal()
    to_log = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SensorWidget, self).__init__(parent)

        self.block_sensor = False

        vbox_total = QtWidgets.QVBoxLayout()
        vbox_total.addWidget(QtWidgets.QLabel("Parameters", self))
        grid_pars = QtWidgets.QGridLayout()
        grid_pars.addWidget(QtWidgets.QLabel("Time (s)", self), 0, 0)
        self.sensor_time_edit = QtWidgets.QLineEdit('60', self)
        self.sensor_time_edit.setFixedWidth(80)
        grid_pars.addWidget(self.sensor_time_edit, 0, 1)
        grid_pars.addWidget(QtWidgets.QLabel("# Averages", self), 0, 2)
        self.sensor_avg_edit = QtWidgets.QLineEdit('1', self)
        self.sensor_avg_edit.setFixedWidth(80)
        grid_pars.addWidget(self.sensor_avg_edit, 0, 3)
        vbox_total.addLayout(grid_pars)

        hbox_mode = QtWidgets.QHBoxLayout()
        grid_mode = QtWidgets.QGridLayout()
        cont_plot_label = QtWidgets.QLabel("Continuous Plot", self)
        cont_plot_label.setAlignment(QtCore.Qt.AlignRight)
        grid_mode.addWidget(cont_plot_label, 0, 0)
        self.sensor_plot_fixed_time = Switch()
        self.sensor_plot_fixed_time.setChecked(False)
        self.sensor_plot_fixed_time.toggled.connect(lambda: self.sensor_mode_changed)
        grid_mode.addWidget(self.sensor_plot_fixed_time, 0, 1)
        grid_mode.addWidget(QtWidgets.QLabel("Fixed Time Plot", self), 0, 2)
        hbox_mode.addLayout(grid_mode)
        hbox_mode.addStretch(-1)
        vbox_total.addLayout(hbox_mode)

        hbox_ports = QtWidgets.QHBoxLayout()
        hbox_ports.addWidget(QtWidgets.QLabel("COM Port", self))
        self.sensor_cb = QtWidgets.QComboBox()
        self.sensor_cb.setFixedWidth(90)
        self.sensor_cb.addItem('dummy')
        for port in serial_ports.get_serial_ports():
            self.sensor_cb.addItem(port)
            if port == ports['arduino']:
                self.sensor_cb.setCurrentText(port)
        self.sensor_cb.currentTextChanged.connect(self.sensor_port_changed)
        hbox_ports.addWidget(self.sensor_cb)
        self.refresh_button = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(paths['icons'], 'refresh.png')), '')
        self.refresh_button.clicked.connect(self.update_ports)
        self.refresh_button.setToolTip('Update Ports')
        hbox_ports.addWidget(self.refresh_button)
        hbox_ports.addStretch(-1)
        vbox_total.addLayout(hbox_ports)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Readout", self))
        grid_sensors = QtWidgets.QGridLayout()
        grid_sensors.addWidget(QtWidgets.QLabel("Temperature (C)", self), 0, 0)
        self.temperature_edit = QtWidgets.QLineEdit('25', self)
        self.temperature_edit.setFixedWidth(60)
        self.temperature_edit.setDisabled(True)
        grid_sensors.addWidget(self.temperature_edit, 0, 1)
        grid_sensors.addWidget(QtWidgets.QLabel("Diode 1 (W/m2)", self), 0, 2)
        self.diode1_edit = QtWidgets.QLineEdit('0', self)
        self.diode1_edit.setFixedWidth(60)
        self.diode1_edit.setDisabled(True)
        grid_sensors.addWidget(self.diode1_edit, 0, 3)
        grid_sensors.addWidget(QtWidgets.QLabel("Diode 2 (W/m2)", self), 1, 0)
        self.diode2_edit = QtWidgets.QLineEdit('0', self)
        self.diode2_edit.setFixedWidth(60)
        self.diode2_edit.setDisabled(True)
        grid_sensors.addWidget(self.diode2_edit, 1, 1)
        grid_sensors.addWidget(QtWidgets.QLabel("Diode 3 (W/m2)", self), 1, 2)
        self.diode3_edit = QtWidgets.QLineEdit('0', self)
        self.diode3_edit.setFixedWidth(60)
        self.diode3_edit.setDisabled(True)
        grid_sensors.addWidget(self.diode3_edit, 1, 3)
        vbox_total.addLayout(grid_sensors)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Measure", self))
        hbox_measure = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Plot Sensors")
        self.start_button.setCheckable(True)
        self.start_button.setStyleSheet("QPushButton:checked { background-color: #32cd32 }")
        self.start_button.setToolTip('Plot Sensors')
        hbox_measure.addWidget(self.start_button)
        hbox_measure.addStretch(-1)
        vbox_total.addLayout(hbox_measure)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Arduino", self))
        grid_arduino = QtWidgets.QGridLayout()
        grid_arduino.addWidget(QtWidgets.QLabel("Baud rate", self), 0, 0)
        self.baud_edit = QtWidgets.QLineEdit('38400', self)
        self.baud_edit.setFixedWidth(60)
        self.baud_edit.setDisabled(True)
        grid_arduino.addWidget(self.baud_edit, 0, 1)
        grid_arduino.addWidget(QtWidgets.QLabel("# Data points", self), 0, 2)
        self.datapoints_edit = QtWidgets.QLineEdit('100', self)
        self.datapoints_edit.setFixedWidth(60)
        self.datapoints_edit.setDisabled(True)
        grid_arduino.addWidget(self.datapoints_edit, 0, 3)
        grid_arduino.addWidget(QtWidgets.QLabel("Data bytes", self), 0, 4)
        self.databytes_edit = QtWidgets.QLineEdit('2', self)
        self.databytes_edit.setFixedWidth(60)
        self.databytes_edit.setDisabled(True)
        grid_arduino.addWidget(self.databytes_edit, 0, 5)
        grid_arduino.addWidget(QtWidgets.QLabel("Timeout (s)", self), 1, 0)
        self.timeout_edit = QtWidgets.QLineEdit('30', self)
        self.timeout_edit.setFixedWidth(60)
        self.timeout_edit.setDisabled(True)
        grid_arduino.addWidget(self.timeout_edit, 1, 1)
        grid_arduino.addWidget(QtWidgets.QLabel("Analogue inputs", self), 1, 2)
        self.ais_edit = QtWidgets.QLineEdit('4', self)
        self.ais_edit.setFixedWidth(60)
        self.ais_edit.setDisabled(True)
        grid_arduino.addWidget(self.ais_edit, 1, 3)
        grid_arduino.addWidget(QtWidgets.QLabel("Query period (s)", self), 1, 4)
        self.query_edit = QtWidgets.QLineEdit('0.25', self)
        self.query_edit.setFixedWidth(60)
        self.query_edit.setDisabled(True)
        grid_arduino.addWidget(self.query_edit, 1, 5)
        vbox_total.addLayout(grid_arduino)
        vbox_total.addStretch(-1)
        self.setLayout(vbox_total)

    def sensor_mode_changed(self):
        self.stop_sensor.emit()
        self.start_sensor.emit()

    def sensor_port_changed(self):
        ports['arduino'] = self.sensor_cb.currentText()
        if self.block_sensor is False:  # if combobox update is in progress, sensor_port_changed is not triggered
            self.stop_sensor.emit()
            self.start_sensor.emit()

    def update_ports(self):
        self.stop_sensor.emit()
        self.block_sensor = True
        self.sensor_cb.clear()
        self.sensor_cb.addItem('dummy')
        for port in serial_ports.get_serial_ports():
            self.sensor_cb.addItem(port)
        self.block_sensor = False
        self.start_sensor.emit()

    def check_sensor_parameters(self):
        try:
            float(self.sensor_time_edit.text())
            int(self.sensor_avg_edit.text())
        except (ZeroDivisionError, ValueError):
            self.to_log.emit('<span style=\" color:#ff0000;\" >Some parameters are not in the right format. '
                             'Please check before starting measurement.</span>')
            return False
        if any([float(self.sensor_time_edit.text()) < 1.0,
                int(self.sensor_avg_edit.text()) < 1
                ]):
            self.to_log.emit('<span style=\" color:#ff0000;\" >Some parameters are out of bounds. '
                             'Please check before starting measurement.</span>')
            return False
        return True
