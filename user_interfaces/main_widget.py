import datetime
import numpy as np
import os
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg

import hardware.keithley as keithley
import hardware.sensor as sensor
from user_interfaces.cell_tab import CellWidget
from user_interfaces.info_tab import InfoWidget
from user_interfaces.sensor_tab import SensorWidget
import utility.colors as colors
from utility.config import defaults

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class MainWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.data_iv = np.zeros((5, 1))
        self.info_data = defaults['info']  # update as references to info_tab
        self.exp_count = 0

        vbox_total = QtWidgets.QVBoxLayout()
        hbox_top = QtWidgets.QHBoxLayout()
        self.iv_group_box = QtWidgets.QGroupBox('I-V Curve')
        vbox_iv = QtWidgets.QVBoxLayout()
        self.iv_graph = pg.PlotWidget()
        self.iv_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.iv_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.iv_graph.setTitle('I-V Curve')
        self.iv_graph.setLabel('left', 'Current (A)')
        self.iv_graph.setLabel('bottom', 'Voltage (V)')
        self.iv_data_line = self.iv_graph.plot(pen=colors.blue_pen)
        vbox_iv.addWidget(self.iv_graph)
        self.iv_group_box.setLayout(vbox_iv)
        hbox_top.addWidget(self.iv_group_box, 5)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabs.setTabPosition(QtWidgets.QTabWidget.South)

        self.cell_tab = CellWidget(self)
        self.cell_tab.clipboard_button.clicked.connect(lambda: self.clipboard('iv'))
        self.cell_tab.start_button.clicked.connect(self.start)
        self.cell_tab.to_log.connect(self.logger)
        self.tabs.addTab(self.cell_tab, 'PV Cell')

        self.sensor_tab = SensorWidget(self)
        self.sensor_tab.start_sensor.connect(self.start_sensor)
        self.sensor_tab.stop_sensor.connect(self.stop_sensor)
        self.sensor_tab.clipboard_button.clicked.connect(lambda: self.clipboard('sensor'))
        self.sensor_tab.start_button.clicked.connect(self.plot_sensors)
        self.sensor_tab.to_log.connect(self.logger)
        self.tabs.addTab(self.sensor_tab, 'Sensors')

        self.info_tab = InfoWidget(self)
        self.tabs.addTab(self.info_tab, 'Info')

        hbox_top.addWidget(self.tabs, 3)
        vbox_total.addLayout(hbox_top, 4)

        hbox_bottom = QtWidgets.QHBoxLayout()
        hbox_bottom_left = QtWidgets.QHBoxLayout()
        self.sens_plot_group_box = QtWidgets.QGroupBox('Sensor Plots')
        hbox_sens_plot = QtWidgets.QHBoxLayout()
        self.sensor_graph = pg.PlotWidget()
        self.sensor_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.sensor_graph.plotItem.getAxis('right').setPen(colors.black_pen)
        self.sensor_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.sensor_graph.setTitle('Sensor Readout')
        # create a new ViewBox, link the right axis to its coordinate system
        self.sensor_viewbox = pg.ViewBox()
        self.sensor_graph.scene().addItem(self.sensor_viewbox)
        self.sensor_graph.getAxis('right').linkToView(self.sensor_viewbox)
        self.sensor_viewbox.setXLink(self.sensor_graph)
        self.sensor_graph.setLabel('left', 'Temperature (C)')
        self.sensor_graph.setLabel('right', 'Irradiance (W/m2)')
        self.sensor_graph.setLabel('bottom', 'Time (s)')
        self.temp_data_line = self.sensor_graph.plot(pen=colors.blue_pen)
        self.power_data_line1 = pg.PlotCurveItem(pen=colors.red_pen)
        self.power_data_line2 = pg.PlotCurveItem(pen=colors.green_pen)
        self.power_data_line3 = pg.PlotCurveItem(pen=colors.orange_pen)
        self.sensor_viewbox.addItem(self.power_data_line1)
        self.sensor_viewbox.addItem(self.power_data_line2)
        self.sensor_viewbox.addItem(self.power_data_line3)

        hbox_sens_plot.addWidget(self.sensor_graph)
        self.sens_plot_group_box.setLayout(hbox_sens_plot)
        hbox_bottom_left.addWidget(self.sens_plot_group_box)
        hbox_bottom_left.addStretch(1)
        hbox_bottom.addLayout(hbox_bottom_left, 5)

        self.log_group_box = QtWidgets.QGroupBox('Log')
        grid_log = QtWidgets.QGridLayout()
        self.log_edit = QtWidgets.QTextEdit("Ready to measure...\n", self)
        grid_log.addWidget(self.log_edit, 0, 0)
        self.log_group_box.setLayout(grid_log)
        hbox_bottom.addWidget(self.log_group_box, 3)
        vbox_total.addLayout(hbox_bottom, 2)
        self.setLayout(vbox_total)

        self.data_sensor = np.zeros((int(self.sensor_tab.ais_edit.text()),
                                     int(self.cell_tab.nstep_edit.text())))
        self.sensor_time_data = None
        self.sensor_time_data_averaged = None
        self.sensor_time_max = None
        self.sensor_avg = None

        self.sensor_mes = None
        self.start_sensor()

        self.iv_mes = keithley.Keithley(gpib_port='dummy')
        self.iv_register(self.iv_mes)
        self.iv_mes.update.emit(-1)

    def sensor_register(self, mes):
        self.sensor_mes = mes
        self.sensor_mes.update.connect(self.update_sensor)
        self.sensor_mes.to_log.connect(self.logger)

    @QtCore.pyqtSlot()
    def update_sensor(self):
        if not self.sensor_mes:
            return
        time_val, [tval, d1val, d2val, d3val] = self.sensor_mes.get_sensor_latest()
        self.sensor_tab.temperature_edit.setText("%.2f" % tval)
        self.sensor_tab.diode1_edit.setText("%.1f" % d1val)
        self.sensor_tab.diode2_edit.setText("%.1f" % d2val)
        self.sensor_tab.diode3_edit.setText("%.1f" % d3val)
        if not(self.sensor_tab.sensor_plot_fixed_time.isChecked()) and not self.sensor_mes.port == 'dummy':
            if self.sensor_tab.start_button.isChecked():
                self.sensor_mes.line_plot(self.temp_data_line, channel='temp')
                self.sensor_mes.line_plot(self.power_data_line1, channel='power1')
                self.sensor_mes.line_plot(self.power_data_line2, channel='power2')
                self.sensor_mes.line_plot(self.power_data_line3, channel='power3')
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
                self.sensor_avg = int(self.sensor_tab.sensor_avg_edit.text())
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
                self.temp_data_line.setData(self.sensor_time_data_averaged[0], self.sensor_time_data_averaged[1])
                self.power_data_line1.setData(self.sensor_time_data_averaged[0], self.sensor_time_data_averaged[2])
                self.power_data_line2.setData(self.sensor_time_data_averaged[0], self.sensor_time_data_averaged[3])
                self.power_data_line3.setData(self.sensor_time_data_averaged[0], self.sensor_time_data_averaged[4])

    @QtCore.pyqtSlot()
    def start_sensor(self):
        if self.sensor_mes:
            self.sensor_mes.stop()
        self.sensor_mes = sensor.ArduinoSensor(port=str(self.sensor_tab.sensor_cb.currentText()),
                                               baud=int(self.sensor_tab.baud_edit.text()),
                                               n_data_points=int(self.sensor_tab.datapoints_edit.text()),
                                               data_num_bytes=int(self.sensor_tab.databytes_edit.text()),
                                               n_ai=int(self.sensor_tab.ais_edit.text()),
                                               timeout=float(self.sensor_tab.timeout_edit.text()),
                                               query_period=float(self.sensor_tab.query_edit.text()))
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
        self.temp_data_line.setData([], [])
        self.power_data_line1.setData([], [])
        self.power_data_line2.setData([], [])
        self.power_data_line3.setData([], [])

    def iv_register(self, mes):
        self.iv_mes = mes
        self.iv_mes.update.connect(self.update_iv)
        self.iv_mes.save_settings.connect(self.save_configuration)
        self.iv_mes.restart_sensor.connect(self.start_sensor)
        self.iv_mes.save.connect(self.save)
        self.iv_mes.to_log.connect(self.logger)
        self.iv_mes.end_of_experiment.connect(self.experiment_loop)

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
                                        averages=int(self.cell_tab.naverage_edit.text()),
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
        self.data_sensor = np.zeros((int(self.sensor_tab.ais_edit.text()), int(self.cell_tab.nstep_edit.text())))
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
    def update_iv(self, datapoint):
        if not self.iv_mes:
            return
        if datapoint != -1:
            _, sensor_latest = self.sensor_mes.get_sensor_latest()
            for ai, val in enumerate(sensor_latest):
                self.data_sensor[ai, datapoint] = val
            self.cell_tab.read_volt_edit.setText("%0.1f" % (1e3*self.iv_mes.voltages_set[datapoint]))
            self.cell_tab.read_curr_edit.setText("%0.2f" % (1e3*self.iv_mes.currents[datapoint]))
        self.iv_mes.line_plot(self.iv_data_line)

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

    @QtCore.pyqtSlot(str)
    def clipboard(self, plot):
        if plot == 'iv':
            pixmap = QtWidgets.QWidget.grab(self.iv_graph)
        elif plot == 'sensor':
            pixmap = QtWidgets.QWidget.grab(self.sensor_graph)
        else:
            return
        QtWidgets.QApplication.clipboard().setPixmap(pixmap)

    @QtCore.pyqtSlot(int)
    def save(self, repetition):
        self.data_iv = self.iv_mes.get_keithley_data()
        self.data_iv['Temperature (C)'] = self.data_sensor[0]
        self.data_iv['Irradiance 1 (W/m2)'] = self.data_sensor[1]
        self.data_iv['Irradiance 2 (W/m2)'] = self.data_sensor[2]
        self.data_iv['Irradiance 3 (W/m2)'] = self.data_sensor[3]
        self.data_iv.to_csv(os.path.join(self.cell_tab.save_dir, 'IV_Curve_%s.csv' % str(repetition)))
        self.save_info(os.path.join(self.cell_tab.save_dir, 'IV_Curve_%s.dat' % str(repetition)),
                       self.cell_tab.save_dir, *defaults['info'])
        if repetition == (self.iv_mes.repetitions - 1):
            self.cell_tab.start_button.setChecked(False)
            self.cell_tab.start_button.setText("Start IV")

    @staticmethod
    def save_info(file_path='.', *args):
        info_pars = ['folder', 'experiment_name', 'experiment_date', 'film_id', 'pv_cell_id', 'setup_location',
                     'setup_calibrated', 'setup_suns', 'pid_proportional_band', 'pid_integral',
                     'pid_derivative', 'pid_fuzzy_overshoot', 'pid_heat_tcr1', 'pid_cool_tcr2',
                     'pid_setpoint', 'room_temperature', 'room_humidity']
        df = pd.DataFrame({par: arg for par, arg in zip(info_pars, args)}, index=[0])
        df.to_csv(file_path)

    @QtCore.pyqtSlot()
    def save_configuration(self):
        now = datetime.datetime.now()
        save_file = open(os.path.join(self.cell_tab.save_dir, 'Settings.txt'), 'w')
        save_file.write(now.strftime("%Y-%m-%d %H:%M:%S"))
        save_file.write("\n\nFilm Parameters\n")
        save_file.write("Thickness (mm): %s\n" % str(-1))
        save_file.write("Area (cm2: %s\n" % str(-1))
        save_file.write("\nIV Parameters\n")
        save_file.write("Port: %s\n" % str(self.cell_tab.source_cb.currentText()))
        save_file.write("Start Voltage (V): %s\n" % str(self.cell_tab.start_edit.text()))
        save_file.write("End Voltage (V): %s\n" % str(self.cell_tab.end_edit.text()))
        save_file.write("Voltage Step (V): %s\n" % str(self.cell_tab.step_edit.text()))
        save_file.write("Number of Voltage Steps: %s\n" % str(self.cell_tab.nstep_edit.text()))
        save_file.write("Current Limit (A): %s\n" % str(self.cell_tab.ilimit_edit.text()))
        save_file.write("Voltage Protection (V): %s\n" % str(self.cell_tab.vprot_edit.text()))
        save_file.write("Averages per Datapoint: %s\n" % str(self.cell_tab.naverage_edit.text()))
        save_file.write("Delay between Datapoints: %s\n" % str(self.cell_tab.delay_edit.text()))
        save_file.write("Traces: %s\n" % str(self.cell_tab.reps_edit.text()))
        save_file.write("Delay between Traces: %s\n" % str(self.cell_tab.rep_delay_edit.text()))
        save_file.write("\nSensor Parameters\n")
        save_file.write("Port: %s\n" % str(self.sensor_tab.sensor_cb.currentText()))
        save_file.write("Baud Rate: %s\n" % str(self.sensor_tab.baud_edit.text()))
        save_file.write("Bytes per Datapoint: %s\n" % str(self.sensor_tab.databytes_edit.text()))
        save_file.write("Datapoints: %s\n" % str(self.sensor_tab.datapoints_edit.text()))
        save_file.write("Analogue Inputs: %s\n" % str(self.sensor_tab.ais_edit.text()))
        save_file.write("Query Period (s): %s\n" % str(self.sensor_tab.query_edit.text()))
        save_file.write("Timeout (s): %s\n" % str(self.sensor_tab.timeout_edit.text()))
        save_file.close()

    def check_save_path(self):
        if any([not os.path.exists(self.cell_tab.save_dir),
                os.path.exists(os.path.join(self.cell_tab.save_dir, 'Settings.txt')),
                os.path.exists(os.path.join(self.cell_tab.save_dir, 'IV_Curve_0.csv'))]):
            self.cell_tab.folder_dialog()
            self.check_save_path()

    @QtCore.pyqtSlot(str)
    def logger(self, string):
        timestring = '[' + datetime.datetime.now().strftime('%H:%M:%S') + '] '
        self.log_edit.append(timestring + string)
        self.log_edit.moveCursor(QtGui.QTextCursor.End)
