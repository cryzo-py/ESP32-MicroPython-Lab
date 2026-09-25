from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLabel, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor

class ExerciseBrowser(QWidget):
    exercise_selected = Signal(str)  # Émet l'ID de l'exercice sélectionné
    
    def __init__(self, catalog, controller, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.controller = controller
        self._setup_ui()
        self.refresh_catalog()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        title = QLabel("🎓 Travaux Pratiques")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        layout.addWidget(title)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(10)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
        
    def refresh_catalog(self):
        self.tree.clear()
        exercises = self.catalog.get_available_exercises()
        
        root = QTreeWidgetItem(self.tree, ["Tous les Exercices"])
        root.setExpanded(True)
        
        for ex in exercises:
            state_icon = "▶"
            is_locked = False
            
            if not self.controller.is_unlocked(ex.id):
                state_icon = "🔒"
                is_locked = True
            elif self.controller.is_mastered(ex.id):
                state_icon = "✓"
                
            display_text = f"{state_icon} {ex.title}"
            item = QTreeWidgetItem(root, [display_text])
            item.setData(0, Qt.UserRole, ex.id)
            
            if is_locked:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                item.setForeground(0, QColor("#666666"))
            elif state_icon == "✓":
                item.setForeground(0, QColor("#10b981"))  # Green
                
    def _on_item_clicked(self, item, column):
        ex_id = item.data(0, Qt.UserRole)
        if ex_id:
            self.exercise_selected.emit(ex_id)
