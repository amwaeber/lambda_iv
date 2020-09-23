import collections
import datetime
import os
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import time

import hardware.keithley as keithley
import hardware.arduino as arduino
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

        self.ns = collections.deque(maxlen=25)
        self.isc = collections.deque(maxlen=25)
        self.voc = collections.deque(maxlen=25)
        self.pmax = collections.deque(maxlen=25)
        self.ais = [collections.deque(maxlen=25) for _ in range(defaults['arduino'][3])]

        hbox_total = QtWidgets.QHBoxLayout()

        self.plot_widget = PlotsWidget()
        hbox_total.addWidget(self.plot_widget, 6)

        vbox_right = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabs.setTabPosition(QtWidgets.QTabWidget.South)

        self.cell_tab = CellWidget(self)
        self.cell_tab.clipboard_button.clicked.connect(self.clipboard)
        self.cell_tab.run_cont_button.clicked.connect(lambda: self.start('continuous'))
        self.cell_tab.run_fixed_button.clicked.connect(lambda: self.start('fixed'))
        self.cell_tab.run_isc_button.clicked.connect(lambda: self.start('isc'))
        self.cell_tab.to_log.connect(self.logger)
        self.tabs.addTab(self.cell_tab, 'PV Cell')

        self.sensor_tab = SensorWidget(self)
        self.sensor_tab.start_sensor.connect(self.start_sensor)
        self.sensor_tab.stop_sensor.connect(self.stop_sensor)
        self.sensor_tab.run_cont_button.clicked.connect(lambda: self.start_sensor('continuous'))
        self.sensor_tab.run_fixed_button.clicked.connect(lambda: self.start_sensor('fixed'))
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

        self.sensor_mes = None
        self.iv_mes = None

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
        if self.sensor_mes.mode != 'cell_measure':
            self.sensor_mes.line_plot(self.plot_widget.temp_data_line, channel='temp')
            self.sensor_mes.line_plot(self.plot_widget.power_data_line1, channel='power1')
            self.sensor_mes.line_plot(self.plot_widget.power_data_line2, channel='power2')
            self.sensor_mes.line_plot(self.plot_widget.power_data_line3, channel='power3')

    @QtCore.pyqtSlot()
    def start_sensor(self, mode='continuous'):
        # Block if measurement is running
        if self.iv_mes and mode != 'cell_measure':
            self.logger('<span style=\" color:#ff0000;\" > Stop current measurement before restarting sensor.</span>')
            return
        self.stop_sensor()
        # Stop measurement if measurement is running
        if self.sensor_tab.buttons_pressed() == 0 and mode != 'cell_measure':
            self.sensor_tab.set_button_text('continuous', False)
            self.sensor_tab.set_button_text('fixed', False)
            return
        # Toggle measurement
        elif mode == 'cell_measure':
            self.sensor_tab.set_button_text('continuous', False)
            self.sensor_tab.set_button_text('fixed', False)
            self.plot_widget.temp_graph.setLabel('bottom', 'Scan #')
        elif mode == 'continuous':
            self.sensor_tab.set_button_text('fixed', False)
            self.plot_widget.temp_graph.setLabel('bottom', 'Time (s)')
        elif mode == 'fixed':
            self.sensor_tab.set_button_text('continuous', False)
            self.plot_widget.temp_graph.setLabel('bottom', 'Time (s)')
        # Give warning and run as dummy if parameter error
        if self.sensor_tab.check_sensor_parameters() is False:
            self.sensor_tab.set_button_text('continuous', False)
            self.sensor_tab.set_button_text('fixed', False)
            self.sensor_mes = arduino.Arduino("dummy", mode, *defaults['arduino'])
        else:
            self.sensor_mes = arduino.Arduino(str(self.sensor_tab.sensor_cb.currentText()), mode, *defaults['arduino'])
        self.sensor_register(self.sensor_mes)
        self.sensor_mes.read_serial_start()

    @QtCore.pyqtSlot()
    def stop_sensor(self):
        if self.sensor_mes:
            self.sensor_mes.close()
            self.sensor_mes = None

    def iv_register(self, mes):
        self.iv_mes = mes
        self.iv_mes.trace_finished.connect(self.trace_finished)
        self.iv_mes.to_log.connect(self.logger)

    def start(self, mode='fixed'):
        # Stop measurement if measurement is running
        if self.cell_tab.buttons_pressed() == 0:  # button unclicked manually or by software
            self.stop()
            return
        # Block attempt to start different measurement
        elif self.cell_tab.buttons_pressed() > 1:
            self.logger('<span style=\" color:#ff0000;\" > Stop current measurement before starting new one.</span>')
            self.cell_tab.stop_button(mode)
            return
        # Do not start measurement if faulty parameters are set
        elif self.cell_tab.check_iv_parameters() is False:
            self.cell_tab.stop_button(mode)
            return
        self.info_tab.save_defaults()
        self.iv_mes = keithley.Keithley(gpib_port=str(self.cell_tab.source_cb.currentText()),
                                        mode=mode,
                                        n_data_points=int(self.cell_tab.nstep_edit.text()),
                                        trigger_delay=float(self.cell_tab.trigger_delay_edit.text()),
                                        traces=int(self.cell_tab.traces_edit.text()),
                                        trace_pause=float(self.cell_tab.trace_pause_edit.text()),
                                        cycles=int(self.cell_tab.cycles_edit.text()),
                                        cycle_pause=float(self.cell_tab.cycle_pause_edit.text()) * 60,
                                        min_voltage=float(self.cell_tab.start_edit.text()),
                                        max_voltage=float(self.cell_tab.end_edit.text()),
                                        compliance_current=float(self.cell_tab.ilimit_edit.text()),
                                        voltage_protection=int(self.cell_tab.vprot_edit.text()),
                                        remote_sense=self.cell_tab.remote_sense_btn.isChecked(),
                                        use_rear_terminals=self.cell_tab.rear_terminal_btn.isChecked()
                                        )
        self.iv_register(self.iv_mes)
        self.check_save_path()
        self.start_sensor('cell_measure')
        self.cell_tab.set_button_text(mode, True)
        self.iv_mes.read_keithley_start()

    @QtCore.pyqtSlot(int, int)
    def trace_finished(self, trace_count, cycle_count):
        if not self.iv_mes:
            return
        _, sensor_latest = self.sensor_mes.get_sensor_latest()
        timestamp = time.time()
        self.iv_mes.line_plot(self.plot_widget.iv_data_line)
        data_iv = self.iv_mes.get_keithley_data()
        fit_data_iv = fit_iv(data_iv)
        self.cell_tab.update_readout(fit_data_iv)

        total_count = cycle_count * self.iv_mes.traces + trace_count
        self.update_plots(total_count, fit_data_iv, *sensor_latest)

        save_file = open(os.path.join(self.cell_tab.save_dir, 'IV_Curve_%s.csv' % str(total_count)), "a+")
        save_file.write(self.save_string(timestamp,
                                         *sensor_latest,
                                         *defaults['info'],
                                         *defaults['cell'],
                                         *fit_data_iv))
        data_iv.to_csv(save_file)
        save_file.close()

        if total_count == (self.iv_mes.traces * self.iv_mes.cycles - 1):
            self.cell_tab.stop_button(self.iv_mes.mode)

    def update_plots(self, trace_count, fit_data, *args):
        isc, _, voc, _, pmax = fit_data
        self.ns.append(trace_count)
        self.isc.append(isc)  # TODO: update only if fit successful
        self.voc.append(voc)
        self.pmax.append(pmax)
        for ai, arg in zip(self.ais, args):
            ai.append(arg)
        self.plot_widget.isc_data_line.setData(self.ns, self.isc)
        self.plot_widget.voc_data_line.setData(self.ns, self.voc)
        self.plot_widget.pmax_data_line.setData(self.ns, self.pmax)
        self.plot_widget.temp_data_line.setData(self.ns, self.ais[2])
        self.plot_widget.power_data_line1.setData(self.ns, self.ais[0])
        self.plot_widget.power_data_line2.setData(self.ns, self.ais[1])
        self.plot_widget.power_data_line3.setData(self.ns, self.ais[3])

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
        self.sensor_tab.run_cont_button.click()  # set sensor to continuous again

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
