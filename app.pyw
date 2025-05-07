import sys
from pathlib import Path
import typing
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from PyQt6.QtWidgets import QApplication, QCompleter, QProgressDialog, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QHBoxLayout, \
    QPushButton, QComboBox

import json
from utils.rinex import parse_header, parse_RINEX, modify_header, RINEX_Header


class ReadThread(QThread):
    read_complete = pyqtSignal(dict)

    def __init__(self, file):
        super(ReadThread, self).__init__()
        self.file = file

    def run(self):
        with open(self.file, 'r') as f:
            lines: list[str] = f.readlines()

            header: list[str]
            body: list[str]
            header, body = parse_RINEX(lines)

            rinex_header: RINEX_Header = parse_header(header)

        self.read_complete.emit(
            {'header': header, 'body': body, 'rinex_header': rinex_header})


class WriteThread(QThread):
    write_complete = pyqtSignal()

    def __init__(self, file: Path, header: list[str], body: list[str]) -> None:
        super(WriteThread, self).__init__()
        self.file = file
        self.header = header
        self.body = body

    def run(self) -> None:

        create_backup = False

        if create_backup:
            self.file.rename(self.file.with_suffix('.bak'))

        with open(self.file, 'w') as f:
            f.writelines(self.header)
            f.writelines(self.body)

        self.write_complete.emit()


class App(QWidget):
    def __init__(self) -> None:
        super(App, self).__init__()

        self.title = 'RINEX Header Editor'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 480

        self.setAcceptDrops(True)

        self.initSettings()
        self.initUI()

    def read_rinex_file(self) -> None:
        self.progress_dialog = QProgressDialog(None, None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle('Load RINEX file')
        self.progress_dialog.setLabelText('Reading file...')
        self.progress_dialog.show()

        self.thread = ReadThread(self.file)
        self.thread.read_complete.connect(self.evt_readthread_completed)
        self.thread.start()

    def write_rinex_file(self) -> None:
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

    def enable_fields(self) -> None:
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

    def disable_fields(self) -> None:
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

    def populate(self, rinex_header: RINEX_Header) -> None:
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

    def get_info_from_view(self) -> RINEX_Header:
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

    def set_marker(self) -> None:
        if self.cb_marker.currentText():

            marker = self.cb_marker.currentText()

            self.qle_marker_name.setText(marker)
            self.qle_marker_type.setText('GEODETIC')

            coords = self.settings['coordinates'][marker]

            self.qle_position_x.setText(f'{coords[0]:.4f}')
            self.qle_position_y.setText(f'{coords[1]:.4f}')
            self.qle_position_z.setText(f'{coords[2]:.4f}')

    def initSettings(self) -> None:

        with open(Path(__file__).parent / 'settings.json') as f:
            self.settings = json.load(f)

    def initUI(self) -> None:
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

    def dragEnterEvent(self, e: typing.Optional[QtGui.QDragEnterEvent]):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e: typing.Optional[QtGui.QDragMoveEvent]):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e: typing.Optional[QtGui.QDropEvent]):
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
