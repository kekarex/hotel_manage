import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox,
                             QDateEdit, QTextEdit, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor
import sqlite3
from dialogs.booking_dialog import BookingDialog
from dialogs.room_dialog import RoomDialog
from dialogs.room_status_dialog import RoomStatusDialog
from dialogs.client_dialog import ClientDialog
from dialogs.discount_dialog import DiscountDialog


class AdminDashboard(QMainWindow):
    """Панель администратора для управления операциями отеля."""

    def __init__(self, user, db):
        """Инициализация панели администратора."""
        super().__init__()
        self.user = user  # Сохранение данных пользователя
        self.db = db  # Сохранение объекта базы данных
        self.setWindowTitle(f'Панель администратора ({user[4]})')  # Установка заголовка
        self.setFixedSize(1000, 800)  # Установка фиксированного размера окна

        self.init_ui()  # Инициализация интерфейса
        self.load_data()  # Загрузка данных
        self.show_bookings()  # Отображение раздела бронирований

        # Настройка таймера для периодического обновления данных
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(300000)  # Обновление каждые 5 минут

    def load_data(self):
        """Обновление данных бронирований."""
        self.load_bookings_data()

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Создание боковой панели
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        # Кнопка для перехода к бронированиям
        btn_bookings = QPushButton('Бронирования')
        btn_bookings.clicked.connect(self.show_bookings)

        # Кнопка для управления номерами
        btn_rooms = QPushButton('Управление номерами')
        btn_rooms.clicked.connect(self.show_rooms)

        # Кнопка для управления клиентами
        btn_clients = QPushButton('Клиенты и скидки')
        btn_clients.clicked.connect(self.show_clients)

        # Кнопка для финансовых отчетов
        btn_reports = QPushButton('Финансовые отчёты')
        btn_reports.clicked.connect(self.show_reports)

        # Кнопка для аналитики и прогнозов
        btn_analytics = QPushButton('Аналитика и прогнозы')
        btn_analytics.clicked.connect(self.show_analytics)

        # Кнопка выхода
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

        # Создание виджета для переключения разделов
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.init_bookings()  # Инициализация раздела бронирований
        self.init_rooms()  # Инициализация раздела номеров
        self.init_clients()  # Инициализация раздела клиентов
        self.init_reports()  # Инициализация раздела отчетов
        self.init_analytics()  # Инициализация раздела аналитики

        self.stacked_widget.setCurrentIndex(0)  # Установка начального раздела

    def init_bookings(self):
        """Инициализация раздела управления бронированиями."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок раздела
        title = QLabel('Управление бронированиями')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()

        # Кнопка создания бронирования
        btn_create = QPushButton('Создать новое бронирование')
        btn_create.clicked.connect(self.create_booking)

        # Кнопка редактирования бронирования
        btn_edit = QPushButton('Редактировать бронирование')
        btn_edit.clicked.connect(self.edit_booking)

        # Кнопка отмены бронирования
        btn_cancel = QPushButton('Отменить бронирование')
        btn_cancel.clicked.connect(self.cancel_booking)

        # Кнопка распределения номеров
        btn_assign = QPushButton('Распределить по номерам')
        btn_assign.clicked.connect(self.assign_rooms)

        buttons.addWidget(btn_create)
        buttons.addWidget(btn_edit)
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_assign)

        layout.addLayout(buttons)

        # Создание таблицы бронирований
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(8)
        self.bookings_table.setHorizontalHeaderLabels(
            ['ID', 'Даты', 'Категория', 'Гость', 'Телефон', 'Email', 'Статус', 'Оплата']
        )
        self.bookings_table.setSortingEnabled(True)
        layout.addWidget(self.bookings_table)

        self.load_bookings_data()  # Загрузка данных бронирований
        self.stacked_widget.addWidget(widget)

    def load_bookings_data(self):
        """Загрузка данных бронирований в таблицу."""
        try:
            self.db.cursor.execute("""
                SELECT b.id, 
                       b.check_in_date || ' - ' || b.check_out_date as dates,
                       r.type as category,
                       b.guest_name,
                       b.guest_phone,
                       b.guest_email,
                       b.status,
                       b.total_price
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                ORDER BY b.check_in_date DESC
            """)
            bookings = self.db.cursor.fetchall()

            self.bookings_table.setRowCount(len(bookings))
            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking):
                    item = QTableWidgetItem(str(value))

                    # Окраска статуса
                    if col == 6:  # Столбец статуса
                        if value == 'cancelled':
                            item.setBackground(QColor(255, 200, 200))
                        elif value == 'checked_in':
                            item.setBackground(QColor(200, 255, 200))
                        elif value == 'checked_out':
                            item.setBackground(QColor(200, 200, 255))

                    self.bookings_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки бронирований: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные бронирований')

    def create_booking(self):
        """Создание нового бронирования."""
        dialog = BookingDialog(self.db)
        if dialog.exec_() == dialog.Accepted:
            self.load_bookings_data()

    def edit_booking(self):
        """Редактирование существующего бронирования."""
        selected_row = self.bookings_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование для редактирования')
            return

        booking_id = self.bookings_table.item(selected_row, 0).text()

        try:
            self.db.cursor.execute("""
                SELECT b.*, r.type as room_type
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.id=?
            """, (booking_id,))
            booking = self.db.cursor.fetchone()

            dialog = BookingDialog(self.db, booking)
            if dialog.exec_() == dialog.Accepted:
                self.load_bookings_data()
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить данные бронирования: {str(e)}')

    def cancel_booking(self):
        """Отмена бронирования."""
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
                self.db.cursor.execute(
                    "UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,)
                )
                self.db.conn.commit()
                self.load_bookings_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось отменить бронирование: {str(e)}')

    def assign_rooms(self):
        """Распределение номеров (заглушка)."""
        QMessageBox.information(
            self, 'Информация',
            'Функция распределения по номерам будет реализована в будущих версиях'
        )

    def init_rooms(self):
        """Инициализация раздела управления номерами."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок раздела
        title = QLabel('Управление номерами')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()

        # Кнопка добавления номера
        btn_add = QPushButton('Добавить новый номер')
        btn_add.clicked.connect(self.add_room)

        # Кнопка редактирования статуса номера
        btn_edit = QPushButton('Редактировать статус')
        btn_edit.clicked.connect(self.edit_room_status)

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_edit)

        layout.addLayout(buttons)

        # Создание таблицы номеров
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels(
            ['ID', 'Номер', 'Категория', 'Статус', 'Гость', 'Примечания']
        )
        self.rooms_table.setSortingEnabled(True)
        layout.addWidget(self.rooms_table)

        self.load_rooms_data()  # Загрузка данных номеров
        self.stacked_widget.addWidget(widget)

    def load_rooms_data(self):
        """Загрузка данных номеров в таблицу."""
        try:
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

                    # Окраска статуса
                    if col == 3:  # Столбец статуса
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
        """Добавление нового номера."""
        dialog = RoomDialog(self.db)
        if dialog.exec_() == dialog.Accepted:
            self.load_rooms_data()

    def edit_room_status(self):
        """Редактирование статуса номера."""
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
                self.db.cursor.execute(
                    "UPDATE rooms SET status=? WHERE id=?", (new_status, room_id)
                )
                self.db.conn.commit()
                self.load_rooms_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось обновить статус номера: {str(e)}')

    def init_clients(self):
        """Инициализация раздела клиентов и скидок."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок раздела
        title = QLabel('Клиенты и скидки')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        buttons = QHBoxLayout()

        # Кнопка добавления клиента
        btn_add = QPushButton('Добавить клиента')
        btn_add.clicked.connect(self.add_client)

        # Кнопка редактирования скидки
        btn_edit = QPushButton('Редактировать скидку')
        btn_edit.clicked.connect(self.edit_discount)

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_edit)

        layout.addLayout(buttons)

        # Создание таблицы клиентов
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels(
            ['ID', 'ФИО', 'Email', 'Телефон', 'Скидка (%)', 'История бронирований']
        )
        self.clients_table.setSortingEnabled(True)
        layout.addWidget(self.clients_table)

        self.load_clients_data()  # Загрузка данных клиентов
        self.stacked_widget.addWidget(widget)

    def load_clients_data(self):
        """Загрузка данных клиентов в таблицу."""
        try:
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

                    # Окраска скидки
                    if col == 4 and value > 0:  # Столбец скидки
                        item.setBackground(QColor(200, 255, 200))

                    self.clients_table.setItem(row, col, item)
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки клиентов: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить данные клиентов')

    def add_client(self):
        """Добавление нового клиента."""
        dialog = ClientDialog(self.db)
        if dialog.exec_() == dialog.Accepted:
            self.load_clients_data()

    def edit_discount(self):
        """Редактирование скидки клиента."""
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
                self.db.cursor.execute(
                    "UPDATE clients SET discount=? WHERE id=?", (new_discount, client_id)
                )
                self.db.conn.commit()
                self.load_clients_data()
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось обновить скидку: {str(e)}')

    def init_reports(self):
        """Инициализация раздела финансовых отчетов."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок раздела
        title = QLabel('Финансовые отчёты')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        report_params = QHBoxLayout()

        # Выбор типа отчета
        self.report_type = QComboBox()
        self.report_type.addItems(['Доходы', 'Расходы', 'Количество бронирований',
                                   'Популярность услуг'])
        report_params.addWidget(QLabel('Тип отчета:'))
        report_params.addWidget(self.report_type)

        # Выбор даты начала
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        report_params.addWidget(QLabel('С:'))
        report_params.addWidget(self.start_date)

        # Выбор даты окончания
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        report_params.addWidget(QLabel('По:'))
        report_params.addWidget(self.end_date)

        # Кнопка генерации отчета
        btn_generate = QPushButton('Создать отчёт')
        btn_generate.clicked.connect(self.generate_report)
        report_params.addWidget(btn_generate)

        # Кнопка экспорта в PDF
        btn_export = QPushButton('Экспорт в PDF')
        btn_export.clicked.connect(self.export_to_pdf)
        report_params.addWidget(btn_export)

        # Кнопка экспорта в Excel
        btn_export_excel = QPushButton('Экспорт в Excel')
        btn_export_excel.clicked.connect(self.export_to_excel)
        report_params.addWidget(btn_export_excel)

        layout.addLayout(report_params)

        # Поле для отображения результата отчета
        self.report_result = QTextEdit()
        self.report_result.setReadOnly(True)
        layout.addWidget(self.report_result)

        self.stacked_widget.addWidget(widget)

    def generate_report(self):
        """Генерация финансового отчета."""
        report_type = self.report_type.currentText()
        start_date = self.start_date.date().toString('yyyy-MM-dd')
        end_date = self.end_date.date().toString('yyyy-MM-dd')

        try:
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
                    SELECT s.name, COUNT(*) as service_count
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
        """Экспорт отчета в PDF (заглушка)."""
        QMessageBox.information(
            self, 'Информация',
            'Экспорт в PDF будет реализован в будущих версиях'
        )

    def export_to_excel(self):
        """Экспорт отчета в Excel (заглушка)."""
        QMessageBox.information(
            self, 'Информация',
            'Экспорт в Excel будет реализован в будущих версиях'
        )

    def init_analytics(self):
        """Инициализация раздела аналитики и прогнозов."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок раздела
        title = QLabel('Аналитика и прогнозы')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title)

        analysis_params = QHBoxLayout()

        # Выбор типа анализа
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(['Занятость номеров', 'Прогноз доходов', 'Тренды спроса'])
        analysis_params.addWidget(QLabel('Тип анализа:'))
        analysis_params.addWidget(self.analysis_type)

        # Выбор периода прогноза
        self.forecast_period = QComboBox()
        self.forecast_period.addItems(['1 неделя', '1 месяц', '3 месяца', '6 месяцев'])
        analysis_params.addWidget(QLabel('Период прогноза:'))
        analysis_params.addWidget(self.forecast_period)

        # Кнопка генерации прогноза
        btn_generate = QPushButton('Сформировать прогноз')
        btn_generate.clicked.connect(self.generate_forecast)
        analysis_params.addWidget(btn_generate)

        # Кнопка обновления данных
        btn_refresh = QPushButton('Обновить данные')
        btn_refresh.clicked.connect(self.refresh_analytics)
        analysis_params.addWidget(btn_refresh)

        layout.addLayout(analysis_params)

        # Поле для отображения результатов анализа
        self.analytics_result = QTextEdit()
        self.analytics_result.setReadOnly(True)
        layout.addWidget(self.analytics_result)

        self.stacked_widget.addWidget(widget)

    def generate_forecast(self):
        """Генерация прогноза."""
        analysis_type = self.analysis_type.currentText()
        forecast_period = self.forecast_period.currentText()

        try:
            forecast_text = f"Прогноз: {analysis_type}\nПериод: {forecast_period}\n\n"

            if analysis_type == 'Занятость номеров':
                self.db.cursor.execute("""
                    SELECT AVG(COUNT(*)) as avg_bookings
                    FROM bookings
                    WHERE date(check_in_date) BETWEEN date('now', '-3 months') AND date('now')
                    GROUP BY strftime('%W', check_in_date)
                """)
                avg_bookings = self.db.cursor.fetchone()[0] or 0

                forecast_text += (
                    f"Средняя загрузка за последние 3 месяца: {avg_bookings:.1f} "
                    "бронирований в неделю\n"
                )
                forecast_text += "Прогноз на выбранный период: стабильная загрузка\n"

            elif analysis_type == 'Прогноз доходов':
                self.db.cursor.execute("""
                    SELECT AVG(SUM(total_price)) as avg_income
                    FROM bookings
                    WHERE date(created_at) BETWEEN date('now', '-3 months') AND date('now')
                    GROUP BY strftime('%W', created_at)
                """)
                avg_income = self.db.cursor.fetchone()[0] or 0

                forecast_text += (
                    f"Средний доход за последние 3 месяца: {avg_income:.2f} руб. в неделю\n"
                )
                forecast_text += "Прогноз на выбранный период: стабильный доход\n"

            self.analytics_result.setPlainText(forecast_text)
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сформировать прогноз: {str(e)}')

    def refresh_analytics(self):
        """Обновление данных аналитики."""
        self.generate_forecast()

    def show_bookings(self):
        """Отображение раздела бронирований."""
        self.stacked_widget.setCurrentIndex(0)
        self.load_bookings_data()

    def show_rooms(self):
        """Отображение раздела управления номерами."""
        self.stacked_widget.setCurrentIndex(1)
        self.load_rooms_data()

    def show_clients(self):
        """Отображение раздела клиентов и скидок."""
        self.stacked_widget.setCurrentIndex(2)
        self.load_clients_data()

    def show_reports(self):
        """Отображение раздела финансовых отчетов."""
        self.stacked_widget.setCurrentIndex(3)

    def show_analytics(self):
        """Отображение раздела аналитики и прогнозов."""
        self.stacked_widget.setCurrentIndex(4)
        self.generate_forecast()

    def logout(self):
        """Выход из системы и возврат к окну авторизации."""
        from auth_window import AuthWindow
        self.close()
        auth_window = AuthWindow()
        auth_window.show()

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        self.db.close()  # Закрытие соединения с базой данных
        event.accept()