from PyQt5.QtWidgets import QDialog, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QMessageBox


class RoomStatusDialog(QDialog):
    """Диалог для изменения статуса номера."""

    def __init__(self, current_status):
        """Инициализация диалога изменения статуса номера."""
        super().__init__()
        self.setWindowTitle('Изменить статус номера')
        self.setFixedSize(300, 200)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Выбор нового статуса
        self.status = QComboBox()
        self.status.addItems(['available', 'occupied', 'cleaning', 'maintenance'])
        self.status.setCurrentText(current_status)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton('Сохранить')
        btn_save.clicked.connect(self.accept)

        # Кнопка отмены
        btn_cancel = QPushButton('Отмена')
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_selected_status(self):
        """Получение выбранного статуса."""
        return self.status.currentText()