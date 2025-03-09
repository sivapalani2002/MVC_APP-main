from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage, QPixmap
from ui.feed.thermal_cam import ThermalCam
from ui.feed.rgb_cam import RGBCam
from ui.heater_controll.heater_control import HeaterControl
from ui.feed.thermal_cam import ThermalCamera

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SLS Camera Feed")
        self.setGeometry(100, 100, 800, 600)  # Set the window size to 800x600 (x,y width x height)
        self.setStyleSheet("background-color: black;")  # Set the background color to red
        
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
        self.thermal_cam_widget = QWidget()
        thermal_layout = QVBoxLayout()

        self.label = QLabel("Thermal Cam Feed")
        thermal_layout.addWidget(self.label)

        self.video_label = QLabel()
        thermal_layout.addWidget(self.video_label)

        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("http://localhost:5000/video_feed"))
        thermal_layout.addWidget(self.web_view)

        self.thermal_cam_widget.setLayout(thermal_layout)
        self.layout.addWidget(self.thermal_cam_widget)

        # Start the thermal camera
        self.thermal_camera = ThermalCamera()
        self.thermal_camera.frame_ready.connect(self.update_frame)
        self.thermal_camera.start()
        self.thermal_camera.start_stream()

    def update_frame(self, frame):
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB32)
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def show_rgb_cam(self):
        print("RGB feed button clicked")
        self.main_window.switch_screen(RGBCam(self.main_window, self.main_window))

    def show_heater_control(self):
        print("Heater Control button clicked")
        self.main_window.switch_screen(HeaterControl(self.main_window, self.main_window))