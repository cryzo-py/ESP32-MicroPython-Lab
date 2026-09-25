"""
Virtual UART Terminal item for UI
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QInputDialog
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF

from .pin_item import PinAnchorItem

class UARTTerminalItem(QGraphicsItem):
    def __init__(self, comp_id: str, scene=None):
        super().__init__()
        self.component_id = comp_id  # FIX: utiliser component_id (pas comp_id)
        self.circuit_scene = scene
        
        # Dimensions
        self.width = 160
        self.height = 100
        
        # Drawing
        self.rect_item = QGraphicsRectItem(0, 0, self.width, self.height, self)
        self.rect_item.setBrush(QBrush(QColor("#1e293b")))
        self.rect_item.setPen(QPen(QColor("#334155"), 2))
        
        # Title
        self.title = QGraphicsTextItem("UART Terminal", self)
        self.title.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Consolas", 10, QFont.Bold)
        self.title.setFont(font)
        self.title.setPos(5, 5)

        # Content Text
        self.text_item = QGraphicsTextItem("RX Buffer: [Empty]", self)
        self.text_item.setDefaultTextColor(QColor("#10b981"))  # Green text
        self.text_item.setFont(QFont("Consolas", 8))
        self.text_item.setPos(5, 30)
        self.text_item.setTextWidth(self.width - 10)
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # Create pins (VCC, GND, TX, RX)
        self.pins = {}
        
        pin_spacing = 20
        start_x = (self.width - (pin_spacing * 3)) / 2

        pin_configs = [
            ("VCC", "#ef4444"),
            ("GND", "#000000"),
            ("TX", "#eab308"),  # Output from terminal, to ESP RX
            ("RX", "#3b82f6")   # Input to terminal, from ESP TX
        ]
        
        for i, (name, color) in enumerate(pin_configs):
            x = start_x + (i * pin_spacing)
            y = self.height
            pin = PinAnchorItem(self.component_id, name, self)  # FIX: args corrects
            pin.setPos(x, y)
            # FIX: PinAnchorItem n'a pas de set_color — on ne l'appelle pas
            self.pins[name] = pin

        self.received_data = bytearray()

    def boundingRect(self):
        return QRectF(-5, -5, self.width + 10, self.height + 15)

    def paint(self, painter, option, widget=None):  # FIX: widget=None
        if self.isSelected():
            painter.setPen(QPen(QColor("#3b82f6"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_from_model(self, model):
        """Update terminal UI state from the device model."""
        if hasattr(model, 'rx_buffer'):
            buf = list(model.rx_buffer)
            if buf:
                # Keep last 50 chars for display
                try:
                    text = b"".join(buf[-50:]).decode('utf-8', 'replace')
                    text = text.replace('\r', '').replace('\n', '⏎')
                except Exception:
                    text = "<binary>"
                self.text_item.setPlainText(f"RX: {text}")
            else:
                self.text_item.setPlainText("RX Buffer: [Empty]")

    def get_pins(self):
        return list(self.pins.values())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.circuit_scene:
            if hasattr(self.circuit_scene, 'update_all_wires'):
                self.circuit_scene.update_all_wires()  # FIX: bon nom de méthode
        return super().itemChange(change, value)
        
    def contextMenuEvent(self, event):
        """Double right click or similar to inject TX data."""
        # Simple input dialog could be opened from a UI signal, 
        # but for simplicity we rely on the main window action or just provide the method.
        super().contextMenuEvent(event)
