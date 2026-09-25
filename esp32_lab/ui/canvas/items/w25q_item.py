from PySide6.QtWidgets import QGraphicsObject, QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF
from .pin_item import PinAnchorItem

class W25QItem(QGraphicsObject):
    def __init__(self, component_id: str, variant="W25Q32", parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.variant = variant
        
        self.setFlag(QGraphicsObject.ItemIsMovable)
        self.setFlag(QGraphicsObject.ItemIsSelectable)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges)
        
        self.width = 40
        self.height = 30
        
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC", parent=self)
        self.pin_vcc.setPos(-20, 15)
        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(-10, 15)
        self.pin_cs = PinAnchorItem(component_id, "cs", "CS", parent=self)
        self.pin_cs.setPos(0, 15)
        self.pin_sck = PinAnchorItem(component_id, "sck", "CLK", parent=self)
        self.pin_sck.setPos(10, 15)
        self.pin_miso = PinAnchorItem(component_id, "miso", "DO", parent=self)
        self.pin_miso.setPos(20, 15)
        self.pin_mosi = PinAnchorItem(component_id, "mosi", "DI", parent=self)
        self.pin_mosi.setPos(30, 15)
        
    def boundingRect(self) -> QRectF:
        return QRectF(-25, -15, 60, 35)
        
    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.setPen(QPen(Qt.black))
        painter.drawRect(-25, -15, 60, 30)
        
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 6, QFont.Bold))
        painter.drawText(QRectF(-25, -15, 60, 15), Qt.AlignCenter, self.variant)
        
        painter.setFont(QFont("Arial", 4))
        painter.drawText(QRectF(-22, 0, 10, 10), Qt.AlignCenter, "VCC")
        painter.drawText(QRectF(-12, 0, 10, 10), Qt.AlignCenter, "GND")
        painter.drawText(QRectF(-2, 0, 10, 10), Qt.AlignCenter, "CS")
        painter.drawText(QRectF(8, 0, 10, 10), Qt.AlignCenter, "CLK")
        painter.drawText(QRectF(18, 0, 10, 10), Qt.AlignCenter, "DO")
        painter.drawText(QRectF(28, 0, 10, 10), Qt.AlignCenter, "DI")
