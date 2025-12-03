"""
Custom image viewer widget with zoom and pan capabilities
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent
import numpy as np
from utils import numpy_to_qpixmap

class ImageViewer(QGraphicsView):
    """Custom image viewer with zoom and pan"""
    
    imageClicked = Signal(QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.pixmap_item = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
        # Enable dragging
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # Set rendering hints
        self.setRenderHint(self.renderHints())
        
        # Disable scrollbars (we'll use them when needed)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Background
        self.setBackgroundBrush(Qt.darkGray)
    
    def set_image(self, image: np.ndarray):
        """
        Set image to display
        
        Args:
            image: Numpy array image
        """
        # Clear scene
        self.scene.clear()
        
        # Convert to pixmap
        pixmap = numpy_to_qpixmap(image)
        
        # Add to scene
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # Reset zoom
        self.zoom_factor = 1.0
        self.fit_in_view()
    
    def set_pixmap(self, pixmap: QPixmap):
        """Set QPixmap to display"""
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.zoom_factor = 1.0
        self.fit_in_view()
    
    def fit_in_view(self):
        """Fit image in view"""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self.zoom_factor = 1.0
    
    def zoom_in(self):
        """Zoom in"""
        self.scale_view(1.25)
    
    def zoom_out(self):
        """Zoom out"""
        self.scale_view(0.8)
    
    def scale_view(self, factor: float):
        """Scale view by factor"""
        new_zoom = self.zoom_factor * factor
        
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return
        
        self.scale(factor, factor)
        self.zoom_factor = new_zoom
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.angleDelta().y() > 0:
            self.scale_view(1.15)
        else:
            self.scale_view(0.85)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.imageClicked.emit(scene_pos)
        super().mousePressEvent(event)
    
    def clear(self):
        """Clear the viewer"""
        self.scene.clear()
        self.pixmap_item = None
        self.zoom_factor = 1.0
