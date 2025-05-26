"""
@file database.py
@brief Модуль для работы с базой данных системы управления отелем.
"""

import logging
import sqlite3
from datetime import datetime


class Database:
    """
    @brief Класс для управления базой данных отеля.
    """
    def __init__(self, db_path: str = "hotel.db"):
        """
        @brief Инициализация соединения с базой данных.
        @param db_path Путь к файлу базы данных SQLite.
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.init_tables()

    def connect(self):
        """
        @brief Установка соединения с базой данных.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logging.info(f"Успешное подключение к базе данных: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def ensure_connection(self):
        """
        @brief Проверка и восстановление соединения с базой данных.
        """
        if self.conn is None or self.cursor is None:
            self.connect()

    def init_tables(self):
        """
        @brief Инициализация таблиц базы данных.
        """
        try:
            self.ensure_connection()
            # Таблица пользователей
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    phone TEXT,
                    is_active INTEGER DEFAULT 1
                )
                """
            )

            # Таблица клиентов
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT,
                    discount INTEGER DEFAULT 0
                )
                """
            )

            # Таблица номеров
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    price_per_night REAL NOT NULL,
                    description TEXT
                )
                """
            )

            # Таблица бронирований
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    room_id INTEGER,
                    guest_name TEXT NOT NULL,
                    guest_email TEXT NOT NULL,
                    guest_phone TEXT,
                    check_in_date TEXT NOT NULL,
                    check_out_date TEXT NOT NULL,
                    total_price REAL,
                    status TEXT DEFAULT 'booked',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (room_id) REFERENCES rooms(id)
                )
                """
            )

            # Таблица услуг
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL
                )
                """
            )

            # Таблица связи бронирований и услуг
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS booking_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id INTEGER,
                    service_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (booking_id) REFERENCES bookings(id),
                    FOREIGN KEY (service_id) REFERENCES services(id)
                )
                """
            )

            # Таблица прогнозов
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    actual_value REAL,
                    predicted_value REAL,
                    error REAL
                )
                """
            )

            self.conn.commit()
            self.insert_default_data()
        except sqlite3.Error as e:
            logging.error(f"Ошибка инициализации таблиц: {e}")
            raise

    def insert_default_data(self):
        """
        @brief Вставка тестовых данных в базу данных.
        """
        try:
            self.ensure_connection()

            # Добавление администратора
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO users (
                    username, password, role, full_name, email, phone
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "admin",
                    "admin123",
                    "admin",
                    "Администратор",
                    "admin@hotel.com",
                    "+79991234567",
                ),
            )

            # Добавление типов номеров
            room_types = [
                ("101", "single", 3000.0, "available", "Одноместный номер"),
                ("102", "double", 5000.0, "available", "Двухместный номер"),
                ("201", "suite", 8000.0, "occupied", "Люкс"),
            ]
            self.cursor.executemany(
                """
                INSERT OR IGNORE INTO rooms (
                    number, type, price_per_night, status, description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                room_types,
            )

            # Добавление услуг
            services = [
                ("Завтрак", 500.0),
                ("Уборка", 300.0),
                ("Трансфер", 1500.0),
            ]
            self.cursor.executemany(
                """
                INSERT OR IGNORE INTO services (name, price) VALUES (?, ?)
                """,
                services,
            )

            self.conn.commit()
            logging.info("Тестовые данные успешно добавлены")
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления тестовых данных: {e}")

    def add_user(self, username, password, role, full_name=None, email=None, phone=None):
        """
        @brief Добавление нового пользователя в базу данных.
        @param username Логин пользователя.
        @param password Пароль пользователя.
        @param role Роль пользователя (admin/guest).
        @param full_name Полное имя пользователя.
        @param email Email пользователя.
        @param phone Телефон пользователя.
        @return bool Успешность операции.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                SELECT id FROM users WHERE username = ? OR email = ?
                """,
                (username, email),
            )
            if self.cursor.fetchone():
                return False

            self.cursor.execute(
                """
                INSERT INTO users (
                    username, password, role, full_name, email, phone
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, password, role, full_name, email, phone),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления пользователя: {e}")
            return False

    def get_user(self, username, password):
        """
        @brief Получение данных пользователя по логину и паролю.
        @param username Логин пользователя.
        @param password Пароль пользователя.
        @return Кортеж с данными пользователя или None, если пользователь не найден.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                SELECT * FROM users WHERE username = ? AND password = ? AND is_active = 1
                """,
                (username, password),
            )
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения данных пользователя: {e}")
            return None

    def get_time_series(self, data_type, start_date, end_date):
        """
        @brief Получение временного ряда для аналитики.
        @param data_type Тип данных ('bookings' или 'revenue').
        @param start_date Начальная дата.
        @param end_date Конечная дата.
        @return Список кортежей (месяц, значение).
        """
        try:
            self.ensure_connection()
            if data_type == "bookings":
                self.cursor.execute(
                    """
                    SELECT strftime('%Y-%m', created_at) as month,
                           COUNT(*) as value
                    FROM bookings
                    WHERE date(created_at) BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY month
                    """,
                    (start_date, end_date),
                )
            else:  # revenue
                self.cursor.execute(
                    """
                    SELECT strftime('%Y-%m', created_at) as month,
                           SUM(total_price) as value
                    FROM bookings
                    WHERE date(created_at) BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY month
                    """,
                    (start_date, end_date),
                )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения временного ряда: {e}")
            return []

    def save_forecast(self, month, data_type, actual_value, predicted_value, error):
        """
        @brief Сохранение прогноза в базу данных.
        @param month Месяц прогноза (формат 'YYYY-MM').
        @param data_type Тип данных ('bookings' или 'revenue').
        @param actual_value Фактическое значение (может быть NULL).
        @param predicted_value Прогнозируемое значение.
        @param error Ошибка прогноза.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                INSERT INTO forecasts (
                    month, data_type, actual_value, predicted_value, error
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (month, data_type, actual_value, predicted_value, error),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка сохранения прогноза: {e}")

    def get_bookings_by_user(self, user_id):
        """
        @brief Получение бронирований пользователя.
        @param user_id ID пользователя.
        @return Список бронирований.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                SELECT b.*, r.number, r.type
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.user_id = ?
                ORDER BY b.check_in_date DESC
                """,
                (user_id,),
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения бронирований пользователя: {e}")
            return []

    def get_available_rooms(self, check_in_date, check_out_date, room_type=None):
        """
        @brief Получение списка доступных номеров на указанные даты.
        @param check_in_date Дата заезда.
        @param check_out_date Дата выезда.
        @param room_type Тип номера (опционально).
        @return Список доступных номеров.
        """
        try:
            self.ensure_connection()
            query = """
                SELECT r.*
                FROM rooms r
                WHERE r.status = 'available'
                AND r.id NOT IN (
                    SELECT room_id
                    FROM bookings
                    WHERE status NOT IN ('cancelled', 'checked_out')
                    AND (
                        (check_in_date <= ? AND check_out_date >= ?)
                        OR (check_in_date >= ? AND check_in_date <= ?)
                        OR (check_out_date >= ? AND check_out_date <= ?)
                    )
                )
            """
            params = (
                check_out_date,
                check_in_date,
                check_in_date,
                check_out_date,
                check_in_date,
                check_out_date,
            )
            if room_type:
                query += " AND r.type = ?"
                params += (room_type,)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения доступных номеров: {e}")
            return []

    def get_room_by_id(self, room_id):
        """
        @brief Получение информации о номере по ID.
        @param room_id ID номера.
        @return Кортеж с данными номера.
        """
        try:
            self.ensure_connection()
            self.cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения данных номера: {e}")
            return None

    def get_services(self):
        """
        @brief Получение списка всех услуг.
        @return Список услуг.
        """
        try:
            self.ensure_connection()
            self.cursor.execute("SELECT * FROM services")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения услуг: {e}")
            return []

    def add_booking(self, booking_data, services):
        """
        @brief Добавление нового бронирования.
        @param booking_data Данные бронирования.
        @param services Список услуг для бронирования.
        @return ID нового бронирования.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                INSERT INTO bookings (
                    user_id, room_id, guest_name, guest_email, guest_phone,
                    check_in_date, check_out_date, total_price, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                booking_data,
            )
            booking_id = self.cursor.lastrowid

            for service_id, quantity in services:
                self.cursor.execute(
                    """
                    INSERT INTO booking_services (booking_id, service_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (booking_id, service_id, quantity),
                )

            self.cursor.execute(
                """
                UPDATE rooms SET status = 'occupied' WHERE id = ?
                """,
                (booking_data[1],),
            )

            self.conn.commit()
            return booking_id
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления бронирования: {e}")
            self.conn.rollback()
            return None

    def update_booking(self, booking_id, booking_data, services):
        """
        @brief Обновление существующего бронирования.
        @param booking_id ID бронирования.
        @param booking_data Обновленные данные бронирования.
        @param services Обновленный список услуг.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                UPDATE bookings
                SET room_id = ?, guest_name = ?, guest_email = ?,
                    guest_phone = ?, check_in_date = ?, check_out_date = ?,
                    total_price = ?, status = ?
                WHERE id = ?
                """,
                booking_data + (booking_id,),
            )

            self.cursor.execute(
                """
                DELETE FROM booking_services WHERE booking_id = ?
                """,
                (booking_id,),
            )

            for service_id, quantity in services:
                self.cursor.execute(
                    """
                    INSERT INTO booking_services (booking_id, service_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (booking_id, service_id, quantity),
                )

            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка обновления бронирования: {e}")
            self.conn.rollback()

    def get_booking_services(self, booking_id):
        """
        @brief Получение услуг, связанных с бронированием.
        @param booking_id ID бронирования.
        @return Список услуг.
        """
        try:
            self.ensure_connection()
            self.cursor.execute(
                """
                SELECT service_id, quantity
                FROM booking_services
                WHERE booking_id = ?
                """,
                (booking_id,),
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения услуг бронирования: {e}")
            return []

    def close(self):
        """
        @brief Закрытие соединения с базой данных.
        """
        if self.conn:
            self.conn.close()
            logging.info("Соединение с базой данных закрыто")
            self.conn = None
            self.cursor = None