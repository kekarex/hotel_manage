"""
@file client_dialog.py
@brief Модуль, реализующий диалог для добавления нового клиента в систему.
"""

import sqlite3

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QMessageBox


class ClientDialog(QDialog):
    """
    @brief Диалог для добавления нового клиента.
    """
    def __init__(self, db):
        """
        @brief Инициализация диалога добавления клиента.
        @param db Экземпляр класса Database для работы с базой данных.
        """
        super().__init__()
        self.db = db  # Сохранение объекта базы данных
        self.setWindowTitle("Добавить клиента")
        self.setFixedSize(400, 300)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Поле для ФИО
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("ФИО клиента")
        form.addRow("ФИО:", self.full_name)

        # Поле для email
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        form.addRow("Email:", self.email)

        # Поле для телефона
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Телефон")
        form.addRow("Телефон:", self.phone)

        # Поле для заметок
        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Заметки о клиенте")
        form.addRow("Заметки:", self.notes)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_client)

        # Кнопка отмены
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def save_client(self):
        """
        @brief Сохранение данных о новом клиенте в базу данных.
        """
        full_name = self.full_name.text().strip()
        email = self.email.text().strip()
        phone = self.phone.text().strip()
        notes = self.notes.text().strip()

        if not all([full_name, email, phone]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
            return

        try:
            self.db.cursor.execute(
                """
                INSERT INTO clients (full_name, email, phone, notes)
                VALUES (?, ?, ?, ?)
                """,
                (full_name, email, phone, notes or None),
            )
            self.db.conn.commit()
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить клиента: {str(e)}")