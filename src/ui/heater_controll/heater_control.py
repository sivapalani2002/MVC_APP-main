from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpinBox, QLabel
from model.serial_model import SerialModel

class HeaterControl(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.serial_model = SerialModel(port="COM19", baudrate=115200, timeout=1)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.label = QLabel("Set Temperature (0-100%)")
        self.layout.addWidget(self.label)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 100)
        self.layout.addWidget(self.spin_box)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_heater)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_heater)
        self.layout.addWidget(self.stop_button)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

        self.setLayout(self.layout)

    def start_heater(self):
        temperature = self.spin_box.value()
        command = f"8,{temperature},{temperature},{temperature},{temperature},{temperature},{temperature},{temperature},{temperature}"
        self.serial_model.send_command(command)
        print(f"Heater started at {temperature}%")

    def stop_heater(self):
        command = "8,1,1,1,1,1,1,1,1"
        self.serial_model.send_command(command)
        print("Heater stopped")

    def go_back(self):
        self.main_window.setCentralWidget(self.main_window.home_screen)

    def closeEvent(self, event):
        self.serial_model.close()
        event.accept()