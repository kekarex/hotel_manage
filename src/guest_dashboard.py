"""
@file guest_dashboard.py
@brief Модуль, реализующий панель гостя для управления бронированиями и отзывами.
"""

import sqlite3
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QComboBox, QDateEdit,
                             QCheckBox, QTextEdit, QPushButton, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QFormLayout, QTableWidget,
                             QTableWidgetItem, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap, QColor


class GuestDashboard(QMainWindow):
    """
    @brief Класс панели гостя для управления бронированиями и отзывами.
    """
    def __init__(self, user, db):
        """
        @brief Инициализация панели гостя.
        @param user Кортеж с данными пользователя.
        @param db Экземпляр класса Database для работы с базой данных.
        """
        super().__init__()
        self.user = user  # Сохранение данных пользователя
        self.db = db  # Сохранение объекта базы данных
        logging.info(f"GuestDashboard получил экземпляр Database: {id(self.db)}")
        self.setWindowTitle(f'Личный кабинет гостя ({user[4]})')  # Установка заголовка
        self.setFixedSize(1000, 800)  # Установка фиксированного размера окна

        self.init_ui()  # Инициализация интерфейса
        self.load_data()  # Загрузка данных

    def init_ui(self):
        """
        @brief Инициализация пользовательского интерфейса.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создание вкладок
        self.tabs = QTabWidget()
        central_layout = QVBoxLayout()
        central_layout.addWidget(self.tabs)
        central_widget.setLayout(central_layout)

        self.init_booking_tab()  # Инициализация вкладки бронирования
        self.init_my_bookings_tab()  # Инициализация вкладки моих бронирований
        self.init_review_tab()  # Инициализация вкладки отзывов
        self.init_offers_tab()  # Инициализация вкладки предложений

    def init_booking_tab(self):
        """
        @brief Инициализация вкладки бронирования номера.
        """
        tab = QWidget()
        layout = QHBoxLayout()
        tab.setLayout(layout)

        form_layout = QVBoxLayout()

        # Группа выбора категории номера
        category_group = QGroupBox('Категория номера')
        category_layout = QVBoxLayout()

        self.room_type = QComboBox()
        self.room_type.addItems(['Эконом', 'Стандарт', 'Люкс', 'Апартаменты'])
        category_layout.addWidget(self.room_type)

        # Изображение номера
        self.room_image = QLabel()
        self.room_image.setPixmap(QPixmap('assets/room_placeholder.png').scaled(
            300, 200, Qt.KeepAspectRatio))
        category_layout.addWidget(self.room_image)

        # Описание номера
        self.room_description = QLabel('Описание номера будет здесь')
        self.room_description.setWordWrap(True)
        category_layout.addWidget(self.room_description)

        category_group.setLayout(category_layout)
        form_layout.addWidget(category_group)

        # Группа выбора дат
        dates_group = QGroupBox('Даты проживания')
        dates_layout = QFormLayout()

        self.check_in = QDateEdit(calendarPopup=True)
        self.check_in.setDate(QDate.currentDate())
        dates_layout.addRow('Дата заезда:', self.check_in)

        self.check_out = QDateEdit(calendarPopup=True)
        self.check_out.setDate(QDate.currentDate().addDays(1))
        dates_layout.addRow('Дата выезда:', self.check_out)

        dates_group.setLayout(dates_layout)
        form_layout.addWidget(dates_group)

        # Группа дополнительных услуг
        services_group = QGroupBox('Дополнительные услуги')
        services_layout = QVBoxLayout()

        self.transfer = QCheckBox('Трансфер (500 руб.)')
        self.breakfast = QCheckBox('Завтрак (300 руб.)')
        self.spa = QCheckBox('SPA (1000 руб.)')

        services_layout.addWidget(self.transfer)
        services_layout.addWidget(self.breakfast)
        services_layout.addWidget(self.spa)

        services_group.setLayout(services_layout)
        form_layout.addWidget(services_group)

        # Группа количества гостей
        guests_group = QGroupBox('Количество гостей')
        guests_layout = QFormLayout()

        self.adults = QComboBox()
        self.adults.addItems([str(i) for i in range(1, 5)])
        self.adults.setCurrentIndex(0)
        guests_layout.addRow('Взрослые:', self.adults)

        self.children = QComboBox()
        self.children.addItems([str(i) for i in range(0, 4)])
        self.children.setCurrentIndex(0)
        guests_layout.addRow('Дети:', self.children)

        guests_group.setLayout(guests_layout)
        form_layout.addWidget(guests_group)

        # Кнопка бронирования
        btn_book = QPushButton('Забронировать')
        btn_book.clicked.connect(self.book_room)
        form_layout.addWidget(btn_book)

        layout.addLayout(form_layout)

        # Таблица доступных номеров
        self.available_rooms_table = QTableWidget()
        self.available_rooms_table.setColumnCount(5)
        self.available_rooms_table.setHorizontalHeaderLabels(
            ['ID', 'Номер', 'Категория', 'Цена/ночь', 'Доступность']
        )
        self.available_rooms_table.setSortingEnabled(True)
        layout.addWidget(self.available_rooms_table)

        self.tabs.addTab(tab, 'Бронирование')

    def load_data(self):
        """
        @brief Загрузка данных о доступных номерах и обновление интерфейса.
        """
        self.load_available_rooms()

    def load_available_rooms(self):
        """
        @brief Загрузка списка доступных номеров в таблицу.
        """
        check_in_date = self.check_in.date().toString('yyyy-MM-dd')
        check_out_date = self.check_out.date().toString('yyyy-MM-dd')
        room_type = self.room_type.currentText()

        try:
            self.db.ensure_connection()
            rooms = self.db.get_available_rooms(check_in_date, check_out_date, room_type)
            self.available_rooms_table.setRowCount(len(rooms))
            for row, room in enumerate(rooms):
                for col, value in enumerate([room[0], room[1], room[2], f"{room[5]} руб.", room[7]]):
                    item = QTableWidgetItem(str(value))
                    if col == 4 and value != 'available':
                        item.setBackground(QColor(255, 200, 200))
                    self.available_rooms_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки доступных номеров: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные номеров')

    def book_room(self):
        """
        @brief Обработка бронирования номера.
        """
        selected_row = self.available_rooms_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите номер для бронирования')
            return

        room_id = self.available_rooms_table.item(selected_row, 0).text()
        check_in_date = self.check_in.date().toString('yyyy-MM-dd')
        check_out_date = self.check_out.date().toString('yyyy-MM-dd')
        adults = int(self.adults.currentText())
        children = int(self.children.currentText())
        guest_name = self.user[4]
        guest_phone = self.user[6] or ''
        guest_email = self.user[5]

        services = []
        if self.transfer.isChecked():
            services.append((1, 1))  # ID 1 - трансфер
        if self.breakfast.isChecked():
            services.append((2, adults + children))  # ID 2 - завтрак
        if self.spa.isChecked():
            services.append((3, 1))  # ID 3 - SPA

        try:
            total_price = self.db.calculate_total_price(
                room_id, check_in_date, check_out_date, guest_email, services
            )
            self.db.cursor.execute(
                """
                INSERT INTO bookings (room_id, guest_name, guest_phone, guest_email,
                                     check_in_date, check_out_date, adults, children,
                                     status, total_price, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'reserved', ?, ?)
                """, (room_id, guest_name, guest_phone, guest_email,
                      check_in_date, check_out_date, adults, children,
                      total_price, self.user[0])
            )
            booking_id = self.db.cursor.lastrowid

            for service_id, quantity in services:
                self.db.cursor.execute(
                    "INSERT INTO booking_services (booking_id, service_id, quantity) VALUES (?, ?, ?)",
                    (booking_id, service_id, quantity)
                )

            self.db.conn.commit()
            logging.info(f"Успешное бронирование номера {room_id} для {guest_email}")
            QMessageBox.information(self, 'Успех', 'Бронирование успешно создано')
            self.load_available_rooms()
        except sqlite3.Error as e:
            logging.error(f"Ошибка бронирования: {e}")
            QMessageBox.warning(self, 'Ошибка', f'Не удалось забронировать номер: {str(e)}')

    def init_my_bookings_tab(self):
        """
        @brief Инициализация вкладки моих бронирований.
        """
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        title = QLabel('Мои бронирования')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        self.my_bookings_table = QTableWidget()
        self.my_bookings_table.setColumnCount(8)
        self.my_bookings_table.setHorizontalHeaderLabels(
            ['ID', 'Номер', 'Даты', 'Статус', 'Цена', 'Услуги', 'Отзыв', 'Действия']
        )
        self.my_bookings_table.setSortingEnabled(True)
        layout.addWidget(self.my_bookings_table)

        btn_refresh = QPushButton('Обновить')
        btn_refresh.clicked.connect(self.load_my_bookings)
        layout.addWidget(btn_refresh)

        self.load_my_bookings()
        self.tabs.addTab(tab, 'Мои бронирования')

    def load_my_bookings(self):
        """
        @brief Загрузка данных о бронированиях текущего гостя.
        """
        try:
            self.db.ensure_connection()
            self.db.cursor.execute(
                """
                SELECT b.id, r.number, b.check_in_date || ' - ' || b.check_out_date,
                       b.status, b.total_price,
                       GROUP_CONCAT(s.name || ' (' || bs.quantity || ' шт.)'),
                       (SELECT rating FROM reviews WHERE booking_id = b.id LIMIT 1)
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                LEFT JOIN booking_services bs ON b.id = bs.booking_id
                LEFT JOIN services s ON bs.service_id = s.id
                WHERE b.guest_email = ? AND b.status != 'cancelled'
                GROUP BY b.id
                ORDER BY b.check_in_date DESC
                """, (self.user[5],)
            )
            bookings = self.db.cursor.fetchall()

            self.my_bookings_table.setRowCount(len(bookings))
            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking):
                    item = QTableWidgetItem(str(value) if value else '')
                    if col == 3:  # Статус
                        if value == 'checked_in':
                            item.setBackground(QColor(200, 255, 200))
                        elif value == 'checked_out':
                            item.setBackground(QColor(200, 200, 255))
                    elif col == 4:  # Цена
                        item.setText(f"{float(value):.2f} руб.")
                    self.my_bookings_table.setItem(row, col, item)

                btn_cancel = QPushButton('Отменить')
                btn_cancel.clicked.connect(lambda checked, id=booking[0]: self.cancel_booking(id))
                self.my_bookings_table.setCellWidget(row, 7, btn_cancel)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки бронирований: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить бронирования')

    def cancel_booking(self, booking_id):
        """
        @brief Отмена бронирования гостем.
        @param booking_id Идентификатор бронирования.
        """
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите отменить это бронирование?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db.ensure_connection()
                self.db.cursor.execute(
                    "UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,)
                )
                self.db.conn.commit()
                logging.info(f"Бронирование {booking_id} отменено пользователем {self.user[5]}")
                QMessageBox.information(self, 'Успех', 'Бронирование отменено')
                self.load_my_bookings()
            except sqlite3.Error as e:
                logging.error(f"Ошибка отмены бронирования: {e}")
                QMessageBox.warning(self, 'Ошибка', f'Не удалось отменить бронирование: {str(e)}')

    def init_review_tab(self):
        """
        @brief Инициализация вкладки для оставления отзывов.
        """
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        title = QLabel('Оставить отзыв')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        self.review_bookings = QComboBox()
        layout.addWidget(QLabel('Выберите бронирование:'))
        layout.addWidget(self.review_bookings)

        form_layout = QFormLayout()
        self.rating = QComboBox()
        self.rating.addItems(['1', '2', '3', '4', '5'])
        form_layout.addRow('Оценка (1-5):', self.rating)

        self.comment = QTextEdit()
        self.comment.setPlaceholderText('Ваш комментарий...')
        form_layout.addRow('Комментарий:', self.comment)

        layout.addLayout(form_layout)

        btn_submit = QPushButton('Отправить отзыв')
        btn_submit.clicked.connect(self.submit_review)
        layout.addWidget(btn_submit)

        self.load_reviews_data()
        self.tabs.addTab(tab, 'Отзывы')

    def load_reviews_data(self):
        """
        @brief Загрузка списка бронирований для отзывов.
        """
        try:
            self.db.ensure_connection()
            self.db.cursor.execute(
                """
                SELECT b.id, r.number, b.check_in_date || ' - ' || b.check_out_date
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.guest_email = ? AND b.status = 'checked_out'
                AND NOT EXISTS (SELECT 1 FROM reviews WHERE booking_id = b.id)
                ORDER BY b.check_in_date DESC
                """, (self.user[5],)
            )
            bookings = self.db.cursor.fetchall()
            self.review_bookings.clear()
            self.review_bookings.addItems([f"Бронь #{b[0]} (Номер {b[1]}, {b[2]})" for b in bookings])
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки данных для отзывов: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные бронирований')

    def submit_review(self):
        """
        @brief Отправка отзыва для выбранного бронирования.
        """
        if not self.review_bookings.currentText():
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование')
            return

        booking_id = int(self.review_bookings.currentText().split('#')[1].split(' ')[0])
        rating = int(self.rating.currentText())
        comment = self.comment.toPlainText().strip()

        try:
            self.db.ensure_connection()
            self.db.cursor.execute(
                "INSERT INTO reviews (booking_id, rating, comment) VALUES (?, ?, ?)",
                (booking_id, rating, comment)
            )
            self.db.conn.commit()
            logging.info(f"Отзыв для бронирования {booking_id} отправлен пользователем {self.user[5]}")
            QMessageBox.information(self, 'Успех', 'Отзыв успешно отправлен')
            self.load_reviews_data()
            self.comment.clear()
        except sqlite3.Error as e:
            logging.error(f"Ошибка отправки отзыва: {e}")
            QMessageBox.warning(self, 'Ошибка', f'Не удалось отправить отзыв: {str(e)}')

    def init_offers_tab(self):
        """
        @brief Инициализация вкладки предложений.
        """
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        title = QLabel('Специальные предложения')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        offers = [
            "Скидка 10% на номера категории 'Люкс' при бронировании на 5+ дней!",
            "Бесплатный завтрак при бронировании до конца мая!",
            "Скидка 15% для постоянных клиентов с 3+ бронированиями."
        ]
        for offer in offers:
            label = QLabel(offer)
            label.setWordWrap(True)
            layout.addWidget(label)

        self.tabs.addTab(tab, 'Предложения')

    def closeEvent(self, event):
        """
        @brief Обработка события закрытия окна.
        @param event Событие закрытия окна.
        """
        logging.info(f"Закрытие GuestDashboard для пользователя {self.user[5]}")
        event.accept()