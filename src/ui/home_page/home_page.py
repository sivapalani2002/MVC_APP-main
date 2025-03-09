from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage, QPixmap
from ui.feed.thermal_cam import ThermalCam
from ui.feed.rgb_cam import RGBCam
from ui.heater_controll.heater_control import HeaterControl
from ui.feed.thermal_cam import ThermalCamera
import logging

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SLS Camera Feed")
        self.setGeometry(100, 100, 800, 600)  # Set the window size to 800x600 (x,y width x height)
        self.setStyleSheet("background-color: black;")  # Set the background color to black
        
        self.layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        self.rgb_button = QPushButton("RGB Feed")
        self.thermal_button = QPushButton("Thermal Feed")
        self.serial_button = QPushButton("Heater Control")

        # Make the buttons square
        button_size = QSize(200, 200)
        self.rgb_button.setFixedSize(button_size)
        self.thermal_button.setFixedSize(button_size)
        self.serial_button.setFixedSize(button_size)

        # Change button colors
        self.rgb_button.setStyleSheet("background-color: grey; color: black;")
        self.thermal_button.setStyleSheet("background-color: grey; color: black;")
        self.serial_button.setStyleSheet("background-color: grey; color: black;")

        button_layout.addWidget(self.rgb_button)
        button_layout.addWidget(self.thermal_button)
        button_layout.addWidget(self.serial_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

        # Connect buttons to their respective methods
        self.rgb_button.clicked.connect(self.show_rgb_cam)
        self.thermal_button.clicked.connect(self.start_thermal_feed)
        self.serial_button.clicked.connect(self.show_heater_control)

    def start_thermal_feed(self):
        # Remove existing thermal feed widget if it exists
        if hasattr(self, 'thermal_cam_widget'):
            self.layout.removeWidget(self.thermal_cam_widget)
            self.thermal_cam_widget.deleteLater()

        # Create and add the thermal feed widget
        self.thermal_cam_widget = ThermalCam(self, self.main_window)
        self.layout.addWidget(self.thermal_cam_widget)

    def update_frame(self, frame):
        logger.debug("Updating frame on UI")
        if frame is not None:
            logger.debug(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
            self.video_label.setPixmap(QPixmap.fromImage(image))
        else:
            logger.error("Received empty frame")

    def show_rgb_cam(self):
        print("RGB feed button clicked")
        self.main_window.switch_screen(RGBCam(self.main_window, self.main_window))

    def show_heater_control(self):
        print("Heater Control button clicked")
        self.main_window.switch_screen(HeaterControl(self.main_window, self.main_window))