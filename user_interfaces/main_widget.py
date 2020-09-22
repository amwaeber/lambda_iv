import collections
import datetime
import numpy as np
import os
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import time

import hardware.keithley as keithley
import hardware.sensor as sensor
from user_interfaces.cell_tab import CellWidget
from user_interfaces.info_tab import InfoWidget
from user_interfaces.plots import PlotsWidget
from user_interfaces.sensor_tab import SensorWidget
from utility.config import defaults
from utility.fitting import fit_iv

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class MainWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.info_data = defaults['info']  # update as references to info_tab
        self.exp_count = 0

        self.ns = collections.deque(maxlen=25)
        self.isc = collections.deque(maxlen=25)
        self.voc = collections.deque(maxlen=25)
        self.pmax = collections.deque(maxlen=25)

        hbox_total = QtWidgets.QHBoxLayout()

        self.plot_widget = PlotsWidget()
        hbox_total.addWidget(self.plot_widget, 6)

        vbox_right = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabs.setTabPosition(QtWidgets.QTabWidget.South)

        self.cell_tab = CellWidget(self)
        self.cell_tab.clipboard_button.clicked.connect(self.clipboard)
        self.cell_tab.start_button.clicked.connect(self.start)
        self.cell_tab.to_log.connect(self.logger)
        self.tabs.addTab(self.cell_tab, 'PV Cell')

        self.sensor_tab = SensorWidget(self)
        self.sensor_tab.start_sensor.connect(self.start_sensor)
        self.sensor_tab.stop_sensor.connect(self.stop_sensor)
        self.sensor_tab.start_button.clicked.connect(self.plot_sensors)
        self.sensor_tab.to_log.connect(self.logger)
        self.tabs.addTab(self.sensor_tab, 'Sensors')

        self.info_tab = InfoWidget(self)
        self.tabs.addTab(self.info_tab, 'Info')

        vbox_right.addWidget(self.tabs, 4)

        self.log_group_box = QtWidgets.QGroupBox('Log')
        grid_log = QtWidgets.QGridLayout()
        self.log_edit = QtWidgets.QTextEdit("Ready to measure...\n", self)
        grid_log.addWidget(self.log_edit, 0, 0)
        self.log_group_box.setLayout(grid_log)
        vbox_right.addWidget(self.log_group_box, 2)
        hbox_total.addLayout(vbox_right, 3)
        self.setLayout(hbox_total)

        self.sensor_time_data = None
        self.sensor_time_data_averaged = None
        self.sensor_time_max = None
        self.sensor_avg = None

        self.sensor_mes = None
        self.start_sensor()

        self.iv_mes = keithley.Keithley(gpib_port='dummy')
        self.iv_register(self.iv_mes)

    def sensor_register(self, mes):
        self.sensor_mes = mes
        self.sensor_mes.update.connect(self.update_sensor)
        self.sensor_mes.to_log.connect(self.logger)

    @QtCore.pyqtSlot()
    def update_sensor(self):
        if not self.sensor_mes:
            return
        time_val, [d1val, d2val, tval, d3val] = self.sensor_mes.get_sensor_latest()
        self.sensor_tab.temperature_edit.setText("%.2f" % tval)
        self.sensor_tab.diode1_edit.setText("%.1f" % d1val)
        self.sensor_tab.diode2_edit.setText("%.1f" % d2val)
        self.sensor_tab.diode3_edit.setText("%.1f" % d3val)
        if not(self.sensor_tab.sensor_plot_fixed_time.isChecked()) and not self.sensor_mes.port == 'dummy':
            if self.sensor_tab.start_button.isChecked():
                self.sensor_mes.line_plot(self.plot_widget.temp_data_line, channel='temp')
                self.sensor_mes.line_plot(self.plot_widget.power_data_line1, channel='power1')
                self.sensor_mes.line_plot(self.plot_widget.power_data_line2, channel='power2')
                self.sensor_mes.line_plot(self.plot_widget.power_data_line3, channel='power3')
        elif all([self.sensor_tab.sensor_plot_fixed_time.isChecked(),
                  self.sensor_tab.start_button.isChecked(),
                  not self.sensor_mes.port == 'dummy']):
            if self.sensor_time_data is None:
                self.sensor_time_data = [[time_val], [tval], [d1val], [d2val], [d3val]]
                self.sensor_time_data_averaged = [[], [], [], [], []]
                if self.sensor_tab.check_sensor_parameters() is False:
                    self.sensor_tab.start_button.setChecked(False)
                    return
                self.sensor_time_max = float(self.sensor_tab.sensor_time_edit.text())
                self.sensor_avg = 1  # TODO: remove averaging
            elif (time_val - self.sensor_time_data[0][0]) > self.sensor_time_max:
                self.sensor_tab.start_button.setChecked(False)
                return
            else:
                latest_data = [time_val, tval, d1val, d2val, d3val]
                for i, _ in enumerate(self.sensor_time_data):
                    self.sensor_time_data[i].append(latest_data[i])
                if len(self.sensor_time_data[0]) % self.sensor_avg == 0:
                    for i, _ in enumerate(self.sensor_time_data):
                        self.sensor_time_data_averaged[i] = \
                            [sum(values, 0.0) / self.sensor_avg
                             for values in zip(*[iter(self.sensor_time_data[i])] * self.sensor_avg)]
                    self.sensor_time_data_averaged[0] = [i - self.sensor_time_data_averaged[0][0]
                                                         for i in self.sensor_time_data_averaged[0]]
            if self.sensor_tab.start_button.isChecked():
                self.plot_widget.temp_data_line.setData(self.sensor_time_data_averaged[0],
                                                        self.sensor_time_data_averaged[1])
                self.plot_widget.power_data_line1.setData(self.sensor_time_data_averaged[0],
                                                          self.sensor_time_data_averaged[2])
                self.plot_widget.power_data_line2.setData(self.sensor_time_data_averaged[0],
                                                          self.sensor_time_data_averaged[3])
                self.plot_widget.power_data_line3.setData(self.sensor_time_data_averaged[0],
                                                          self.sensor_time_data_averaged[4])

    @QtCore.pyqtSlot()
    def start_sensor(self):
        if self.sensor_mes:
            self.sensor_mes.stop()
        self.sensor_mes = sensor.ArduinoSensor(str(self.sensor_tab.sensor_cb.currentText()), *defaults['arduino'])
        self.sensor_register(self.sensor_mes)
        self.sensor_mes.start()

    @QtCore.pyqtSlot()
    def stop_sensor(self):
        self.sensor_tab.start_button.setChecked(False)
        if self.sensor_mes:
            self.sensor_mes.stop()
            self.sensor_mes = None

    def plot_sensors(self):
        # reset stored sensor data
        self.sensor_time_data = None
        self.sensor_time_data_averaged = None
        # Do not start fixed time measurement if iv-scan is running
        if self.sensor_tab.sensor_plot_fixed_time.isChecked() and self.cell_tab.start_button.isChecked():
            self.logger('<span style=\" color:#ff0000;\" >I-V scan is running. '
                        'Stop current experiment before starting fixed time sensor scan.</span>')
            self.sensor_tab.start_button.setChecked(False)
            return
        if self.sensor_tab.start_button.isChecked():
            self.sensor_tab.start_button.setText("Stop Plot")
        else:
            self.sensor_tab.start_button.setText("Plot Sensors")
        self.plot_widget.temp_data_line.setData([], [])
        self.plot_widget.power_data_line1.setData([], [])
        self.plot_widget.power_data_line2.setData([], [])
        self.plot_widget.power_data_line3.setData([], [])

    def update_sens_views(self):
        self.sensor_p2.setGeometry(self.sensor_p1.vb.sceneBoundingRect())
        self.sensor_p2.linkedViewChanged(self.sensor_p1.vb, self.sensor_p2.XAxis)

    def iv_register(self, mes):
        self.iv_mes = mes
        self.iv_mes.trace_finished.connect(self.trace_finished)
        self.iv_mes.restart_sensor.connect(self.start_sensor)
        self.iv_mes.to_log.connect(self.logger)
        self.iv_mes.experiment_finished.connect(self.experiment_loop)

    def start(self):
        # Stop measurement if measurement is running
        if not self.cell_tab.start_button.isChecked():
            self.stop()
            return
        # Do not start measurement if sensor plot with fixed time is active
        elif self.sensor_tab.start_button.isChecked() \
                and self.sensor_tab.sensor_plot_fixed_time.isChecked():
            self.logger('<span style=\" color:#ff0000;\" >Fixed time sensor scan is running. '
                        'Stop current sensor experiment first.</span>')
            self.cell_tab.start_button.setChecked(False)
            return
        # Do not start measurement if faulty parameters are set
        elif self.cell_tab.check_iv_parameters() is False:
            self.cell_tab.start_button.setChecked(False)
            return
        self.cell_tab.start_button.setText("Stop IV")
        self.info_tab.save_defaults()
        if self.iv_mes:
            self.iv_mes.close()
        experiment_delay = 1 if self.exp_count == 0 else float(self.cell_tab.exp_delay_edit.text()) * 60
        self.iv_mes = keithley.Keithley(gpib_port=str(self.cell_tab.source_cb.currentText()),
                                        n_data_points=int(self.cell_tab.nstep_edit.text()),
                                        repetitions=int(self.cell_tab.reps_edit.text()),
                                        repetition_delay=float(self.cell_tab.rep_delay_edit.text()),
                                        delay=float(self.cell_tab.delay_edit.text()),
                                        experiment_delay=experiment_delay,
                                        min_voltage=float(self.cell_tab.start_edit.text()),
                                        max_voltage=float(self.cell_tab.end_edit.text()),
                                        compliance_current=float(self.cell_tab.ilimit_edit.text()),
                                        voltage_protection=int(self.cell_tab.vprot_edit.text()),
                                        remote_sense=self.cell_tab.remote_sense_btn.isChecked(),
                                        use_rear_terminals=self.cell_tab.rear_terminal_btn.isChecked()
                                        )
        self.iv_register(self.iv_mes)
        self.check_save_path()
        if self.exp_count == 0 and int(self.cell_tab.exps_edit.text()) > 1:  # count file names from ' 0' if multiple
            os.rmdir(self.cell_tab.save_dir)
            self.cell_tab.save_dir += ' 0'
            defaults['info'][0] += ' 0'
            self.cell_tab.folder_edit.setText(self.cell_tab.save_dir)
            if not os.path.exists(self.cell_tab.save_dir):
                os.makedirs(self.cell_tab.save_dir)
        self.iv_mes.read_keithley_start()
        self.exp_count += 1

    @QtCore.pyqtSlot(int)
    def trace_finished(self, itrace):
        if not self.iv_mes:
            return
        _, sensor_latest = self.sensor_mes.get_sensor_latest()
        timestamp = time.time()
        self.iv_mes.line_plot(self.plot_widget.iv_data_line)
        data_iv = self.iv_mes.get_keithley_data()
        fit_data_iv = fit_iv(data_iv)
        self.cell_tab.update_readout(fit_data_iv)
        self.update_plots(itrace, fit_data_iv)

        save_file = open(os.path.join(self.cell_tab.save_dir, 'IV_Curve_%s.csv' % str(itrace)), "a+")
        save_file.write(self.save_string(timestamp,
                                         *sensor_latest,
                                         *defaults['info'],
                                         *defaults['cell'],
                                         *fit_data_iv))
        data_iv.to_csv(save_file)
        save_file.close()

        if itrace == (self.iv_mes.traces - 1):  # TODO: capture experiment repeats
            self.cell_tab.start_button.setChecked(False)
            self.cell_tab.start_button.setText("Start IV")

    def update_plots(self, itrace, fit_data):
        isc, _, voc, _, pmax = fit_data
        self.ns.append(itrace)
        self.isc.append(isc)
        self.voc.append(voc)
        self.pmax.append(pmax)
        self.plot_widget.isc_data_line.setData(self.ns, self.isc)
        self.plot_widget.voc_data_line.setData(self.ns, self.voc)
        self.plot_widget.pmax_data_line.setData(self.ns, self.pmax)

    @staticmethod
    def save_string(*args):
        pars = ['timestamp', 'irradiance_1', 'irradiance_2', 'sample_temperature', 'irradiance_3',
                'experiment_name', 'experiment_date', 'film_id', 'pv_cell_id', 'setup_location',
                'setup_calibrated', 'setup_suns', 'pid_proportional_band', 'pid_integral',
                'pid_derivative', 'pid_fuzzy_overshoot', 'pid_heat_tcr1', 'pid_cool_tcr2',
                'pid_setpoint', 'room_temperature', 'room_humidity', 'source_start_voltage',
                'source_end_voltage', 'source_voltage_step', 'source_n_steps',
                'source_compliance', 'source_voltage_limit', 'source_trigger_delay',
                'source_n_traces', 'source_trace_delay', 'source_n_experiments',
                'source_experiment_delay', 'source_remote_sense', 'source_rear_terminal',
                'isc', 'disc', 'voc', 'dvoc', 'pmax']
        return "\n".join([f"# {par}, {arg}" for par, arg in zip(pars, args)]) + "\n"

    def stop(self):
        if self.iv_mes:
            self.iv_mes.close()
        self.cell_tab.start_button.setChecked(False)
        self.cell_tab.start_button.setText("Start IV")

    @QtCore.pyqtSlot()
    def experiment_loop(self):
        if self.exp_count < int(self.cell_tab.exps_edit.text()):
            self.cell_tab.save_dir = self.cell_tab.save_dir[:-(len(str(self.exp_count - 1)) + 1)]
            self.cell_tab.save_dir += ' %d' % self.exp_count
            self.cell_tab.folder_edit.setText(self.cell_tab.save_dir)
            defaults['info'][0] = defaults['info'][0][:-(len(str(self.exp_count - 1)) + 1)]
            defaults['info'][0] += ' %d' % self.exp_count
            if not os.path.exists(self.cell_tab.save_dir):
                os.makedirs(self.cell_tab.save_dir)
            self.start_button.click()
            self.logger('<span style=\" color:#ff0000;\" >Next Experiment lined up in %s minutes.</span>' %
                        str(self.exp_delay_edit.text()))
        else:
            self.exp_count = 0

    @QtCore.pyqtSlot()
    def clipboard(self):
        pixmap = QtWidgets.QWidget.grab(self.plot_widget)
        QtWidgets.QApplication.clipboard().setPixmap(pixmap)

    def check_save_path(self):
        if any([not os.path.exists(self.cell_tab.save_dir),
                os.path.exists(os.path.join(self.cell_tab.save_dir, 'IV_Curve_0.csv'))]):
            self.cell_tab.folder_dialog()
            self.check_save_path()

    @QtCore.pyqtSlot(str)
    def logger(self, string):
        timestring = '[' + datetime.datetime.now().strftime('%H:%M:%S') + '] '
        self.log_edit.append(timestring + string)
        self.log_edit.moveCursor(QtGui.QTextCursor.End)
