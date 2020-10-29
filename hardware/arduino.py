import collections
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore
import serial
import struct
import threading
import time

import utility.conversions as conversions


class Arduino(QtCore.QObject):
    update = QtCore.pyqtSignal()
    to_log = QtCore.pyqtSignal(str)

    def __init__(self, serial_port='COM3', mode='continuous', serial_baud=38400, n_data_points=100, data_num_bytes=2,
                 n_ai=4, query_period=0.25, fixed_time=60., supply_voltage=5.2):
        super(Arduino, self).__init__()

        self.port = serial_port
        self.supply_voltage = supply_voltage
        self.mode = mode
        self.query_period = query_period
        self.fixed_time = fixed_time
        self.n_data_points = int(
            np.ceil(self.fixed_time / self.query_period)) if self.mode == 'fixed' else n_data_points

        self.baud = serial_baud
        self.data_num_bytes = data_num_bytes
        self.n_ai = n_ai

        self.raw_data = bytearray(self.n_ai * self.data_num_bytes)
        self.data_type = 'h'  # 2 byte integer
        self.data = [collections.deque(maxlen=self.n_data_points) for _ in range(self.n_ai)]
        self.times = [collections.deque(maxlen=self.n_data_points) for _ in range(self.n_ai)]
        self.init_time = time.time()

        self.is_run = True
        self.is_receiving = False
        self.serial_thread = None
        self.serialConnection = None

    def config_serial(self):
        if str(self.port) == 'dummy':
            return
        self.to_log.emit('<span style=\" color:#000000;\" >Trying to connect to Arduino at ' + str(self.port) +
                         '.</span>')
        try:
            self.serialConnection = serial.Serial(self.port, self.baud, timeout=4)
            self.to_log.emit('<span style=\" color:#32cd32;\" >Connected to Arduino at ' + str(self.port) +
                             '.</span>')
        except serial.serialutil.SerialException:
            self.to_log.emit('<span style=\" color:#ff0000;\" >Failed to connect to Arduino at ' + str(self.port) +
                             '.</span>')
            self.port = 'dummy'
            return

    def read_serial_start(self):
        self.is_run = True
        if self.serial_thread is None:
            self.serial_thread = threading.Thread(target=self.background_thread)
            self.serial_thread.start()
            # Block till we start receiving values
            while not self.is_receiving:
                time.sleep(0.1)

    def background_thread(self):  # retrieve data
        self.config_serial()
        time.sleep(1.0)  # give some buffer time for retrieving data
        n = 0
        while self.is_run:
            if str(self.port) == 'dummy':
                self.is_receiving = True
            else:
                try:
                    self.serialConnection.reset_input_buffer()
                    self.serialConnection.readinto(self.raw_data)
                    self.is_receiving = True
                except (AttributeError, serial.serialutil.SerialException):
                    self.port = 'dummy'
                    self.is_run = False
                    self.to_log.emit('<span style=\" color:#ff0000;\" >Lost connection to Arduino. Check connection '
                                     'and refresh COM ports.</span>')
            self.update.emit()
            if self.mode == 'fixed':
                n += 1
                self.is_run = False if n >= self.n_data_points else True
            time.sleep(self.query_period)

    def close(self):
        self.is_run = False
        if self.serial_thread is not None:
            self.serial_thread.join()
        if not str(self.port) == 'dummy':
            self.serialConnection.close()
            self.to_log.emit('<span style=\" color:#000000;\" >Disconnected serial port...</span>')

    def get_serial_data(self, plt_number):
        self.times[plt_number].append(time.time() - self.init_time)
        data = self.raw_data[(plt_number * self.data_num_bytes):(self.data_num_bytes +
                                                                 plt_number * self.data_num_bytes)]
        value,  = struct.unpack(self.data_type, data)
        if plt_number == 2:
            value = conversions.voltage_to_temperature(conversions.digital_to_voltage(value, bits=15,
                                                                                      voltage_range=6.144),
                                                       voltage_range=self.supply_voltage)
        else:
            value = conversions.voltage_to_power(conversions.digital_to_voltage(value, bits=15, voltage_range=6.144))
        self.data[plt_number].append(value)  # we get the latest data point and append it to our array
        return self.times[plt_number], self.data[plt_number], self.data[plt_number][-1]

    def line_plot(self, target_line=None, channel=None):
        channels = {'temp': 2, 'power1': 0, 'power2': 1, 'power3': 3}
        if target_line is None:
            target_line = pg.PlotCurveItem()
        if self.port == 'dummy':
            xval, yval = [], []
        elif channel in channels.keys():
            xval, yval, _ = self.get_serial_data(channels[channel])
        else:
            xval, yval = [], []
        target_line.setData(np.array(xval), np.array(yval))

    def get_sensor_latest(self):
        if not self.port == 'dummy':
            sensor_time = self.get_serial_data(0)[0][-1]
            sensor_readout = [self.get_serial_data(i)[2] for i in range(self.n_ai)]
        else:
            sensor_time = 0.
            sensor_readout = [-1.0 for _ in range(self.n_ai)]
        return sensor_time, sensor_readout
