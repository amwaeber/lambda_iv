from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg

import utility.colors as colors


class PlotsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(PlotsWidget, self).__init__(parent)

        hbox_total = QtWidgets.QHBoxLayout()

        vbox_left = QtWidgets.QVBoxLayout()

        # I-V Curve
        self.iv_graph = pg.PlotWidget()
        self.iv_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.iv_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.iv_graph.setTitle('Photocurrent (mA)')
        self.iv_graph.setLabel('bottom', 'Voltage (V)')
        self.iv_data_line = self.iv_graph.plot(pen=colors.blue_pen)
        vbox_left.addWidget(self.iv_graph, 2)

        # Isc
        self.isc_graph = pg.PlotWidget()
        self.isc_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.isc_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.isc_graph.setTitle('Short-Circuit Current (A)')
        self.isc_graph.setLabel('bottom', 'Scan #')
        self.isc_data_line = self.isc_graph.plot(pen=colors.red_pen)
        vbox_left.addWidget(self.isc_graph, 2)

        # Temperature
        self.temp_graph = pg.PlotWidget()
        self.temp_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.temp_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.temp_graph.setTitle('Temperature (C)')
        self.temp_graph.setLabel('bottom', 'Time (s)')
        self.temp_data_line = self.temp_graph.plot(pen=colors.lblue_pen)
        vbox_left.addWidget(self.temp_graph, 2)
        hbox_total.addLayout(vbox_left, 3)

        vbox_right = QtWidgets.QVBoxLayout()

        # Maximum Power Point
        self.pmax_graph = pg.PlotWidget()
        self.pmax_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.pmax_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.pmax_graph.setTitle('Maximum Power (mW)')
        self.pmax_graph.setLabel('bottom', 'Scan #')
        self.pmax_data_line = self.pmax_graph.plot(pen=colors.orange_pen)
        vbox_right.addWidget(self.pmax_graph, 2)

        # Voc
        self.voc_graph = pg.PlotWidget()
        self.voc_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.voc_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.voc_graph.setTitle('Open-Circuit Voltage (mV)')
        self.voc_graph.setLabel('bottom', 'Scan #')
        self.voc_data_line = self.voc_graph.plot(pen=colors.green_pen)
        vbox_right.addWidget(self.voc_graph, 2)

        # Irradiance
        self.irrad_graph = pg.PlotWidget()
        self.irrad_graph.plotItem.getAxis('left').setPen(colors.black_pen)
        self.irrad_graph.plotItem.getAxis('bottom').setPen(colors.black_pen)
        self.irrad_graph.setTitle('Irradiance (W/m2)')
        self.irrad_graph.setLabel('bottom', 'Time (s)')
        self.power_data_line1 = self.irrad_graph.plot(pen=colors.violet_pen)
        self.power_data_line2 = self.irrad_graph.plot(pen=colors.lred_pen)
        self.power_data_line3 = self.irrad_graph.plot(pen=colors.lgreen_pen)
        vbox_right.addWidget(self.irrad_graph, 2)
        hbox_total.addLayout(vbox_right, 3)

        self.setLayout(hbox_total)
