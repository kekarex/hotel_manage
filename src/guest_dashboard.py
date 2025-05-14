import sqlite3
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QComboBox, QDateEdit,
                             QCheckBox, QTextEdit, QPushButton, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QFormLayout, QTableWidget,
                             QTableWidgetItem, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap, QColor


class GuestDashboard(QMainWindow):
    """Панель гостя для управления бронированиями и отзывами."""

    def __init__(self, user, db):
        """Инициализация панели гостя."""
        super().__init__()
        self.user = user  # Сохранение данных пользователя
        self.db = db  # Сохранение объекта базы данных
        self.setWindowTitle(f'Личный кабинет гостя ({user[4]})')  # Установка заголовка
        self.setFixedSize(1000, 800)  # Установка фиксированного размера окна

        self.init_ui()  # Инициализация интерфейса
        self.load_data()  # Загрузка данных

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
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
        """Инициализация вкладки бронирования номера."""
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

        self.transfer = QCheckBox('Трансфер')
        self.spa = QCheckBox('Спа-процедуры')
        self.excursions = QCheckBox('Экскурсии')
        self.extra_bed = QCheckBox('Дополнительная кровать')
        self.gym = QCheckBox('Спортзал')
        self.equipment = QCheckBox('Прокат инвентаря')

        services_layout.addWidget(self.transfer)
        services_layout.addWidget(self.spa)
        services_layout.addWidget(self.excursions)
        services_layout.addWidget(self.extra_bed)
        services_layout.addWidget(self.gym)
        services_layout.addWidget(self.equipment)

        services_group.setLayout(services_layout)
        form_layout.addWidget(services_group)

        # Группа выбора питания
        meals_group = QGroupBox('Тип питания')
        meals_layout = QVBoxLayout()

        self.meals = QComboBox()
        self.meals.addItems(['Без питания', 'Только завтрак', 'Полупансион',
                             'Полный пансион'])
        meals_layout.addWidget(self.meals)

        meals_group.setLayout(meals_layout)
        form_layout.addWidget(meals_group)

        buttons = QHBoxLayout()

        # Кнопка расчета стоимости
        btn_calculate = QPushButton('Рассчитать стоимость')
        btn_calculate.clicked.connect(self.calculate_cost)
        buttons.addWidget(btn_calculate)

        # Кнопка подтверждения бронирования
        self.btn_book = QPushButton('Подтвердить бронирование')
        self.btn_book.clicked.connect(self.confirm_booking)
        self.btn_book.setEnabled(False)
        buttons.addWidget(self.btn_book)

        form_layout.addLayout(buttons)
        form_layout.addStretch()

        # Группа расчета стоимости
        self.cost_group = QGroupBox('Расчет стоимости')
        self.cost_layout = QVBoxLayout()

        self.cost_details = QLabel('Здесь будет отображен расчет стоимости')
        self.cost_details.setWordWrap(True)
        self.cost_layout.addWidget(self.cost_details)

        self.total_cost = QLabel('Итого: 0 руб.')
        self.total_cost.setFont(QFont('Arial', 14, QFont.Bold))
        self.cost_layout.addWidget(self.total_cost)

        self.cost_group.setLayout(self.cost_layout)
        self.cost_group.setVisible(False)

        layout.addLayout(form_layout, 70)
        layout.addWidget(self.cost_group, 30)

        self.tabs.addTab(tab, 'Бронирование номера')

    def calculate_cost(self):
        """Расчет стоимости бронирования."""
        room_type = self.room_type.currentText()
        check_in = self.check_in.date().toString('yyyy-MM-dd')
        check_out = self.check_out.date().toString('yyyy-MM-dd')

        try:
            self.db.cursor.execute(
                "SELECT price_per_night FROM rooms WHERE type=? LIMIT 1", (room_type,)
            )
            price_per_night = self.db.cursor.fetchone()[0]

            nights = self.check_in.date().daysTo(self.check_out.date())
            if nights <= 0:
                QMessageBox.warning(
                    self, 'Ошибка',
                    'Дата выезда должна быть позже даты заезда'
                )
                return

            base_cost = price_per_night * nights

            services_cost = 0
            services_text = "Включенные услуги:\n"

            if self.transfer.isChecked():
                services_cost += 1500
                services_text += "- Трансфер: 1500 руб.\n"
            if self.spa.isChecked():
                services_cost += 3000
                services_text += "- Спа-процедуры: 3000 руб.\n"
            if self.excursions.isChecked():
                services_cost += 2000
                services_text += "- Экскурсии: 2000 руб.\n"
            if self.extra_bed.isChecked():
                services_cost += 1000 * nights
                services_text += f"- Доп. кровать: {1000 * nights} руб.\n"
            if self.gym.isChecked():
                services_cost += 500 * nights
                services_text += f"- Спортзал: {500 * nights} руб.\n"
            if self.equipment.isChecked():
                services_cost += 800 * nights
                services_text += f"- Прокат инвентаря: {800 * nights} руб.\n"

            meals_cost = 0
            meals_type = self.meals.currentText()
            if meals_type == 'Только завтрак':
                meals_cost = 500 * nights
            elif meals_type == 'Полупансион':
                meals_cost = 1500 * nights
            elif meals_type == 'Полный пансион':
                meals_cost = 2500 * nights

            if meals_cost > 0:
                services_text += f"- Питание ({meals_type}): {meals_cost} руб.\n"

            total_cost = base_cost + services_cost + meals_cost

            self.db.cursor.execute(
                "SELECT discount FROM clients WHERE email=?", (self.user[5],)
            )
            discount = self.db.cursor.fetchone()

            if discount and discount[0] > 0:
                discount_amount = total_cost * discount[0] / 100
                total_cost -= discount_amount
                services_text += f"\nСкидка {discount[0]}%: -{discount_amount:.2f} руб.\n"

            cost_text = f"Категория номера: {room_type}\n"
            cost_text += f"Даты: {check_in} - {check_out} ({nights} ночей)\n"
            cost_text += f"Базовая стоимость: {base_cost:.2f} руб.\n\n"
            cost_text += services_text
            cost_text += f"\nИтого к оплате: {total_cost:.2f} руб."

            self.cost_details.setText(cost_text)
            self.total_cost.setText(f"Итого: {total_cost:.2f} руб.")
            self.cost_group.setVisible(True)
            self.btn_book.setEnabled(True)

        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось рассчитать стоимость: {str(e)}')

    def confirm_booking(self):
        """Подтверждение бронирования (заглушка)."""
        QMessageBox.information(self, 'Успех', 'Бронирование успешно создано!')
        self.load_my_bookings()

    def init_my_bookings_tab(self):
        """Инициализация вкладки моих бронирований."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Создание таблицы бронирований
        self.my_bookings_table = QTableWidget()
        self.my_bookings_table.setColumnCount(6)
        self.my_bookings_table.setHorizontalHeaderLabels(
            ['ID', 'Даты', 'Тип номера', 'Услуги', 'Стоимость', 'Статус']
        )
        self.my_bookings_table.setSortingEnabled(True)
        layout.addWidget(self.my_bookings_table)

        # Кнопка отмены бронирования
        btn_cancel = QPushButton('Отменить бронирование')
        btn_cancel.clicked.connect(self.cancel_my_booking)
        layout.addWidget(btn_cancel)

        self.tabs.addTab(tab, 'Мои бронирования')

    def load_my_bookings(self):
        """Загрузка бронирований пользователя."""
        try:
            self.db.cursor.execute("""
                SELECT b.id, 
                       b.check_in_date || ' - ' || b.check_out_date as dates,
                       r.type,
                       (SELECT GROUP_CONCAT(s.name, ', ') 
                        FROM booking_services bs 
                        JOIN services s ON bs.service_id = s.id 
                        WHERE bs.booking_id = b.id) as services,
                       b.total_price,
                       b.status
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.guest_email = ?
                ORDER BY b.check_in_date DESC
            """, (self.user[5],))
            bookings = self.db.cursor.fetchall()

            self.my_bookings_table.setRowCount(len(bookings))
            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking):
                    item = QTableWidgetItem(str(value if value is not None else ''))

                    # Окраска статуса
                    if col == 5:  # Столбец статуса
                        if value == 'cancelled':
                            item.setBackground(QColor(255, 200, 200))
                        elif value == 'checked_in':
                            item.setBackground(QColor(200, 255, 200))

                    self.my_bookings_table.setItem(row, col, item)
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить бронирования: {str(e)}')

    def cancel_my_booking(self):
        """Отмена бронирования."""
        selected_row = self.my_bookings_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование для отмены')
            return

        booking_id = self.my_bookings_table.item(selected_row, 0).text()
        status = self.my_bookings_table.item(selected_row, 5).text()

        if status == 'cancelled':
            QMessageBox.warning(self, 'Ошибка', 'Это бронирование уже отменено')
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
                self.load_my_bookings()
                QMessageBox.information(self, 'Успех', 'Бронирование успешно отменено')
            except sqlite3.Error as e:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось отменить бронирование: {str(e)}')

    def init_review_tab(self):
        """Инициализация вкладки отзывов."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        review_form = QFormLayout()

        # Выбор бронирования для отзыва
        self.review_booking = QComboBox()
        review_form.addRow('Бронирование:', self.review_booking)

        # Выбор оценки
        self.rating = QComboBox()
        self.rating.addItems(['5 - Отлично', '4 - Хорошо', '3 - Удовлетворительно',
                              '2 - Плохо', '1 - Ужасно'])
        review_form.addRow('Оценка:', self.rating)

        # Поле для текста отзыва
        self.review_text = QTextEdit()
        self.review_text.setPlaceholderText('Напишите ваш отзыв здесь...')
        review_form.addRow('Отзыв:', self.review_text)

        layout.addLayout(review_form)

        # Кнопка отправки отзыва
        btn_submit = QPushButton('Отправить отзыв')
        btn_submit.clicked.connect(self.submit_review)
        layout.addWidget(btn_submit)

        self.tabs.addTab(tab, 'Оставить отзыв')

    def load_review_bookings(self):
        """Загрузка бронирований, доступных для отзыва."""
        try:
            self.db.cursor.execute("""
                SELECT b.id, r.type || ' (' || b.check_in_date || ' - ' || b.check_out_date || ')'
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.guest_email = ? AND b.status = 'checked_out'
                AND NOT EXISTS (SELECT 1 FROM reviews WHERE booking_id = b.id)
                ORDER BY b.check_out_date DESC
            """, (self.user[5],))
            bookings = self.db.cursor.fetchall()

            self.review_booking.clear()
            for booking in bookings:
                self.review_booking.addItem(booking[1], booking[0])
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить бронирования: {str(e)}')

    def submit_review(self):
        """Отправка отзыва о бронировании."""
        booking_id = self.review_booking.currentData()
        if not booking_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование для отзыва')
            return

        rating = 5 - self.rating.currentIndex()
        comment = self.review_text.toPlainText()

        try:
            self.db.cursor.execute(
                "INSERT INTO reviews (booking_id, rating, comment) VALUES (?, ?, ?)",
                (booking_id, rating, comment if comment else None)
            )
            self.db.conn.commit()
            QMessageBox.information(self, 'Успех', 'Спасибо за ваш отзыв!')
            self.review_text.clear()
            self.load_review_bookings()
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось отправить отзыв: {str(e)}')

    def init_offers_tab(self):
        """Инициализация вкладки персональных предложений."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Поле для отображения предложений
        self.offers_text = QTextEdit()
        self.offers_text.setReadOnly(True)
        layout.addWidget(self.offers_text)

        self.tabs.addTab(tab, 'Персональные предложения')

    def load_offers(self):
        """Загрузка персональных предложений для пользователя."""
        try:
            self.db.cursor.execute(
                "SELECT discount FROM clients WHERE email=?", (self.user[5],)
            )
            discount = self.db.cursor.fetchone()

            offers_text = "Специальные предложения для вас:\n\n"

            if discount and discount[0] > 0:
                offers_text += f"- Ваша персональная скидка: {discount[0]}%\n"
            else:
                offers_text += "- Станьте постоянным клиентом и получите скидку!\n"

            current_month = QDate.currentDate().month()
            if current_month in [12, 1, 2]:
                offers_text += "\nЗимние предложения:\n"
                offers_text += "- Скидка 15% на номера категории Люкс\n"
                offers_text += "- Бесплатный спа-комплекс при бронировании от 5 ночей\n"
            elif current_month in [6, 7, 8]:
                offers_text += "\nЛетние предложения:\n"
                offers_text += "- Скидка 10% на все номера\n"
                offers_text += "- Бесплатные экскурсии при бронировании от 7 ночей\n"

            self.offers_text.setPlainText(offers_text)
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить предложения: {str(e)}')

    def load_data(self):
        """Загрузка всех данных для панели."""
        self.load_my_bookings()
        self.load_review_bookings()
        self.load_offers()

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        self.db.close()  # Закрытие соединения с базой данных
        event.accept()