"""!
@file admin_dashboard.py
@brief Модуль, реализующий панель администратора.
"""

import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox,
                             QDateEdit, QTextEdit, QMessageBox, QStackedWidget, QGroupBox)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor
import sqlite3
from dialogs.booking_dialog import BookingDialog
from dialogs.room_dialog import RoomDialog
from dialogs.room_status_dialog import RoomStatusDialog
from dialogs.client_dialog import ClientDialog
from dialogs.discount_dialog import DiscountDialog
from forecast import Forecast
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime


class AdminDashboard(QMainWindow):
    """!
    @brief Панель администратора для управления операциями отеля.

    Этот класс реализует основной интерфейс администратора для управления бронированиями,
    номерами, клиентами, финансовыми отчётами и аналитикой.
    """

    def __init__(self, user, db):
        """!
        @brief Инициализация панели администратора.

        @param user Кортеж с данными пользователя (например, ID, роль).
        @param db Объект базы данных SQLite для взаимодействия с данными.
        """
        super().__init__()
        self.user = user
        self.db = db
        self.setWindowTitle(f'Панель администратора ({user[4]})')
        self.setFixedSize(1000, 800)

        self.init_ui()
        self.load_data()
        self.show_bookings()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(300000)

    def load_data(self):
        """!
        @brief Обновление данных бронирований.

        Вызывает метод загрузки данных бронирований в таблицу.
        """
        self.load_bookings_data()

    def init_ui(self):
        """!
        @brief Инициализация пользовательского интерфейса.

        Создаёт боковую панель с кнопками навигации и основной контейнер для разделов.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        btn_bookings = QPushButton('Бронирования')
        btn_bookings.clicked.connect(self.show_bookings)
        btn_rooms = QPushButton('Управление номерами')
        btn_rooms.clicked.connect(self.show_rooms)
        btn_clients = QPushButton('Клиенты и скидки')
        btn_clients.clicked.connect(self.show_clients)
        btn_reports = QPushButton('Финансовые отчёты')
        btn_reports.clicked.connect(self.show_reports)
        btn_analytics = QPushButton('Аналитика и прогнозы')
        btn_analytics.clicked.connect(self.show_analytics)
        btn_logout = QPushButton('Выход')
        btn_logout.clicked.connect(self.logout)

        sidebar_layout.addWidget(btn_bookings)
        sidebar_layout.addWidget(btn_rooms)
        sidebar_layout.addWidget(btn_clients)
        sidebar_layout.addWidget(btn_reports)
        sidebar_layout.addWidget(btn_analytics)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(btn_logout)

        main_layout.addWidget(sidebar)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.init_bookings()
        self.init_rooms()
        self.init_clients()
        self.init_reports()
        self.init_analytics()

        self.stacked_widget.setCurrentIndex(0)

    def init_bookings(self):
        """!
        @brief Инициализация раздела управления бронированиями.

        Создаёт интерфейс для управления бронированиями, включая таблицу и кнопки действий.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Управление бронированиями')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()
        btn_create = QPushButton('Создать новое бронирование')
        btn_create.clicked.connect(self.create_booking)
        btn_edit = QPushButton('Редактировать бронирование')
        btn_edit.clicked.connect(self.edit_booking)
        btn_cancel = QPushButton('Отменить бронирование')
        btn_cancel.clicked.connect(self.cancel_booking)
        btn_assign = QPushButton('Распределить по номерам')
        btn_assign.clicked.connect(self.assign_rooms)

        buttons.addWidget(btn_create)
        buttons.addWidget(btn_edit)
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_assign)

        layout.addLayout(buttons)

        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(9)
        self.bookings_table.setHorizontalHeaderLabels(
            ['ID', 'Даты', 'Категория', 'Гость', 'Телефон', 'Email', 'Статус', 'Оплата', 'Услуги']
        )
        self.bookings_table.setSortingEnabled(True)
        layout.addWidget(self.bookings_table)

        self.load_bookings_data()
        self.stacked_widget.addWidget(widget)

    def load_bookings_data(self):
        """!
        @brief Загрузка данных бронирований в таблицу.

        Извлекает данные бронирований из базы данных и заполняет ими таблицу.
        """
        try:
            self.db.ensure_connection()
            self.db.cursor.execute("""
                SELECT b.id, 
                       b.check_in_date || ' - ' || b.check_out_date as dates,
                       r.type as category,
                       b.guest_name,
                       b.guest_phone,
                       b.guest_email,
                       b.status,
                       b.total_price,
                       GROUP_CONCAT(s.name || ' (' || bs.quantity || ' шт.)') as services
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                LEFT JOIN booking_services bs ON b.id = bs.booking_id
                LEFT JOIN services s ON bs.service_id = s.id
                GROUP BY b.id
                ORDER BY b.check_in_date DESC
            """)
            bookings = self.db.cursor.fetchall()

            self.bookings_table.setRowCount(len(bookings))
            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking):
                    item = QTableWidgetItem(str(value) if value else '')
                    if col == 6:  # Статус
                        if value == 'cancelled':
                            item.setBackground(QColor(255, 200, 200))
                        elif value == 'checked_in':
                            item.setBackground(QColor(200, 255, 200))
                        elif value == 'checked_out':
                            item.setBackground(QColor(200, 200, 255))
                    elif col == 7:  # Оплата
                        item.setText(f"{float(value):.2f} руб.")
                    self.bookings_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки бронирований: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные бронирований')

    def create_booking(self):
        """!
        @brief Создание нового бронирования.

        Открывает диалог для создания нового бронирования и обновляет таблицу при успехе.
        """
        dialog = BookingDialog(self.db, user_id=self.user[0])
        if dialog.exec_() == dialog.Accepted:
            self.load_bookings_data()

    def edit_booking(self):
        """!
        @brief Редактирование существующего бронирования.

        Открывает диалог для редактирования выбранного бронирования.
        """
        selected_row = self.bookings_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование для редактирования')
            return

        booking_id = self.bookings_table.item(selected_row, 0).text()

        try:
            self.db.ensure_connection()
            self.db.cursor.execute("""
                SELECT b.*, r.type as room_type
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.id=?
            """, (booking_id,))
            booking = self.db.cursor.fetchone()

            dialog = BookingDialog(self.db, booking, user_id=self.user[0])
            if dialog.exec_() == dialog.Accepted:
                self.load_bookings_data()
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить данные бронирования: {str(e)}')

    def cancel_booking(self):
        """!
        @brief Отмена бронирования.

        Отменяет выбранное бронирование после подтверждения пользователем.
        """
        selected_row = self.bookings_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование для отмены')
            return

        booking_id = self.bookings_table.item(selected_row, 0).text()
        status = self.bookings_table.item(selected_row, 6).text()

        if status == 'cancelled':
            QMessageBox.warning(self, 'Ошибка', 'Бронирование уже отменено')
            return

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
                self.load_bookings_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось отменить бронирование: {str(e)}')

    def assign_rooms(self):
        """!
        @brief Распределение номеров (заглушка).

        Показывает сообщение о том, что функция будет реализована в будущем.
        """
        QMessageBox.information(
            self, 'Информация',
            'Функция распределения по номерам будет реализована в будущих версиях'
        )

    def init_rooms(self):
        """!
        @brief Инициализация раздела управления номерами.

        Создаёт интерфейс для управления номерами, включая таблицу и кнопки действий.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Управление номерами')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()
        btn_add = QPushButton('Добавить новый номер')
        btn_add.clicked.connect(self.add_room)
        btn_edit = QPushButton('Редактировать статус')
        btn_edit.clicked.connect(self.edit_room_status)

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_edit)

        layout.addLayout(buttons)

        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels(
            ['ID', 'Номер', 'Категория', 'Статус', 'Гость', 'Примечания']
        )
        self.rooms_table.setSortingEnabled(True)
        layout.addWidget(self.rooms_table)

        self.load_rooms_data()
        self.stacked_widget.addWidget(widget)

    def load_rooms_data(self):
        """!
        @brief Загрузка данных номеров в таблицу.

        Извлекает данные о номерах из базы данных и заполняет ими таблицу.
        """
        try:
            self.db.ensure_connection()
            self.db.cursor.execute("""
                SELECT r.id, r.number, r.type, r.status, 
                       CASE WHEN b.guest_name IS NOT NULL THEN b.guest_name ELSE '' END as guest,
                       r.description
                FROM rooms r
                LEFT JOIN bookings b ON r.id = b.room_id AND b.status = 'checked_in'
                ORDER BY r.number
            """)
            rooms = self.db.cursor.fetchall()

            self.rooms_table.setRowCount(len(rooms))
            for row, room in enumerate(rooms):
                for col, value in enumerate(room):
                    item = QTableWidgetItem(str(value))
                    if col == 3:
                        if value == 'occupied':
                            item.setBackground(QColor(255, 200, 200))
                        elif value == 'available':
                            item.setBackground(QColor(200, 255, 200))
                        elif value == 'cleaning':
                            item.setBackground(QColor(255, 255, 200))
                        elif value == 'maintenance':
                            item.setBackground(QColor(200, 200, 255))
                    self.rooms_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки номеров: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные номеров')

    def add_room(self):
        """!
        @brief Добавление нового номера.

        Открывает диалог для добавления нового номера и обновляет таблицу при успехе.
        """
        dialog = RoomDialog(self.db)
        if dialog.exec_() == dialog.Accepted:
            self.load_rooms_data()

    def edit_room_status(self):
        """!
        @brief Редактирование статуса номера.

        Открывает диалог для изменения статуса выбранного номера.
        """
        selected_row = self.rooms_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите номер для изменения статуса')
            return

        room_id = self.rooms_table.item(selected_row, 0).text()
        current_status = self.rooms_table.item(selected_row, 3).text()

        dialog = RoomStatusDialog(current_status)
        if dialog.exec_() == dialog.Accepted:
            new_status = dialog.get_selected_status()
            try:
                self.db.ensure_connection()
                self.db.cursor.execute(
                    "UPDATE rooms SET status=? WHERE id=?", (new_status, room_id)
                )
                self.db.conn.commit()
                self.load_rooms_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось обновить статус номера: {str(e)}')

    def init_clients(self):
        """!
        @brief Инициализация раздела клиентов и скидок.

        Создаёт интерфейс для управления клиентами и их скидками.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Клиенты и скидки')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()
        btn_add = QPushButton('Добавить клиента')
        btn_add.clicked.connect(self.add_client)
        btn_edit = QPushButton('Редактировать скидку')
        btn_edit.clicked.connect(self.edit_discount)

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_edit)

        layout.addLayout(buttons)

        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels(
            ['ID', 'ФИО', 'Email', 'Телефон', 'Скидка (%)', 'История бронирований']
        )
        self.clients_table.setSortingEnabled(True)
        layout.addWidget(self.clients_table)

        self.load_clients_data()
        self.stacked_widget.addWidget(widget)

    def load_clients_data(self):
        """!
        @brief Загрузка данных клиентов в таблицу.

        Извлекает данные о клиентах из базы данных и заполняет ими таблицу.
        """
        try:
            self.db.ensure_connection()
            self.db.cursor.execute("""
                SELECT c.id, c.full_name, c.email, c.phone, c.discount,
                       (SELECT COUNT(*) FROM bookings WHERE guest_email = c.email) as bookings_count
                FROM clients c
                ORDER BY c.full_name
            """)
            clients = self.db.cursor.fetchall()

            self.clients_table.setRowCount(len(clients))
            for row, client in enumerate(clients):
                for col, value in enumerate(client):
                    item = QTableWidgetItem(str(value))
                    if col == 4 and value > 0:
                        item.setBackground(QColor(200, 255, 200))
                    self.clients_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки клиентов: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные клиентов')

    def add_client(self):
        """!
        @brief Добавление нового клиента.

        Открывает диалог для добавления нового клиента и обновляет таблицу при успехе.
        """
        dialog = ClientDialog(self.db)
        if dialog.exec_() == dialog.Accepted:
            self.load_clients_data()

    def edit_discount(self):
        """!
        @brief Редактирование скидки клиента.

        Открывает диалог для изменения скидки выбранного клиента.
        """
        selected_row = self.clients_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите клиента для изменения скидки')
            return

        client_id = self.clients_table.item(selected_row, 0).text()
        current_discount = int(self.clients_table.item(selected_row, 4).text())

        dialog = DiscountDialog(current_discount)
        if dialog.exec_() == dialog.Accepted:
            new_discount = dialog.get_discount()
            try:
                self.db.ensure_connection()
                self.db.cursor.execute(
                    "UPDATE clients SET discount=? WHERE id=?", (new_discount, client_id)
                )
                self.db.conn.commit()
                self.load_clients_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось обновить скидку: {str(e)}')

    def init_reports(self):
        """!
        @brief Инициализация раздела финансовых отчётов.

        Создаёт интерфейс для генерации и экспорта финансовых отчётов.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Финансовые отчёты')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        report_params = QHBoxLayout()
        self.report_type = QComboBox()
        self.report_type.addItems(['Доходы', 'Расходы', 'Количество бронирований',
                                   'Популярность услуг'])
        report_params.addWidget(QLabel('Тип отчета:'))
        report_params.addWidget(self.report_type)

        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        report_params.addWidget(QLabel('С:'))
        report_params.addWidget(self.start_date)

        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        report_params.addWidget(QLabel('По:'))
        report_params.addWidget(self.end_date)

        btn_generate = QPushButton('Создать отчёт')
        btn_generate.clicked.connect(self.generate_report)
        report_params.addWidget(btn_generate)

        btn_export = QPushButton('Экспорт в PDF')
        btn_export.clicked.connect(self.export_to_pdf)
        report_params.addWidget(btn_export)

        btn_export_excel = QPushButton('Экспорт в Excel')
        btn_export_excel.clicked.connect(self.export_to_excel)
        report_params.addWidget(btn_export_excel)

        layout.addLayout(report_params)

        self.report_result = QTextEdit()
        self.report_result.setReadOnly(True)
        layout.addWidget(self.report_result)

        self.stacked_widget.addWidget(widget)

    def generate_report(self):
        """!
        @brief Генерация финансового отчёта.

        Формирует отчёт на основе выбранного типа и периода.
        """
        report_type = self.report_type.currentText()
        start_date = self.start_date.date().toString('yyyy-MM-dd')
        end_date = self.end_date.date().toString('yyyy-MM-dd')

        try:
            self.db.ensure_connection()
            report_text = f"Отчет: {report_type}\nПериод: {start_date} - {end_date}\n\n"

            if report_type == 'Доходы':
                self.db.cursor.execute("""
                    SELECT strftime('%Y-%m-%d', created_at) as date,
                           SUM(total_price) as daily_income
                    FROM bookings
                    WHERE date(created_at) BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                """, (start_date, end_date))
                results = self.db.cursor.fetchall()

                total = 0
                for row in results:
                    report_text += f"{row[0]}: {row[1]:.2f} руб.\n"
                    total += row[1]
                report_text += f"\nИтого: {total:.2f} руб."

            elif report_type == 'Количество бронирований':
                self.db.cursor.execute("""
                    SELECT strftime('%Y-%m-%d', created_at) as date,
                           COUNT(*) as bookings_count
                    FROM bookings
                    WHERE date(created_at) BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                """, (start_date, end_date))
                results = self.db.cursor.fetchall()

                total = 0
                for row in results:
                    report_text += f"{row[0]}: {row[1]} бронирований\n"
                    total += row[1]
                report_text += f"\nИтого: {total} бронирований"

            elif report_type == 'Популярность услуг':
                self.db.cursor.execute("""
                    SELECT s.name, SUM(bs.quantity) as service_count
                    FROM booking_services bs
                    JOIN services s ON bs.service_id = s.id
                    JOIN bookings b ON bs.booking_id = b.id
                    WHERE date(b.created_at) BETWEEN ? AND ?
                    GROUP BY s.name
                    ORDER BY service_count DESC
                """, (start_date, end_date))
                results = self.db.cursor.fetchall()

                for row in results:
                    report_text += f"{row[0]}: {row[1]} заказов\n"

            self.report_result.setPlainText(report_text)
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сформировать отчет: {str(e)}')

    def export_to_pdf(self):
        """!
        @brief Экспорт отчёта в PDF (заглушка).

        Показывает сообщение о том, что функция будет реализована в будущем.
        """
        QMessageBox.information(
            self, 'Информация',
            'Экспорт в PDF будет реализован в будущих версиях'
        )

    def export_to_excel(self):
        """!
        @brief Экспорт отчёта в Excel (заглушка).

        Показывает сообщение о том, что функция будет реализована в будущем.
        """
        QMessageBox.information(
            self, 'Информация',
            'Экспорт в Excel будет реализован в будущих версиях'
        )

    def init_analytics(self):
        """!
        @brief Инициализация раздела аналитики и прогнозов.

        Создаёт интерфейс для формирования прогнозов бронирований и доходов.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Аналитика и прогнозы')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        forecast_group = QGroupBox("Прогноз бронирований и доходов")
        forecast_layout = QVBoxLayout()

        params_layout = QHBoxLayout()
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(['Бронирования', 'Доход'])
        params_layout.addWidget(QLabel('Тип данных:'))
        params_layout.addWidget(self.analysis_type)

        self.forecast_start_date = QDateEdit(calendarPopup=True)
        self.forecast_start_date.setDate(QDate.currentDate().addYears(-1))
        params_layout.addWidget(QLabel('Начальная дата:'))
        params_layout.addWidget(self.forecast_start_date)

        self.forecast_end_date = QDateEdit(calendarPopup=True)
        self.forecast_end_date.setDate(QDate.currentDate())
        params_layout.addWidget(QLabel('Конечная дата:'))
        params_layout.addWidget(self.forecast_end_date)

        self.forecast_periods = QComboBox()
        self.forecast_periods.addItems(['1 месяц', '3 месяца', '6 месяцев', '12 месяцев'])
        self.forecast_periods.setCurrentText('3 месяца')
        params_layout.addWidget(QLabel('Период прогноза:'))
        params_layout.addWidget(self.forecast_periods)

        btn_generate = QPushButton('Сформировать прогноз')
        btn_generate.clicked.connect(self.generate_forecast)
        params_layout.addWidget(btn_generate)

        forecast_layout.addLayout(params_layout)

        self.forecast_table = QTableWidget()
        self.forecast_table.setColumnCount(6)
        self.forecast_table.setHorizontalHeaderLabels([
            'Месяц', 'Фактическое', 'Прогноз', 'Абс. ошибка', 'Квадр. ошибка', 'Отн. ошибка (%)'
        ])
        self.forecast_table.setSortingEnabled(True)
        forecast_layout.addWidget(self.forecast_table)

        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        forecast_layout.addWidget(self.canvas)

        forecast_group.setLayout(forecast_layout)
        layout.addWidget(forecast_group)

        self.stacked_widget.addWidget(widget)

    def generate_forecast(self):
        """!
        @brief Генерация прогноза с использованием скользящей средней.

        Формирует прогноз бронирований или доходов на основе данных за выбранный период.
        """
        data_type = 'bookings' if self.analysis_type.currentText() == 'Бронирования' else 'revenue'
        start_date = self.forecast_start_date.date().toString('yyyy-MM-dd')
        end_date = self.forecast_end_date.date().toString('yyyy-MM-dd')
        period_text = self.forecast_periods.currentText()
        periods = {'1 месяц': 1, '3 месяца': 3, '6 месяцев': 6, '12 месяцев': 12}[period_text]

        try:
            self.db.ensure_connection()
            time_series = self.db.get_time_series(data_type, start_date, end_date)
            if not time_series or len(time_series) < 3:
                QMessageBox.warning(self, 'Ошибка', 'Недостаточно данных для прогноза (нужно минимум 3 месяца)')
                return

            months, values = zip(*time_series)
            values = list(values)

            n = 3
            forecast_values = Forecast.forecast_values(values, n, periods)
            if not forecast_values:
                QMessageBox.warning(self, 'Ошибка', 'Невозможно рассчитать прогноз')
                return

            self.forecast_table.setRowCount(len(values) + periods)
            actual_values = values + [None] * periods
            predicted_values = values[:len(values)] + forecast_values
            errors = Forecast.calculate_errors(values[-min(len(forecast_values), len(values)):],
                                             forecast_values[:min(len(forecast_values), len(values))])

            for i, month in enumerate(months):
                self.forecast_table.setItem(i, 0, QTableWidgetItem(month))
                self.forecast_table.setItem(i, 1, QTableWidgetItem(str(actual_values[i]) if actual_values[i] else ""))
                self.forecast_table.setItem(i, 2, QTableWidgetItem(str(predicted_values[i])))

            last_month = datetime.strptime(months[-1], "%Y-%m")
            forecast_months = list(months)
            for i in range(periods):
                next_month = last_month.replace(month=last_month.month % 12 + 1,
                                               year=last_month.year + (last_month.month // 12))
                forecast_months.append(next_month.strftime("%Y-%m"))
                self.forecast_table.setItem(len(months) + i, 0, QTableWidgetItem(next_month.strftime("%Y-%m")))
                self.forecast_table.setItem(len(months) + i, 2, QTableWidgetItem(str(forecast_values[i])))
                last_month = next_month

            mean_abs_error, mean_sq_error, mean_rel_error = errors
            self.forecast_table.setItem(0, 3, QTableWidgetItem(f"{mean_abs_error:.2f}"))
            self.forecast_table.setItem(0, 4, QTableWidgetItem(f"{mean_sq_error:.2f}"))
            self.forecast_table.setItem(0, 5, QTableWidgetItem(f"{mean_rel_error:.2f} ({Forecast.interpret_accuracy(mean_rel_error)})"))

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            # Сброс стилей Matplotlib и отключение циклической палитры
            plt.style.use('default')
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#0000FF', '#FF0000'])
            # Рисуем линию фактических данных (синий цвет)
            line_actual = ax.plot(months, values, label="Фактические", marker="o", color='#0000FF')
            # Рисуем линию прогноза (красный цвет, пунктир)
            line_forecast = ax.plot(forecast_months, predicted_values, label="Прогноз", marker="x", linestyle='--', color='#FF0000')
            ax.set_xlabel("Месяц")
            ax.set_ylabel("Количество бронирований" if data_type == "bookings" else "Доход (руб.)")
            ax.legend()
            ax.grid(True)
            plt.setp(ax.get_xticklabels(), rotation=45)
            self.canvas.draw()

            # Логирование для проверки применения цвета
            logging.info(f"Цвет линии фактических данных в AdminDashboard: {line_actual[0].get_color()}")
            logging.info(f"Цвет линии прогноза в AdminDashboard: {line_forecast[0].get_color()}")

            for i in range(periods):
                self.db.save_forecast(
                    forecast_months[len(months) + i],
                    data_type,
                    None,
                    forecast_values[i],
                    mean_rel_error if i == 0 else None
                )

        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сформировать прогноз: {str(e)}')

    def show_bookings(self):
        """!
        @brief Отображение раздела бронирований.

        Переключает интерфейс на раздел бронирований и обновляет данные.
        """
        self.stacked_widget.setCurrentIndex(0)
        self.load_bookings_data()

    def show_rooms(self):
        """!
        @brief Отображение раздела управления номерами.

        Переключает интерфейс на раздел управления номерами и обновляет данные.
        """
        self.stacked_widget.setCurrentIndex(1)
        self.load_rooms_data()

    def show_clients(self):
        """!
        @brief Отображение раздела клиентов и скидок.

        Переключает интерфейс на раздел клиентов и обновляет данные.
        """
        self.stacked_widget.setCurrentIndex(2)
        self.load_clients_data()

    def show_reports(self):
        """!
        @brief Отображение раздела финансовых отчётов.

        Переключает интерфейс на раздел финансовых отчётов.
        """
        self.stacked_widget.setCurrentIndex(3)

    def show_analytics(self):
        """!
        @brief Отображение раздела аналитики и прогнозов.

        Переключает интерфейс на раздел аналитики и формирует прогноз.
        """
        self.stacked_widget.setCurrentIndex(4)
        self.generate_forecast()

    def logout(self):
        """!
        @brief Выход из системы и возврат к окну авторизации.

        Закрывает текущее окно и открывает окно авторизации.
        """
        from auth_window import AuthWindow
        self.close()
        auth_window = AuthWindow()
        auth_window.show()

    def closeEvent(self, event):
        """!
        @brief Обработка закрытия окна.

        @param event Событие закрытия окна.
        """
        event.accept()