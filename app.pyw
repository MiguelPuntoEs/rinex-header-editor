import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtCore import QThread, pyqtSignal, Qt

import parse
from PyQt6.QtWidgets import QApplication, QCompleter, QProgressDialog, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QHBoxLayout, \
    QPushButton, QComboBox

import json
import os


class ReadThread(QThread):
    read_complete = pyqtSignal(dict)

    def __init__(self, file):
        super(ReadThread, self).__init__()
        self.file = file

    def run(self):
        with open(self.file, 'r') as f:
            data = f.readlines()
            header, body = parse_RINEX(data)

            rinex_header = parse_header(header)

        self.read_complete.emit(
            {'header': header, 'body': body, 'rinex_header': rinex_header})


class WriteThread(QThread):
    write_complete = pyqtSignal()

    def __init__(self, file, header, body):
        super(WriteThread, self).__init__()
        self.file = file
        self.header = header
        self.body = body

    def run(self):

        create_backup = False

        if create_backup:
            self.file.rename(self.file.with_suffix('.bak'))

        with open(self.file, 'w') as f:
            f.writelines(self.header)
            f.writelines(self.body)

        self.write_complete.emit()


def formatApproxPosition(x, y, z):
    return f'{x:14.4f}{y:14.4f}{z:14.4f}                  APPROX POSITION XYZ\n'


def get_antenna_IGS_code(antenna):
    antenna = ' '.join(antenna.split())
    parts = antenna.split(' ')
    if len(parts) == 1:
        antenna_type = f'{parts[0]:20}'
    else:
        antenna_type = parts[0] + \
            (' ' * (20 - len(parts[0]) - len(parts[1]))) + parts[1]
    return antenna_type


@dataclass
class RINEX_Header:
    marker_name: str = ''
    marker_type: str = ''
    receiver_sn: str = ''
    receiver_type: str = ''
    receiver_version: str = ''
    antenna_sn: str = ''
    antenna_type: str = ''
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0


def parse_header(header):
    rinex_header = RINEX_Header()
    for line in header:
        if line[60:] == 'REC # / TYPE / VERS\n':
            fmt = '{:20}{:20}{:20}REC # / TYPE / VERS\n'
            receiver_sn, receiver_type, receiver_version = parse.parse(
                fmt, line)

            rinex_header.receiver_sn = receiver_sn.rstrip()
            rinex_header.receiver_type = receiver_type.rstrip()
            rinex_header.receiver_version = receiver_version.rstrip()
        elif line[60:] == 'ANT # / TYPE\n':
            fmt = '{:20}{:20}                    ANT # / TYPE\n'
            antenna_sn, antenna_type = parse.parse(fmt, line)

            rinex_header.antenna_sn = antenna_sn.rstrip()
            rinex_header.antenna_type = antenna_type.rstrip()
        elif line[60:] == 'APPROX POSITION XYZ\n':
            fmt = '{:14.4f}{:14.4f}{:14.4f}                  APPROX POSITION XYZ\n'
            rinex_header.position_x, rinex_header.position_y, rinex_header.position_z = parse.parse(
                fmt, line)
        elif line[60:] == 'MARKER NAME\n':
            fmt = '{:60}MARKER NAME\n'
            marker_name, *_ = parse.parse(fmt, line)
            rinex_header.marker_name = marker_name.rstrip()
        elif line[60:] == 'MARKER TYPE\n':
            fmt = '{:60}MARKER TYPE\n'
            marker_type, *_ = parse.parse(fmt, line)
            rinex_header.marker_type = marker_type.rstrip()

    return rinex_header


def parse_RINEX(data):
    header_complete = False
    header_ = []
    body_ = []

    for line in data:
        line = line.rstrip() + '\n'

        if not header_complete:
            header_.append(line)
            if line[60:] == 'END OF HEADER\n':
                header_complete = True
        else:
            body_.append(line)

    return header_, body_


def modify_header(header_, rinex_header_: RINEX_Header):
    for idx, line in enumerate(header_):
        if line[60:] == 'REC # / TYPE / VERS\n':
            header_[idx] = f'{rinex_header_.receiver_sn:20}{rinex_header_.receiver_type:20}' \
                f'{rinex_header_.receiver_version:20}REC # / TYPE / VERS\n'
        elif line[60:] == 'ANT # / TYPE\n':
            antenna_type = get_antenna_IGS_code(rinex_header_.antenna_type)

            header_[idx] = f'{rinex_header_.antenna_sn:<20}{antenna_type:20}                    ANT # / ' \
                f'TYPE\n'
        elif line[60:] == 'APPROX POSITION XYZ\n':
            header_[idx] = f'{rinex_header_.position_x:14.4f}{rinex_header_.position_y:14.4f}' \
                f'{rinex_header_.position_z:14.4f}                  APPROX POSITION XYZ\n'
        # elif line[60:] == 'RINEX VERSION / TYPE\n':
        #     header_[idx] = '     3.02           OBSERVATION DATA    M: MIXED            RINEX VERSION / TYPE\n'
        elif line[60:] == 'MARKER NAME\n':
            header_[idx] = f'{rinex_header_.marker_name:60}MARKER NAME\n'
        elif line[60:] == 'MARKER TYPE\n':
            header_[idx] = f'{rinex_header_.marker_type:60}MARKER TYPE\n'
        elif line[60:] == 'PRN / # OF OBS\n':
            header_[idx] = ''
        elif line[60:] == '# OF SATELLITES\n' in line:
            header_[idx] = ''


class App(QWidget):
    def __init__(self):
        super(App, self).__init__()

        self.title = 'RINEX Header Editor'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 480

        self.setAcceptDrops(True)

        self.initSettings()
        self.initUI()

    def read_rinex_file(self):
        self.progress_dialog = QProgressDialog(None, None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle('Load RINEX file')
        self.progress_dialog.setLabelText('Reading file...')
        self.progress_dialog.show()

        self.thread = ReadThread(self.file)
        self.thread.read_complete.connect(self.evt_readthread_completed)
        self.thread.start()

    def write_rinex_file(self):
        self.progress_dialog = QProgressDialog(None, None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle('Write RINEX file')
        self.progress_dialog.setLabelText('Writing file...')
        self.progress_dialog.show()

        rinex_header = self.get_info_from_view()

        modify_header(self.header, rinex_header)

        self.thread = WriteThread(self.file, self.header, self.body)
        self.thread.write_complete.connect(self.evt_writethread_completed)
        self.thread.start()

    def enable_fields(self):
        self.qle_marker_name.setReadOnly(False)
        self.qle_marker_type.setReadOnly(False)

        self.qle_receiver_sn.setReadOnly(False)
        self.qle_receiver_type.setReadOnly(False)
        self.qle_receiver_version.setReadOnly(False)

        self.qle_antenna_sn.setReadOnly(False)
        self.qle_antenna_type.setReadOnly(False)

        self.qle_position_x.setReadOnly(False)
        self.qle_position_y.setReadOnly(False)
        self.qle_position_z.setReadOnly(False)

    def disable_fields(self):
        self.qle_marker_name.setReadOnly(True)
        self.qle_marker_type.setReadOnly(True)

        self.qle_receiver_sn.setReadOnly(True)
        self.qle_receiver_type.setReadOnly(True)
        self.qle_receiver_version.setReadOnly(True)

        self.qle_antenna_sn.setReadOnly(True)
        self.qle_antenna_type.setReadOnly(True)

        self.qle_position_x.setReadOnly(True)
        self.qle_position_y.setReadOnly(True)
        self.qle_position_z.setReadOnly(True)

    def populate(self, rinex_header: RINEX_Header):
        self.qle_marker_name.setText(rinex_header.marker_name)
        self.qle_marker_type.setText(rinex_header.marker_type)

        self.qle_receiver_sn.setText(rinex_header.receiver_sn)
        self.qle_receiver_type.setText(rinex_header.receiver_type)
        self.qle_receiver_version.setText(rinex_header.receiver_version)

        self.qle_antenna_sn.setText(rinex_header.antenna_sn)
        self.qle_antenna_type.setText(rinex_header.antenna_type)

        self.qle_position_x.setText(f'{rinex_header.position_x:.4f}')
        self.qle_position_y.setText(f'{rinex_header.position_y:.4f}')
        self.qle_position_z.setText(f'{rinex_header.position_z:.4f}')

    def get_info_from_view(self):
        rinex_header = RINEX_Header()
        rinex_header.marker_name = self.qle_marker_name.text()
        rinex_header.marker_type = self.qle_marker_type.text()

        rinex_header.receiver_sn = self.qle_receiver_sn.text()
        rinex_header.receiver_type = self.qle_receiver_type.text()
        rinex_header.receiver_version = self.qle_receiver_version.text()

        rinex_header.antenna_sn = self.qle_antenna_sn.text()
        rinex_header.antenna_type = self.qle_antenna_type.text()

        rinex_header.position_x = float(self.qle_position_x.text())
        rinex_header.position_y = float(self.qle_position_y.text())
        rinex_header.position_z = float(self.qle_position_z.text())

        return rinex_header

    def set_marker(self):
        if self.cb_marker.currentText():

            marker = self.cb_marker.currentText()

            self.qle_marker_name.setText(marker)
            self.qle_marker_type.setText('GEODETIC')

            coords = self.settings['coordinates'][marker]

            self.qle_position_x.setText(f'{coords[0]:.4f}')
            self.qle_position_y.setText(f'{coords[1]:.4f}')
            self.qle_position_z.setText(f'{coords[2]:.4f}')

    def initSettings(self):

        with open(Path(__file__).parent / 'settings.json') as f:
            self.settings = json.load(f)

    def initUI(self):
        self.setWindowTitle(self.title)

        self.setGeometry(self.left, self.top, self.width, self.height)

        main_layout = QVBoxLayout()

        self.qle_marker_name = QLineEdit()

        marker_type_completer = QCompleter(['GEODETIC', 'NON_GEODETIC'])
        marker_type_completer.setCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.qle_marker_type = QLineEdit()
        self.qle_marker_type.setCompleter(marker_type_completer)

        self.qle_receiver_sn = QLineEdit()

        receiver_completer = QCompleter(self.settings['receivers'])
        receiver_completer.setCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.qle_receiver_type = QLineEdit()
        self.qle_receiver_type.setCompleter(receiver_completer)

        self.qle_receiver_version = QLineEdit()

        self.qle_antenna_sn = QLineEdit()

        antenna_completer = QCompleter(self.settings['antennas'])
        antenna_completer.setCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.qle_antenna_type = QLineEdit()
        self.qle_antenna_type.setCompleter(antenna_completer)

        self.qle_position_x = QLineEdit()
        self.qle_position_y = QLineEdit()
        self.qle_position_z = QLineEdit()

        self.cb_marker = QComboBox()
        self.cb_marker.addItems(self.settings['coordinates'].keys())
        self.cb_marker.setCurrentIndex(0)
        # print(self.cb_marker.geometry())
        # self.cb_marker.setFixedWidth(100)

        btn_apply_marker = QPushButton('Apply')
        btn_apply_marker.clicked.connect(self.set_marker)

        form_layout = QFormLayout()
        form_layout.addRow(QLabel('Marker name'), self.qle_marker_name)
        form_layout.addRow(QLabel('Marker type'), self.qle_marker_type)

        form_layout.addRow(QLabel('Receiver S/N'), self.qle_receiver_sn)
        form_layout.addRow(QLabel('Receiver Type'), self.qle_receiver_type)
        form_layout.addRow(QLabel('Receiver Version'),
                           self.qle_receiver_version)

        form_layout.addRow(QLabel('Antenna S/N'), self.qle_antenna_sn)
        form_layout.addRow(QLabel('Antenna Type'), self.qle_antenna_type)

        form_layout.addRow(QLabel('Antenna X'), self.qle_position_x)
        form_layout.addRow(QLabel('Antenna Y'), self.qle_position_y)
        form_layout.addRow(QLabel('Antenna Z'), self.qle_position_z)

        form_layout.addRow(self.cb_marker, btn_apply_marker)

        btn_read_rinex = QPushButton('Read')
        btn_read_rinex.clicked.connect(self.read_rinex_file)

        btn_write_rinex = QPushButton('Write')
        btn_write_rinex.clicked.connect(self.write_rinex_file)

        h_layout = QHBoxLayout()
        h_layout.addWidget(btn_read_rinex)
        h_layout.addWidget(btn_write_rinex)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(h_layout)

        self.disable_fields()

        self.setLayout(main_layout)
        self.show()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    #
    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
            for url in e.mimeData().urls():
                fname = str(url.toLocalFile())

                self.file = Path(fname)
                self.read_rinex_file()
        else:
            e.ignore()

    def evt_readthread_completed(self, emp):
        self.header = emp['header']
        self.body = emp['body']
        self.populate(emp['rinex_header'])
        self.progress_dialog.hide()
        self.enable_fields()

    def evt_writethread_completed(self):
        self.progress_dialog.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
