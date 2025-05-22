"""
@file room_status_dialog.py
@brief Модуль, реализующий диалог для изменения статуса номера.
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMessageBox


class RoomStatusDialog(QDialog):
    """
    @brief Диалог для изменения статуса номера.
    """
    def __init__(self, current_status):
        """
        @brief Инициализация диалога изменения статуса номера.
        @param current_status Текущий статус номера (например, 'available',
                              'occupied').
        """
        super().__init__()
        self.setWindowTitle("Изменить статус номера")
        self.setFixedSize(300, 200)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Выбор нового статуса
        self.status = QComboBox()
        self.status.addItems(["available", "occupied", "cleaning", "maintenance"])
        self.status.setCurrentText(current_status)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.accept)

        # Кнопка отмены
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_selected_status(self):
        """
        @brief Получение выбранного статуса номера.
        @return str Новый статус номера.
        """
        return self.status.currentText()