import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtCore
import pyvisa as visa
import threading
import time


class Keithley(QtCore.QObject):
    trace_finished = QtCore.pyqtSignal(int)
    restart_sensor = QtCore.pyqtSignal()
    to_log = QtCore.pyqtSignal(str)
    experiment_finished = QtCore.pyqtSignal()

    def __init__(self, gpib_port='GPIB::24::INSTR', n_data_points=100, averages=5, repetitions=1, repetition_delay=5.0,
                 delay=0.0, experiment_delay=1.0, min_voltage=-0.01, max_voltage=0.7, compliance_current=0.5,
                 voltage_protection=20, remote_sense=False, use_rear_terminals=False):
        super(Keithley, self).__init__()
        self.gpib_port = gpib_port
        self.n_data_points = n_data_points
        self.traces = repetitions
        self.repetition_delay = repetition_delay
        self.delay = delay
        self.experiment_delay = experiment_delay
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.compliance_current = compliance_current
        self.voltage_protection = voltage_protection
        self.remote_sense = remote_sense
        self.use_rear_terminals = use_rear_terminals
        self.times = np.linspace(self.min_voltage, self.max_voltage, num=self.n_data_points)
        self.voltages = np.zeros_like(self.times)
        self.currents = np.zeros_like(self.times)

        self.is_run = True
        self.gpib_thread = None
        self.sourcemeter = None

        self.rm = visa.ResourceManager()

    def config_keithley(self, **kwargs):
        self.to_log.emit('<span style=\" color:#000000;\" >Trying to connect to: ' + str(self.gpib_port) + '.</span>')
        if str(self.gpib_port) == 'dummy':
            return
        try:
            self.sourcemeter = self.rm.open_resource(str(self.gpib_port))
            self.to_log.emit('<span style=\" color:#32cd32;\" >Connected to ' + str(self.gpib_port) + '.</span>')
        except visa.errors.VisaIOError:
            self.to_log.emit('<span style=\" color:#ff0000;\" >Failed to connect with ' + str(self.gpib_port) +
                             '.</span>')
            self.gpib_port = 'dummy'
            return
        self.sourcemeter.write("*RST")
        self.sourcemeter.write(":SYST:BEEP:STAT OFF")
        self.sourcemeter.write(":SOUR:FUNC:MODE VOLT")
        self.sourcemeter.write("SOUR:SWE:SPAC LIN")
        self.sourcemeter.write(f"SOUR:VOLT:STAR {self.min_voltage}")
        self.sourcemeter.write(f"SOUR:VOLT:STOP {self.max_voltage}")
        self.sourcemeter.write(f"SOUR:SWE:POIN {self.n_data_points}")
        self.sourcemeter.write(":SOUR:VOLT:MODE SWE")
        self.sourcemeter.write(f"TRIG:COUN {self.n_data_points}")
        self.sourcemeter.write(":ARM:COUNT 1")
        self.sourcemeter.write(f":TRIG:DEL {self.delay}")
        self.sourcemeter.write(":SOUR:DEL 0.0")
        self.sourcemeter.write(f":SOUR:VOLT:RANGE {self.voltage_protection}")
        self.sourcemeter.write(f":SENSE:CURR:PROT {self.compliance_current}")
        self.sourcemeter.write(":SENSE:FUNC:CONC OFF")
        self.sourcemeter.write(":SENSE:FUNC 'CURR'")
        self.sourcemeter.write(":SENSE:CURR:RANGE 0.1")
        self.sourcemeter.write(":SENSE:CURR:NPLC 0.01")
        self.sourcemeter.write(":SENSE:AVERAGE:STAT OFF")
        self.sourcemeter.write(":DISP:ENAB OFF")
        self.sourcemeter.write(":SYSTEM:AZERO:STAT OFF")
        if self.use_rear_terminals:
            self.sourcemeter.write(":ROUT:TERM REAR")
        else:
            self.sourcemeter.write(":ROUT:TERM FRON")
        if self.remote_sense:
            self.sourcemeter.write(":SYST:RSEN ON;")
        else:
            self.sourcemeter.write(":SYST:RSEN OFF;")
        self.sourcemeter.write(":TRAC:CLE")
        self.sourcemeter.write(f":TRAC:POIN {self.n_data_points}")
        self.sourcemeter.write(":TRAC:FEED SENS")

    def read_keithley_start(self):
        self.is_run = True
        if self.gpib_thread is None:
            self.gpib_thread = threading.Thread(target=self.background_thread)
            self.gpib_thread.start()

    def get_keithley_data(self):
        data = pd.DataFrame({
            'Time (s)': self.times,
            'Voltage (V)': self.voltages,
            'Current (A)': self.currents})
        return data

    def background_thread(self):
        time.sleep(self.experiment_delay)  # pause between experiments
        self.restart_sensor.emit()
        time.sleep(5.0)  # give time for sensor connection to re-establish itself
        self.config_keithley()
        while self.is_run:
            for trace in range(self.traces):
                if not self.is_run:
                    self.to_log.emit('<span style=\" color:#ff0000;\" >Scan aborted.</span>')
                    return
                if str(self.gpib_port) == 'dummy':
                    for dp in range(self.n_data_points):
                        time.sleep(self.delay)
                        self.times[dp] = time.time()
                else:
                    self.sourcemeter.write(":OUTPUT ON")
                    self.sourcemeter.write(":TRAC:FEED:CONT NEXT")
                    self.sourcemeter.write(":INIT")
                    time.sleep(self.n_data_points / 100)  # npoints * 10ms
                    self.sourcemeter.write(":OUTPUT OFF")
                    data = self.sourcemeter.query_ascii_values("TRAC:DATA?")
                    self.voltages = data[0::5]
                    self.currents = [-dp for dp in data[1::5]]
                    self.times = data[3::5]  # add time.time() for timestamp
                self.trace_finished.emit(trace)  # couple save.emit(rep) into it
                self.to_log.emit('<span style=\" color:#1e90ff;\" >Finished curve #%s</span>' % str(trace + 1))
                if trace < self.traces - 1:
                    time.sleep(self.repetition_delay)
                else:
                    self.to_log.emit('<span style=\" color:#32cd32;\" >Finished IV scan.</span>')
            self.is_run = False
        self.experiment_finished.emit()

    def close(self):
        self.is_run = False
        if self.gpib_thread is not None:
            self.gpib_thread.join()
        if not str(self.gpib_port) == 'dummy':
            self.sourcemeter.shutdown()
            self.to_log.emit('<span style=\" color:#000000;\" >Disconnected Keithley...</span>')

    def line_plot(self, target_line=None):
        if target_line is None:
            graph = pg.PlotWidget()
            target_line = graph.plot()
        if self.gpib_port == 'dummy':
            xval, yval = [], []
        else:
            xval, yval = self.voltages, self.currents
        target_line.setData(xval, yval)
