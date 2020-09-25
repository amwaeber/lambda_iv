import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtCore
import pyvisa as visa
import threading
import time


class Keithley(QtCore.QObject):
    trace_finished = QtCore.pyqtSignal(int, int)
    to_log = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, gpib_port='GPIB::24::INSTR', mode='fixed', n_data_points=100, traces=1, trace_pause=5.0,
                 trigger_delay=0.0, cycles=1, cycle_pause=1.0, min_voltage=-0.01, max_voltage=0.7,
                 compliance_current=0.5, voltage_protection=20, remote_sense=False, use_rear_terminals=False):
        super(Keithley, self).__init__()
        self.gpib_port = gpib_port
        self.mode = mode
        self.n_data_points = n_data_points
        self.traces = traces
        self.trace_pause = trace_pause
        self.trigger_delay = trigger_delay
        self.cycles = cycles
        self.cycle_pause = cycle_pause
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

    def config_keithley(self):
        if str(self.gpib_port) == 'dummy':
            return
        self.to_log.emit('<span style=\" color:#000000;\" >Trying to connect to Keithley at ' + str(self.gpib_port) +
                         '.</span>')
        try:
            self.sourcemeter = self.rm.open_resource(str(self.gpib_port))
            self.to_log.emit('<span style=\" color:#32cd32;\" >Connected to Keithley at ' + str(self.gpib_port) +
                             '.</span>')
        except visa.errors.VisaIOError:
            self.to_log.emit('<span style=\" color:#ff0000;\" >Failed to connect to Keithley at ' +
                             str(self.gpib_port) + '.</span>')
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
        self.sourcemeter.write(f":TRIG:DEL {self.trigger_delay}")
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

    def background_thread(self):
        self.config_keithley()
        while self.is_run:
            for cycle in range(self.cycles):
                time.sleep(5.0)  # give time for sensor connection to re-establish itself
                for trace in range(self.traces):
                    if not self.is_run:
                        self.to_log.emit('<span style=\" color:#ff0000;\" >Scan aborted.</span>')
                        return
                    if str(self.gpib_port) == 'dummy':
                        for dp in range(self.n_data_points):
                            time.sleep(self.trigger_delay)
                            self.times[dp] = time.time()
                    else:
                        self.sourcemeter.write(":OUTPUT ON")
                        self.sourcemeter.write(":TRAC:FEED:CONT NEXT")
                        self.sourcemeter.write(":INIT")
                        time.sleep(self.n_data_points / 100)
                        self.sourcemeter.write(":OUTPUT OFF")
                        data = self.sourcemeter.query_ascii_values("TRAC:DATA?")
                        self.voltages = data[0::5]
                        self.currents = [-dp for dp in data[1::5]]
                        self.times = data[3::5]
                    self.trace_finished.emit(trace, cycle)
                    self.to_log.emit('<span style=\" color:#1e90ff;\" >Finished trace %s of cycle %s.</span>'
                                     % (str(trace + 1), str(cycle + 1)))
                    if trace < self.traces - 1:
                        time.sleep(self.trace_pause)
                if cycle < self.cycles - 1:
                    self.to_log.emit('<span style=\" color:#ff0000;\" >Next Experiment lined up in %d min.</span>' %
                                     int(self.cycle_pause / 60.))
                    time.sleep(self.cycle_pause)
                else:
                    self.to_log.emit('<span style=\" color:#32cd32;\" >Finished IV scan.</span>')
            self.is_run = False
            self.finished.emit()

    def close(self):
        self.is_run = False
        if self.gpib_thread is not None:
            self.gpib_thread.join()
        if not str(self.gpib_port) == 'dummy':
            self.sourcemeter.write(":ABOR")
            self.sourcemeter.write("OUTPUT OFF")
            self.rm.close()
            self.to_log.emit('<span style=\" color:#000000;\" >Disconnected Keithley...</span>')

    def get_keithley_data(self):
        data = pd.DataFrame({
            'Time (s)': self.times,
            'Voltage (V)': self.voltages,
            'Current (A)': self.currents})
        return data

    def line_plot(self, target_line=None):
        if target_line is None:
            target_line = pg.PlotCurveItem()
        if self.gpib_port == 'dummy':
            xval, yval = [], []
        else:
            xval, yval = self.voltages, self.currents
        target_line.setData(xval, yval)
