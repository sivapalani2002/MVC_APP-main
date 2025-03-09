import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()

    # 9-3-25 sunday