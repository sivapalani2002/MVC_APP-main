import sys
import os
import signal
import logging
import threading
import numpy as np
import cv2 as cv
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
from senxor.mi48 import MI48, format_header, format_framestats  # Connects and communicates with the MI48 thermal camera
from senxor.utils import data_to_frame, remap, cv_filter, RollingAverageFilter, connect_senxor

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def replace_dead_pixels(frame, min_val=0, max_val=200):
    """Replace dead pixels with the average of surrounding 48 pixels."""
    for i in range(3, frame.shape[0] - 3):
        for j in range(3, frame.shape[1] - 3):
            if frame[i, j] < min_val or frame[i, j] > max_val:
                surrounding_pixels = [
                    frame[i-3, j-3], frame[i-3, j-2], frame[i-3, j-1], frame[i-3, j], frame[i-3, j+1], frame[i-3, j+2], frame[i-3, j+3],  # top row
                    frame[i-2, j-3], frame[i-2, j-2], frame[i-2, j-1], frame[i-2, j], frame[i-2, j+1], frame[i-2, j+2], frame[i-2, j+3],  # second row
                    frame[i-1, j-3], frame[i-1, j-2], frame[i-1, j-1], frame[i-1, j], frame[i-1, j+1], frame[i-1, j+2], frame[i-1, j+3],  # third row
                    frame[i, j-3], frame[i, j-2], frame[i, j-1], frame[i, j+1], frame[i, j+2], frame[i, j+3],  # middle row (excluding center)
                    frame[i+1, j-3], frame[i+1, j-2], frame[i+1, j-1], frame[i+1, j], frame[i+1, j+1], frame[i+1, j+2], frame[i+1, j+3],  # fifth row
                    frame[i+2, j-3], frame[i+2, j-2], frame[i+2, j-1], frame[i+2, j], frame[i+2, j+1], frame[i+2, j+2], frame[i+2, j+3],  # sixth row
                    frame[i+3, j-3], frame[i+3, j-2], frame[i+3, j-1], frame[i+3, j], frame[i+3, j+1], frame[i+3, j+2], frame[i+3, j+3]   # bottom row
                ]
                frame[i, j] = np.mean(surrounding_pixels)
    return frame

class ThermalCamera(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, roi=(0, 0, 80, 80), com_port=None):
        """
        Initializes the thermal camera with a given ROI and optional COM port.
        Runs in a separate thread.
        """
        super().__init__()
        self.roi = roi    # (x1, y1, x2, y2) cam FOV crop
        self.com_port = com_port #cam com
        self.running = True
        self.latest_frame = None
        self.lock = threading.Lock()

        self.temps = {"Top": 0, "Bottom": 0, "Left": 0, "Right": 0, "Center": 0}

        # Connect to the MI48 camera. detects automatically 
        self.mi48, self.connected_port, _ = connect_senxor(src=self.com_port) if self.com_port else connect_senxor()

        logger.info(f"Camera initialized on {self.connected_port}")

        # Set camera parameters
        self.mi48.set_fps(25)                                                   # Set Frames Per Second (FPS)  15-->25
        self.mi48.disable_filter(f1=True, f2=True, f3=True)                     # Disable all filters
        self.mi48.set_filter_1(85)                                              # Set internal filter sett 1 to 85
        self.mi48.enable_filter(f1=True, f2=False, f3=False, f3_ks_5=False)
        self.mi48.set_offset_corr(0.0)                                          # Set offset correction to 0.0
        self.mi48.set_sens_factor(100)       # Set sensitivity factor to 100
        
        # Start streaming                                 
        self.mi48.start(stream=True, with_header=True)

        self.dminav = RollingAverageFilter(N=10)
        self.dmaxav = RollingAverageFilter(N=10)

    def run(self):
        """Runs the camera processing loop asynchronously."""
        while self.running:
            self.process_frame()

    def process_frame(self):
        """Processes a frame: crops ROI, calculates temperatures, overlays grid and text."""
        data, header = self.mi48.read()
        if data is None:
            logger.error("No data received from the camera.")
            return

        # Calculate min/max temperatures
        min_temp = self.dminav(data.min())
        max_temp = self.dmaxav(data.max())

        # Convert raw data to an image frame
        frame = data_to_frame(data, (80, 62), hflip=True)
        frame = np.clip(frame, min_temp, max_temp)

        # Replace dead pixels
        frame = replace_dead_pixels(frame)

        # Vertical flip and rotate
        #frame = cv.flip(frame, 1)
        frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)

        # Apply filters
        filt_frame = cv_filter(remap(frame), {'blur_ks': 3, 'd': 5, 'sigmaColor': 27, 'sigmaSpace': 27},  #Remaps temperature values for visualization
                               use_median=True, use_bilat=True, use_nlm=False)                            #Applies smoothing filters to reduce noise.

        # Crop to ROI
        x1, y1, x2, y2 = self.roi
        roi_frame = filt_frame[y1:y2, x1:x2]

        # Apply thermal color mapping
        roi_frame = cv.applyColorMap(roi_frame, cv.COLORMAP_INFERNO)

        # Resize the frame to make it larger
        roi_frame = cv.resize(roi_frame, (600, 600), interpolation=cv.INTER_LINEAR)

        # Draw the 3×3 grid
        self.draw_grid(roi_frame)

        # Calculate section temperatures
        temps = self.calculate_temperatures(frame, x1, y1, x2, y2)
        logger.debug(f"Section temperatures: {temps}")               #prints the section temperature

        # Overlay text on the image
        self.overlay_text(roi_frame, temps)

        # Store the latest frame for streaming
        with self.lock:
            self.latest_frame = roi_frame

        self.frame_ready.emit(roi_frame)

    def draw_grid(self, frame):
        """Draws a 3×3 grid overlay on the thermal feed."""
        h, w = frame.shape[:2]     # Get frame dimensions
        step_w, step_h = w // 3, h // 3    # Divide width and height into 3 sections to get 3x3 grid

        # Draw vertical lines
        for i in range(1, 3):
            x = i * step_w
            cv.line(frame, (x, 0), (x, h), (255, 255, 255), 1)

        # Draw horizontal lines
        for i in range(1, 3):
            y = i * step_h
            cv.line(frame, (0, y), (w, y), (255, 255, 255), 1)

    def calculate_temperatures(self, frame, x1, y1, x2, y2):
        """Calculates the average temperatures for 5 sections: Top, Bottom, Left, Right, Center."""
        w, h = x2 - x1, y2 - y1
        section_w, section_h = w // 3, h // 3   # Divide into 3x3 grid
        
        # Define sections
        sections = {
            "Top": frame[y1:y1+section_h, x1:x2],     # Top 3 squares
            "Bottom": frame[y2-section_h:y2, x1:x2],  # Bottom 3 squares
            "Left": frame[y1:y2, x1:x1+section_w],    # Left 3 squares
            "Right": frame[y1:y2, x2-section_w:x2],   # Right 3 squares
            "Center": frame[y1+section_h:y2-section_h, x1+section_w:x2-section_w]  # Center square
        }

        # Calculate average temperature for each section
        self.temps = {name: np.mean(region) for name, region in sections.items()}
        return self.temps
    
    def get_avg_temperatures(self):
        """Returns the latest average temperatures for the 5 zones."""
        return self.temps
    
    def overlay_text(self, frame, temps):
        """Overlays temperature values on the image."""
        h, w = frame.shape[:2]
        section_w, section_h = w // 3, h // 3   # Grid size

        # Set positions to display average temperature
        positions = {
            "Top": (w // 2 - 50, section_h // 2),
            "Bottom": (w // 2 - 50, h - section_h // 2),
            "Left": (section_w // 4, h // 2),
            "Right": (w - section_w // 2 - 50, h // 2),
            "Center": (w // 2 - 50, h // 2)
        }
        
        # Overlay text for each section
        for section, temp in temps.items():
            x, y = positions[section]
            cv.putText(frame, f"{temp:.2f}C", (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

    def stop(self):
        """Stops the camera."""
        self.running = False
        self.mi48.stop()
        cv.destroyAllWindows()

class ThermalCam(QWidget):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.thermal_camera = ThermalCamera()
        self.thermal_camera.frame_ready.connect(self.update_frame)
        self.thermal_camera.start()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.label = QLabel("Thermal Cam Feed")
        self.layout.addWidget(self.label)

        self.video_label = QLabel()
        self.layout.addWidget(self.video_label)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

        self.setLayout(self.layout)

    def update_frame(self, frame):
        logger.debug("Updating frame on UI")
        if frame is not None:
            logger.debug(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
            self.video_label.setPixmap(QPixmap.fromImage(image))
        else:
            logger.error("Received empty frame")

    def go_back(self):
        self.thermal_camera.stop()
        self.main_window.setCentralWidget(self.main_window.home_screen)

    def closeEvent(self, event):
        self.thermal_camera.stop()
        event.accept()

# **Main Execution**
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    thermal_cam = ThermalCam(main_window, main_window)
    layout.addWidget(thermal_cam)
    main_window.setLayout(layout)
    main_window.show()
    sys.exit(app.exec_())
