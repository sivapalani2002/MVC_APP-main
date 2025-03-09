from PyQt5.QtWidgets import QMainWindow
from ui.home_page.home_page import HomeScreen
#from ui.feed.thermal_cam import ThermalCamera
#from ui.feed.thermal_cam import ThermalCam

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Printer App")
        self.setGeometry(100, 100, 800, 600)
        self.home_screen = HomeScreen(self)
        self.setCentralWidget(self.home_screen)

    def switch_screen(self, new_screen):
        self.setCentralWidget(new_screen)