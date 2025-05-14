import sqlite3
from PyQt5.QtWidgets import QDialog, QLineEdit, QComboBox, QDateEdit, QSpinBox, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox
from PyQt5.QtCore import QDate


class BookingDialog(QDialog):
    """Диалог для создания или редактирования бронирования."""

    def __init__(self, db, booking=None):
        """Инициализация диалога бронирования."""
        super().__init__()
        self.db = db  # Сохранение объекта базы данных
        self.booking = booking  # Сохранение данных бронирования (если редактирование)
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
        self.guest_phone.setPlaceholderText('Телефон')
        form.addRow('Телефон:', self.guest_phone)

        # Поле для email
        self.guest_email = QLineEdit()
        self.guest_email.setPlaceholderText('Email')
        form.addRow('Email:', self.guest_email)

        # Поле для даты заезда
        self.check_in = QDateEdit(calendarPopup=True)
        self.check_in.setDate(QDate.currentDate())
        form.addRow('Дата заезда:', self.check_in)

        # Поле для даты выезда
        self.check_out = QDateEdit(calendarPopup=True)
        self.check_out.setDate(QDate.currentDate().addDays(1))
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

            self.db.cursor.execute("SELECT type FROM rooms WHERE id=?", (self.booking[1],))
            room_type = self.db.cursor.fetchone()[0]
            self.room_type.setCurrentText(room_type)

        self.load_available_rooms()

    def load_available_rooms(self):
        """Загрузка доступных номеров для выбранного типа и дат."""
        room_type = self.room_type.currentText()
        check_in = self.check_in.date().toString('yyyy-MM-dd')
        check_out = self.check_out.date().toString('yyyy-MM-dd')

        try:
            rooms = self.db.get_available_rooms(check_in, check_out, room_type)
            self.room_number.clear()
            for room in rooms:
                self.room_number.addItem(str(room[1]), room[0])  # Номер и ID номера
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить номера: {str(e)}')

    def calculate_price(self):
        """Расчет стоимости бронирования."""
        room_type = self.room_type.currentText()
        nights = self.check_in.date().daysTo(self.check_out.date())

        if nights <= 0:
            QMessageBox.warning(self, 'Ошибка', 'Дата выезда должна быть позже даты заезда')
            return

        try:
            self.db.cursor.execute(
                "SELECT price_per_night FROM rooms WHERE type=? LIMIT 1", (room_type,)
            )
            price_per_night = self.db.cursor.fetchone()[0]
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
        total_price = float(self.total_price.text() or 0)

        if not all([guest_name, guest_phone, room_id]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля')
            return

        try:
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
                     adults, children, status, total_price, 1)  # created_by=1 (админ)
                )
            self.db.conn.commit()
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить бронирование: {str(e)}')