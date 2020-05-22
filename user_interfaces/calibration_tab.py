from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os
from PyQt5 import QtWidgets, QtGui, QtCore

import hardware.sensor as sensor
from utility.config import paths


class Calibration(QtWidgets.QWidget):
    update_plt = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Calibration, self).__init__(parent)

        self.temperature_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.temperature_canvas.figure.tight_layout(pad=0.3)
        self.update_plt.connect(self.temperature_canvas.figure.canvas.draw)
        self.power_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.power_canvas.figure.tight_layout(pad=0.3)
        self.update_plt.connect(self.power_canvas.figure.canvas.draw)

        # self.sensor_traces = [[list(range(100)), [0] * 100] for _ in range(5)]

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.temperature_canvas)
        hbox.addWidget(self.power_canvas)
        self.setLayout(hbox)

        self.plot(target_fig=self.temperature_canvas.figure, chs=['temp'])
        self.plot(target_fig=self.power_canvas.figure, chs=['power'])
        self.update_plt.emit()

        # self.mes = sensor.ArduinoSensor(port="COM3", query_period=0.25)
        # self.register(self.mes)
        # self.mes.update.emit()

    # def register(self, mes):
    #     self.mes = mes
    #     self.mes.update[list, list].connect(self.update)

    @QtCore.pyqtSlot(list)
    def update(self, sensor_traces):
        # if not self.mes:
        #     return
        # self.sensor_traces = sensor_traces  # sometimes seems to cause crash?
        # print(sensor_traces[0])
        self.plot(target_fig=self.temperature_canvas.figure, chs=['temp'], data=sensor_traces)
        self.plot(target_fig=self.power_canvas.figure, chs=['power'], data=sensor_traces)
        self.update_plt.emit()

    def plot(self, target_fig=None, chs=None, data=None):
        if chs is None:
            chs = []
        if data is None:
            data = [[list(range(100)), [0] * 100] for _ in range(5)]
        if target_fig is None:
            fig = Figure()
            canvas = FigureCanvas(fig)
        else:
            fig = target_fig
        fig.clear()
        axis = fig.add_subplot(111)
        if 'temp' in chs:
            axis.set_xlabel("Time (s)")
            axis.set_ylabel("Temperature (C)")
            xval, yval = data[0]
            axis.plot(xval, yval, lw=1.3)
        if 'power' in chs:
            axis.set_xlabel("Time (s)")
            axis.set_ylabel("Illumination (W/m2)")
            for i in [1, 2, 3, 4]:
                xval, yval = data[i]
                axis.plot(xval, yval, lw=1.3)
        return fig

    # def start(self):
    #     if self.mes:
    #         self.mes.close()
    #     self.mes = sensor.ArduinoSensor(port="COM3", query_period=0.25)
    #     self.register(self.mes)
    #     self.mes.read_serial_start()
    #
    # def stop(self):
    #     if self.mes:
    #         self.mes.close()
