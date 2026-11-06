from PyQt6.QtWidgets import QLineEdit, QToolButton
from PyQt6.QtCore import Qt
import qtawesome as qta

class PasswordInput(QLineEdit):
    def __init__(self, placeholder="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText(placeholder)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_eye = QToolButton(self)
        self.btn_eye.setIcon(qta.icon('fa5s.eye', color='#cdd6f4'))
        self.btn_eye.setStyleSheet("border: none; background: transparent; padding: 0;")
        self.btn_eye.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_eye.pressed.connect(self.show_password)
        self.btn_eye.released.connect(self.hide_password)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Manter o botão alinhado à direita
        btn_width = 30
        self.btn_eye.resize(btn_width, self.height())
        self.btn_eye.move(self.width() - btn_width - 5, 0)
        
    def show_password(self):
        self.setEchoMode(QLineEdit.EchoMode.Normal)
        self.btn_eye.setIcon(qta.icon('fa5s.eye-slash', color='#cdd6f4'))
        
    def hide_password(self):
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_eye.setIcon(qta.icon('fa5s.eye', color='#cdd6f4'))
