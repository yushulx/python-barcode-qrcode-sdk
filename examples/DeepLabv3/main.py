"""
Document Detection Application
Main entry point
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from main_window import MainWindow
from utils import get_logger

logger = get_logger(__name__)

def main():
    """Main application entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Document Detection")
    app.setOrganizationName("DeepLabV3")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("Application started")
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
