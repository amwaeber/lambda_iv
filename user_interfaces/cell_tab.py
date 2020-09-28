import os
from PyQt5 import QtWidgets, QtGui, QtCore
import pyvisa as visa

from user_interfaces.widgets.separator import Separator
from user_interfaces.widgets.switch_button import Switch
from utility.config import defaults, paths, ports, write_config


class CellWidget(QtWidgets.QWidget):
    to_log = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(CellWidget, self).__init__(parent)

        self.save_dir = paths['last_save']

        vbox_total = QtWidgets.QVBoxLayout()
        vbox_total.addWidget(QtWidgets.QLabel("Parameters", self))
        grid_source = QtWidgets.QGridLayout()
        grid_source.addWidget(QtWidgets.QLabel("Start (V)", self), 0, 0)
        self.start_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][0], self)
        self.start_edit.setFixedWidth(60)
        self.start_edit.textChanged.connect(self.update_steps)
        grid_source.addWidget(self.start_edit, 0, 1)
        grid_source.addWidget(QtWidgets.QLabel("End (V)", self), 1, 0)
        self.end_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][1], self)
        self.end_edit.setFixedWidth(60)
        self.end_edit.textChanged.connect(self.update_steps)
        grid_source.addWidget(self.end_edit, 1, 1)
        grid_source.addWidget(QtWidgets.QLabel("Step (V)", self), 0, 2)
        self.step_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][2], self)
        self.step_edit.setFixedWidth(60)
        self.step_edit.setDisabled(True)
        grid_source.addWidget(self.step_edit, 0, 3)
        grid_source.addWidget(QtWidgets.QLabel("# Steps", self), 1, 2)
        self.nstep_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][3], self)
        self.nstep_edit.setFixedWidth(60)
        self.nstep_edit.textChanged.connect(self.update_steps)
        grid_source.addWidget(self.nstep_edit, 1, 3)
        grid_source.addWidget(QtWidgets.QLabel("I Limit (A)", self), 0, 4)
        self.ilimit_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][4], self)
        self.ilimit_edit.setFixedWidth(60)
        grid_source.addWidget(self.ilimit_edit, 0, 5)
        grid_source.addWidget(QtWidgets.QLabel("V Protection (V)", self), 1, 4)
        self.vprot_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][5], self)
        self.vprot_edit.setFixedWidth(60)
        grid_source.addWidget(self.vprot_edit, 1, 5)

        grid_source.addWidget(QtWidgets.QLabel("Averages", self), 2, 0)
        self.averages_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][6], self)
        self.averages_edit.setFixedWidth(60)
        grid_source.addWidget(self.averages_edit, 2, 1)
        grid_source.addWidget(QtWidgets.QLabel("Trigger Delay (s)", self), 3, 0)
        self.trigger_delay_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][7], self)
        self.trigger_delay_edit.setFixedWidth(60)
        grid_source.addWidget(self.trigger_delay_edit, 3, 1)
        grid_source.addWidget(QtWidgets.QLabel("Traces", self), 2, 2)
        self.traces_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][8], self)
        self.traces_edit.setFixedWidth(60)
        grid_source.addWidget(self.traces_edit, 2, 3)
        grid_source.addWidget(QtWidgets.QLabel("Trace Pause (s)", self), 3, 2)
        self.trace_pause_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][9], self)
        self.trace_pause_edit.setFixedWidth(60)
        grid_source.addWidget(self.trace_pause_edit, 3, 3)
        grid_source.addWidget(QtWidgets.QLabel("Cycles", self), 2, 4)
        self.cycles_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][10], self)
        self.cycles_edit.setFixedWidth(60)
        grid_source.addWidget(self.cycles_edit, 2, 5)
        grid_source.addWidget(QtWidgets.QLabel("Cycle Pause (min)", self), 3, 4)
        self.cycle_pause_edit = QtWidgets.QLineEdit('%s' % defaults['cell'][11], self)
        self.cycle_pause_edit.setFixedWidth(60)
        grid_source.addWidget(self.cycle_pause_edit, 3, 5)
        vbox_total.addLayout(grid_source)

        hbox_terminals = QtWidgets.QHBoxLayout()
        grid_terminals = QtWidgets.QGridLayout()
        meas2w_label = QtWidgets.QLabel("2 Wire Sensing", self)
        meas2w_label.setAlignment(QtCore.Qt.AlignRight)
        grid_terminals.addWidget(meas2w_label, 0, 0)
        self.remote_sense_btn = Switch()
        self.remote_sense_btn.setChecked(defaults['cell'][12])
        grid_terminals.addWidget(self.remote_sense_btn, 0, 1)
        grid_terminals.addWidget(QtWidgets.QLabel("4 Wire Sensing", self), 0, 2)
        front_label = QtWidgets.QLabel("Front Terminals", self)
        front_label.setAlignment(QtCore.Qt.AlignRight)
        grid_terminals.addWidget(front_label, 1, 0)
        self.rear_terminal_btn = Switch()
        self.rear_terminal_btn.setChecked(defaults['cell'][13])
        grid_terminals.addWidget(self.rear_terminal_btn, 1, 1)
        grid_terminals.addWidget(QtWidgets.QLabel("Rear Terminals", self), 1, 2)
        hbox_terminals.addLayout(grid_terminals)
        hbox_terminals.addStretch(-1)
        vbox_total.addLayout(hbox_terminals)

        hbox_port = QtWidgets.QHBoxLayout()
        hbox_port.addWidget(QtWidgets.QLabel("GPIB Port", self))
        self.source_cb = QtWidgets.QComboBox()
        self.source_cb.setFixedWidth(160)
        self.get_gpib_ports()
        self.source_cb.currentTextChanged.connect(self.source_port_changed)
        hbox_port.addWidget(self.source_cb)
        self.refresh_button = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(paths['icons'], 'refresh.png')), '')
        self.refresh_button.clicked.connect(self.get_gpib_ports)
        self.refresh_button.setToolTip('Update Port')
        hbox_port.addWidget(self.refresh_button)
        hbox_port.addStretch(-1)
        vbox_total.addLayout(hbox_port)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Save", self))
        hbox_folder = QtWidgets.QHBoxLayout()
        self.folder_button = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(paths['icons'], 'folder.png')), '')
        self.folder_button.clicked.connect(self.folder_dialog)
        self.folder_button.setToolTip('Choose folder')
        hbox_folder.addWidget(self.folder_button)
        self.folder_edit = QtWidgets.QLineEdit(self.save_dir, self)
        self.folder_edit.setMinimumWidth(180)
        self.folder_edit.setDisabled(True)
        hbox_folder.addWidget(self.folder_edit)
        self.clipboard_button = QtWidgets.QPushButton(
            QtGui.QIcon(os.path.join(paths['icons'], 'clipboard.png')), '')
        self.clipboard_button.setToolTip('Save plot to clipboard')
        hbox_folder.addWidget(self.clipboard_button)
        vbox_total.addLayout(hbox_folder)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Readout", self))
        hbox_readout = QtWidgets.QHBoxLayout()
        hbox_readout.addWidget(QtWidgets.QLabel("Isc (mA)", self))
        self.show_isc_edit = QtWidgets.QLineEdit('-1', self)
        self.show_isc_edit.setFixedWidth(60)
        self.show_isc_edit.setDisabled(True)
        hbox_readout.addWidget(self.show_isc_edit)
        hbox_readout.addWidget(QtWidgets.QLabel("Voc (mV)", self))
        self.show_voc_edit = QtWidgets.QLineEdit('-1', self)
        self.show_voc_edit.setFixedWidth(60)
        self.show_voc_edit.setDisabled(True)
        hbox_readout.addWidget(self.show_voc_edit)
        hbox_readout.addWidget(QtWidgets.QLabel("Pmax (mW)", self))
        self.show_pmax_edit = QtWidgets.QLineEdit('-1', self)
        self.show_pmax_edit.setFixedWidth(60)
        self.show_pmax_edit.setDisabled(True)
        hbox_readout.addWidget(self.show_pmax_edit)
        hbox_readout.addStretch(-1)
        vbox_total.addLayout(hbox_readout)

        vbox_total.addWidget(Separator())
        vbox_total.addWidget(QtWidgets.QLabel("Measure", self))
        hbox_measure = QtWidgets.QHBoxLayout()
        self.run_cont_button = QtWidgets.QPushButton("Run \u221e")
        self.run_cont_button.setCheckable(True)
        self.run_cont_button.setStyleSheet("QPushButton:checked { background-color: #32cd32 }")
        self.run_cont_button.setToolTip("Run Continuously")
        hbox_measure.addWidget(self.run_cont_button)
        self.run_fixed_button = QtWidgets.QPushButton("Run Fixed")
        self.run_fixed_button.setCheckable(True)
        self.run_fixed_button.setStyleSheet("QPushButton:checked { background-color: #32cd32 }")
        self.run_fixed_button.setToolTip('Run fixed set')
        hbox_measure.addWidget(self.run_fixed_button)
        self.run_isc_button = QtWidgets.QPushButton("Run Isc")
        self.run_isc_button.setCheckable(True)
        self.run_isc_button.setStyleSheet("QPushButton:checked { background-color: #32cd32 }")
        self.run_isc_button.setToolTip('Record Isc')
        hbox_measure.addWidget(self.run_isc_button)
        hbox_measure.addStretch(-1)
        vbox_total.addLayout(hbox_measure)
        vbox_total.addStretch(-1)
        self.setLayout(vbox_total)

    def button_checked_count(self):
        return sum([self.run_cont_button.isChecked(), self.run_fixed_button.isChecked(),
                    self.run_isc_button.isChecked()])

    def reset_measure_buttons(self):
        for button, label in zip([self.run_cont_button, self.run_fixed_button, self.run_isc_button],
                                 ["Run \u221e", "Run Fixed", "Run Isc"]):
            button.setChecked(False)
            button.setText(label)

    def reset_single_button(self, mode):
        if mode == 'continuous':
            self.run_cont_button.setChecked(False)
            self.run_cont_button.setText("Run \u221e")
        elif mode == 'fixed':
            self.run_fixed_button.setChecked(False)
            self.run_fixed_button.setText("Run Fixed")
        elif mode == 'isc':
            self.run_isc_button.setChecked(False)
            self.run_isc_button.setText("Run Isc")

    def set_button_active(self, mode):
        if mode == 'continuous':
            self.run_cont_button.setText("Stop")
        elif mode == 'fixed':
            self.run_fixed_button.setText("Stop")
        elif mode == 'isc':
            self.run_isc_button.setText("Stop")

    def folder_dialog(self):
        self.save_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory', self.save_dir))
        self.folder_edit.setText(self.save_dir)

    @QtCore.pyqtSlot()
    def update_steps(self):
        try:  # capture empty cells, typos etc during data entry
            steps = (float(self.end_edit.text()) - float(self.start_edit.text())) / float(self.nstep_edit.text())
            self.step_edit.setText(f"{steps:.3f}")
        except (ZeroDivisionError, ValueError):
            pass

    def get_gpib_ports(self):
        self.source_cb.clear()
        self.source_cb.addItem('dummy')
        rm = visa.ResourceManager()
        for port in rm.list_resources():
            if port.startswith('GPIB'):
                self.source_cb.addItem(port)
            if port == ports['keithley']:
                self.source_cb.setCurrentText(port)
        rm.close()

    def source_port_changed(self):
        ports['keithley'] = self.source_cb.currentText()

    def update_readout(self, fitted_vals):
        isc, _, voc, _, pmax = fitted_vals
        self.show_isc_edit.setText(f"{isc:.1f}")
        self.show_voc_edit.setText(f"{voc:.1f}")
        self.show_pmax_edit.setText(f"{pmax:.2f}")

    def check_iv_parameters(self):
        try:
            int(self.nstep_edit.text())
            int(self.vprot_edit.text())
            int(self.averages_edit.text())
            int(self.traces_edit.text())
            int(self.cycles_edit.text())
            float(self.start_edit.text())
            float(self.end_edit.text())
            float(self.ilimit_edit.text())
            float(self.trigger_delay_edit.text())
            float(self.trace_pause_edit.text())
            float(self.cycle_pause_edit.text())
        except (ZeroDivisionError, ValueError):
            self.to_log.emit('<span style=\" color:#ff0000;\" >Some parameters are not in the right format. '
                             'Please check before starting measurement.</span>')
            return False
        if any([float(self.end_edit.text()) > 0.75,
                float(self.start_edit.text()) < -0.15,
                float(self.start_edit.text()) > float(self.end_edit.text()),
                float(self.trigger_delay_edit.text()) < 0.0,
                float(self.trace_pause_edit.text()) < 1.0,
                float(self.cycle_pause_edit.text()) < 0.5,
                float(self.ilimit_edit.text()) > 0.5,
                float(self.ilimit_edit.text()) <= 0.,
                int(self.averages_edit.text()) < 1,
                int(self.vprot_edit.text()) > 200,
                int(self.vprot_edit.text()) < 5,
                int(self.traces_edit.text()) < 1,
                int(self.cycles_edit.text()) < 1
                ]):
            self.to_log.emit('<span style=\" color:#ff0000;\" >Some parameters are out of bounds. '
                             'Please check before starting measurement.</span>')
            return False
        self.save_defaults()
        return True

    def save_defaults(self):
        defaults['cell'] = [self.start_edit.text(), self.end_edit.text(), self.step_edit.text(), self.nstep_edit.text(),
                            self.ilimit_edit.text(), self.vprot_edit.text(), self.averages_edit.text(),
                            self.trigger_delay_edit.text(), self.traces_edit.text(), self.trace_pause_edit.text(),
                            self.cycles_edit.text(), self.cycle_pause_edit.text(), self.remote_sense_btn.isChecked(),
                            self.rear_terminal_btn.isChecked()]
        write_config()
