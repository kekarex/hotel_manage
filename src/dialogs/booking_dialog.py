import sqlite3
import re
from PyQt5.QtWidgets import QDialog, QLineEdit, QComboBox, QDateEdit, QSpinBox, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox
from PyQt5.QtCore import QDate
from src.database import Database


class BookingDialog(QDialog):
    """Диалог для создания или редактирования бронирования."""

    def __init__(self, db, booking=None, user_id=None):
        """Инициализация диалога бронирования."""
        super().__init__()
        self.db = db  # Используем переданный экземпляр Database
        self.booking = booking  # Сохранение данных бронирования (если редактирование)
        self.user_id = user_id if user_id else 1  # ID пользователя, создающего бронирование
        self.setWindowTitle('Новое бронирование' if not booking else 'Редактирование бронирования')
        self.setFixedSize(500, 500)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Поле для ФИО гостя
        self.guest_name = QLineEdit()
        self.guest_name.setPlaceholderText('ФИО гостя')
        form.addRow('ФИО гостя:', self.guest_name)

        # Поле для телефона
        self.guest_phone = QLineEdit()
        self.guest_phone.setPlaceholderText('Телефон (+79991234567)')
        form.addRow('Телефон:', self.guest_phone)

        # Поле для email
        self.guest_email = QLineEdit()
        self.guest_email.setPlaceholderText('Email (example@domain.com)')
        form.addRow('Email:', self.guest_email)

        # Поле для даты заезда
        self.check_in = QDateEdit(calendarPopup=True)
        self.check_in.setDate(QDate.currentDate())
        self.check_in.dateChanged.connect(self.load_available_rooms)
        form.addRow('Дата заезда:', self.check_in)

        # Поле для даты выезда
        self.check_out = QDateEdit(calendarPopup=True)
        self.check_out.setDate(QDate.currentDate().addDays(1))
        self.check_out.dateChanged.connect(self.load_available_rooms)
        form.addRow('Дата выезда:', self.check_out)

        # Поле для количества взрослых
        self.adults = QSpinBox()
        self.adults.setRange(1, 10)
        form.addRow('Взрослых:', self.adults)

        # Поле для количества детей
        self.children = QSpinBox()
        self.children.setRange(0, 5)
        form.addRow('Детей:', self.children)

        # Выбор типа номера
        self.room_type = QComboBox()
        self.room_type.addItems(['Эконом', 'Стандарт', 'Люкс', 'Апартаменты'])
        self.room_type.currentTextChanged.connect(self.load_available_rooms)
        form.addRow('Тип номера:', self.room_type)

        # Выбор номера
        self.room_number = QComboBox()
        form.addRow('Номер:', self.room_number)

        # Выбор статуса
        self.status = QComboBox()
        self.status.addItems(['reserved', 'checked_in', 'checked_out', 'cancelled'])
        form.addRow('Статус:', self.status)

        # Поле для стоимости
        self.total_price = QLineEdit()
        self.total_price.setReadOnly(True)
        form.addRow('Стоимость:', self.total_price)

        layout.addLayout(form)

        # Кнопка расчета стоимости
        btn_calculate = QPushButton('Рассчитать стоимость')
        btn_calculate.clicked.connect(self.calculate_price)
        layout.addWidget(btn_calculate)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton('Сохранить')
        btn_save.clicked.connect(self.save_booking)

        # Кнопка отмены
        btn_cancel = QPushButton('Отмена')
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

        if self.booking:
            # Заполнение полей данными существующего бронирования
            self.guest_name.setText(self.booking[2])
            self.guest_phone.setText(self.booking[3])
            self.guest_email.setText(self.booking[4] or '')
            self.check_in.setDate(QDate.fromString(self.booking[5], 'yyyy-MM-dd'))
            self.check_out.setDate(QDate.fromString(self.booking[6], 'yyyy-MM-dd'))
            self.adults.setValue(self.booking[7])
            self.children.setValue(self.booking[8])
            self.status.setCurrentText(self.booking[9])
            self.total_price.setText(str(self.booking[10]))
            self.room_type.setCurrentText(self.booking[12])  # room_type из JOIN
            self.load_available_rooms()
            self.room_number.setCurrentIndex(self.room_number.findData(self.booking[1]))  # room_id

    def load_available_rooms(self):
        """Загрузка доступных номеров для выбранного типа и дат."""
        room_type = self.room_type.currentText()
        check_in = self.check_in.date().toString('yyyy-MM-dd')
        check_out = self.check_out.date().toString('yyyy-MM-dd')

        try:
            self.db.ensure_connection()
            rooms = self.db.get_available_rooms(check_in, check_out, room_type)
            self.room_number.clear()
            for room in rooms:
                self.room_number.addItem(f"{room[1]} ({room[2]})", room[0])  # Номер и ID номера
            if self.booking:
                self.room_number.setCurrentIndex(self.room_number.findData(self.booking[1]))
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить номера: {str(e)}')

    def calculate_price(self):
        """Расчет стоимости бронирования."""
        room_id = self.room_number.currentData()
        nights = self.check_in.date().daysTo(self.check_out.date())

        if nights <= 0:
            QMessageBox.warning(self, 'Ошибка', 'Дата выезда должна быть позже даты заезда')
            return
        if not room_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите номер')
            return

        try:
            self.db.ensure_connection()
            self.db.cursor.execute(
                "SELECT price_per_night FROM rooms WHERE id=?", (room_id,)
            )
            result = self.db.cursor.fetchone()
            if not result:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось найти цену для выбранного номера')
                return
            price_per_night = result[0]
            total_price = price_per_night * nights
            self.total_price.setText(f"{total_price:.2f}")
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось рассчитать стоимость: {str(e)}')

    def save_booking(self):
        """Сохранение бронирования."""
        guest_name = self.guest_name.text().strip()
        guest_phone = self.guest_phone.text().strip()
        guest_email = self.guest_email.text().strip()
        check_in = self.check_in.date().toString('yyyy-MM-dd')
        check_out = self.check_out.date().toString('yyyy-MM-dd')
        adults = self.adults.value()
        children = self.children.value()
        room_id = self.room_number.currentData()
        status = self.status.currentText()
        total_price_text = self.total_price.text().strip()

        # Валидация
        if not all([guest_name, guest_phone, room_id]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля (ФИО, телефон, номер)')
            return
        if not re.match(r'^\+?[1-9]\d{10,14}$', guest_phone):
            QMessageBox.warning(self, 'Ошибка', 'Некорректный формат телефона (например, +79991234567)')
            return
        if guest_email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', guest_email):
            QMessageBox.warning(self, 'Ошибка', 'Некорректный формат email (например, example@domain.com)')
            return
        if check_in >= check_out:
            QMessageBox.warning(self, 'Ошибка', 'Дата выезда должна быть позже даты заезда')
            return
        if not total_price_text or float(total_price_text) <= 0:
            QMessageBox.warning(self, 'Ошибка', 'Рассчитайте стоимость перед сохранением')
            return

        total_price = float(total_price_text)

        # Проверка доступности номера
        try:
            self.db.ensure_connection()
            rooms = self.db.get_available_rooms(check_in, check_out, self.room_type.currentText())
            if not any(room[0] == room_id for room in rooms):
                if not self.booking or self.booking[1] != room_id:
                    QMessageBox.warning(self, 'Ошибка', 'Выбранный номер недоступен на указанные даты')
                    return
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось проверить доступность номера: {str(e)}')
            return

        try:
            self.db.ensure_connection()
            if self.booking:
                # Обновление существующего бронирования
                self.db.cursor.execute(
                    """
                    UPDATE bookings
                    SET guest_name=?, guest_phone=?, guest_email=?,
                        check_in_date=?, check_out_date=?, adults=?,
                        children=?, room_id=?, status=?, total_price=?
                    WHERE id=?
                    """,
                    (guest_name, guest_phone, guest_email, check_in, check_out,
                     adults, children, room_id, status, total_price, self.booking[0])
                )
            else:
                # Создание нового бронирования
                self.db.cursor.execute(
                    """
                    INSERT INTO bookings (room_id, guest_name, guest_phone, guest_email,
                                         check_in_date, check_out_date, adults, children,
                                         status, total_price, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (room_id, guest_name, guest_phone, guest_email, check_in, check_out,
                     adults, children, status, total_price, self.user_id)
                )
            self.db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Бронирование успешно сохранено')
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить бронирование: {str(e)}')