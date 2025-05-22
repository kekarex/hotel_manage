"""
@file room_dialog.py
@brief Модуль, реализующий диалог для добавления нового номера в систему.
"""

import sqlite3

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QMessageBox


class RoomDialog(QDialog):
    """
    @brief Диалог для добавления нового номера.
    """
    def __init__(self, db):
        """
        @brief Инициализация диалога добавления номера.
        @param db Экземпляр класса Database для работы с базой данных.
        """
        super().__init__()
        self.db = db  # Сохранение объекта базы данных
        self.setWindowTitle("Добавить новый номер")
        self.setFixedSize(400, 400)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Поле для номера комнаты
        self.room_number = QLineEdit()
        self.room_number.setPlaceholderText("Номер комнаты")
        form.addRow("Номер:", self.room_number)

        # Выбор типа номера
        self.room_type = QComboBox()
        self.room_type.addItems(["Эконом", "Стандарт", "Люкс", "Апартаменты"])
        form.addRow("Тип:", self.room_type)

        # Поле для этажа
        self.floor = QSpinBox()
        self.floor.setRange(1, 20)
        form.addRow("Этаж:", self.floor)

        # Поле для вместимости
        self.capacity = QSpinBox()
        self.capacity.setRange(1, 10)
        form.addRow("Вместимость:", self.capacity)

        # Поле для цены за ночь
        self.price_per_night = QLineEdit()
        self.price_per_night.setPlaceholderText("Цена за ночь")
        form.addRow("Цена за ночь:", self.price_per_night)

        # Поле для описания
        self.description = QLineEdit()
        self.description.setPlaceholderText("Описание номера")
        form.addRow("Описание:", self.description)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_room)

        # Кнопка отмены
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def save_room(self):
        """
        @brief Сохранение данных о новом номере в базу данных.
        """
        number = self.room_number.text().strip()
        room_type = self.room_type.currentText()
        floor = self.floor.value()
        capacity = self.capacity.value()
        price = self.price_per_night.text().strip()
        description = self.description.text().strip()

        if not all([number, price]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
            return

        try:
            price = float(price)
            self.db.cursor.execute(
                """
                INSERT INTO rooms (number, type, floor, capacity,
                                   price_per_night, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (number, room_type, floor, capacity, price, description or None),
            )
            self.db.conn.commit()
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Цена должна быть числом")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить номер: {str(e)}")