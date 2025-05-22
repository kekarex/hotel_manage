"""
@file database.py
@brief Модуль, реализующий класс для работы с базой данных SQLite для системы управления отелем.
"""

import sqlite3
import logging
from datetime import datetime, timedelta


class Database:
    """
    @brief Класс для работы с базой данных SQLite для системы управления отелем.
    """
    def __init__(self, db_path='hotel.db'):
        """
        @brief Инициализация соединения с базой данных и создание таблиц.
        @param db_path Путь к файлу базы данных (по умолчанию 'hotel.db').
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.ensure_connection()
        self.create_tables()
        try:
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'is_active' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
                self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка проверки/добавления столбца is_active: {e}")
            raise
        self.check_data_integrity()
        self.create_default_admin()

    def ensure_connection(self):
        """
        @brief Проверка и переоткрытие соединения, если оно закрыто или отсутствует.
        """
        try:
            if self.conn is None or self.cursor is None:
                raise AttributeError("Соединение или курсор не инициализированы")
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            logging.debug("Соединение с базой данных активно")
        except (sqlite3.Error, AttributeError) as e:
            logging.warning(f"Переоткрытие соединения: {e}")
            if self.conn:
                try:
                    self.conn.close()
                except sqlite3.Error:
                    pass
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logging.info("Новое соединение с базой данных установлено")

    def create_tables(self):
        """
        @brief Создание всех необходимых таблиц в базе данных.
        """
        self.ensure_connection()
        self.cursor.execute("PRAGMA foreign_keys = ON")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'guest')),
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                floor INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                price_per_night REAL NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'available' CHECK(status IN ('available', 'occupied',
                                                                'cleaning', 'maintenance')),
                image_path TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                guest_name TEXT NOT NULL,
                guest_phone TEXT NOT NULL,
                guest_email TEXT,
                check_in_date TEXT NOT NULL,
                check_out_date TEXT NOT NULL,
                adults INTEGER NOT NULL,
                children INTEGER DEFAULT 0,
                status TEXT DEFAULT 'reserved' CHECK(status IN ('reserved', 'checked_in',
                                                               'checked_out', 'cancelled')),
                total_price REAL NOT NULL,
                deposit REAL DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                discount INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('bookings', 'revenue')),
                actual_value REAL,
                forecast_value REAL NOT NULL,
                error REAL
            )
        """)

        self.conn.commit()

    def check_data_integrity(self):
        """
        @brief Проверка целостности базы данных.
        """
        self.ensure_connection()
        try:
            self.cursor.execute("PRAGMA integrity_check")
            result = self.cursor.fetchone()
            if result[0] != 'ok':
                logging.error(f"Ошибка проверки целостности базы данных: {result}")
                raise sqlite3.Error("Проверка целостности базы данных не пройдена")
        except sqlite3.Error as e:
            logging.error(f"Ошибка проверки целостности: {e}")
            raise

    def create_default_admin(self):
        """
        @brief Создание администраторов по умолчанию, если они отсутствуют.
        """
        self.ensure_connection()
        admins = [
            ('admin', 'admin123', 'Главный администратор', 'admin@hotel.com'),
            ('manager1', 'mgrpass1', 'Менеджер Иванов', 'manager1@hotel.com'),
            ('manager2', 'mgrpass2', 'Менеджер Петров', 'manager2@hotel.com'),
            ('director', 'dirpass1', 'Директор Сидоров', 'director@hotel.com')
        ]

        for username, password, full_name, email in admins:
            try:
                self.cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                if not self.cursor.fetchone():
                    self.cursor.execute(
                        """
                        INSERT INTO users (username, password, role, full_name, email, is_active)
                        VALUES (?, ?, 'admin', ?, ?, 1)
                        """, (username, password, full_name, email)
                    )
                    logging.info(f"Создан администратор по умолчанию: {username}")
            except sqlite3.Error as e:
                logging.error(f"Ошибка создания администратора {username}: {e}")

        self.conn.commit()

    def add_user(self, username, password, role, full_name, email, phone=None):
        """
        @brief Добавление нового пользователя в базу данных.
        @param username Логин пользователя.
        @param password Пароль пользователя.
        @param role Роль пользователя ('admin' или 'guest').
        @param full_name Полное имя пользователя.
        @param email Электронная почта пользователя.
        @param phone Телефон пользователя (опционально).
        @return bool Успешность операции (True при успехе, False при ошибке).
        """
        self.ensure_connection()
        try:
            self.cursor.execute(
                """
                INSERT INTO users (username, password, role, full_name, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (username, password, role, full_name, email, phone)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Ошибка добавления пользователя: {e}")
            return False

    def get_user(self, username, password):
        """
        @brief Получение данных пользователя из базы данных.
        @param username Логин пользователя.
        @param password Пароль пользователя.
        @return tuple Кортеж с данными пользователя или None, если пользователь не найден.
        """
        self.ensure_connection()
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?", (username, password)
            )
            user = self.cursor.fetchone()
            if user:
                logging.info(f"Найден пользователь: {username}")
            else:
                logging.warning(f"Пользователь не найден: {username}")
            return user
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения пользователя: {e}")
            return None

    def get_available_rooms(self, check_in, check_out, room_type=None, capacity=None):
        """
        @brief Получение списка доступных номеров на указанные даты.
        @param check_in Дата заезда (строка в формате 'yyyy-MM-dd').
        @param check_out Дата выезда (строка в формате 'yyyy-MM-dd').
        @param room_type Тип номера (опционально).
        @param capacity Вместимость номера (опционально).
        @return list Список кортежей с данными доступных номеров.
        """
        self.ensure_connection()
        try:
            query = """
                SELECT * FROM rooms 
                WHERE status='available'
                AND id NOT IN (
                    SELECT room_id FROM bookings 
                    WHERE (
                        (check_in_date < ? AND check_out_date > ?) OR
                        (check_in_date >= ? AND check_in_date < ?) OR
                        (check_out_date > ? AND check_out_date <= ?)
                    )
                    AND status IN ('reserved', 'checked_in')
                )
            """
            params = [check_out, check_in, check_in, check_out, check_in, check_out]

            if room_type:
                query += " AND type=?"
                params.append(room_type)
            if capacity:
                query += " AND capacity>=?"
                params.append(capacity)

            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения доступных номеров: {e}")
            return []

    def get_time_series(self, data_type: str, start_date: str, end_date: str) -> list[tuple[str, float]]:
        """
        @brief Извлечение временного ряда для бронирований или дохода.
        @param data_type Тип данных ('bookings' или 'revenue').
        @param start_date Начальная дата (строка в формате 'yyyy-MM-dd').
        @param end_date Конечная дата (строка в формате 'yyyy-MM-dd').
        @return list Список кортежей (месяц, значение) для временного ряда.
        """
        self.ensure_connection()
        try:
            if data_type == "bookings":
                query = """
                    SELECT strftime('%Y-%m', check_in_date) AS month, COUNT(*) AS value
                    FROM bookings
                    WHERE check_in_date BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', check_in_date)
                    ORDER BY month
                """
            elif data_type == "revenue":
                query = """
                    SELECT strftime('%Y-%m', check_in_date) AS month, SUM(total_price) AS value
                    FROM bookings
                    WHERE check_in_date BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', check_in_date)
                    ORDER BY month
                """
            else:
                return []
            self.cursor.execute(query, (start_date, end_date))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения временного ряда: {e}")
            return []

    def save_forecast(self, forecast_date: str, data_type: str, actual_value: float, forecast_value: float, error: float):
        """
        @brief Сохранение результата прогноза.
        @param forecast_date Дата прогноза (строка в формате 'yyyy-MM').
        @param data_type Тип данных ('bookings' или 'revenue').
        @param actual_value Фактическое значение (опционально).
        @param forecast_value Прогнозируемое значение.
        @param error Ошибка прогноза (опционально).
        """
        self.ensure_connection()
        try:
            self.cursor.execute(
                """
                INSERT INTO forecasts (forecast_date, type, actual_value, forecast_value, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (forecast_date, data_type, actual_value, forecast_value, error)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка сохранения прогноза: {e}")

    def get_services_cost(self, booking_id: int) -> float:
        """
        @brief Получение суммарной стоимости услуг для бронирования.
        @param booking_id Идентификатор бронирования.
        @return float Суммарная стоимость услуг.
        """
        self.ensure_connection()
        try:
            self.cursor.execute("""
                SELECT SUM(s.price * bs.quantity)
                FROM booking_services bs
                JOIN services s ON bs.service_id = s.id
                WHERE bs.booking_id = ?
            """, (booking_id,))
            result = self.cursor.fetchone()[0]
            return result if result else 0.0
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения стоимости услуг: {e}")
            return 0.0

    def calculate_total_price(self, room_id: int, check_in_date: str, check_out_date: str, guest_email: str, service_ids: list[tuple[int, int]]) -> float:
        """
        @brief Расчет общей стоимости бронирования с учетом номера, скидки и услуг.
        @param room_id Идентификатор номера.
        @param check_in_date Дата заезда (строка в формате 'yyyy-MM-dd').
        @param check_out_date Дата выезда (строка в формате 'yyyy-MM-dd').
        @param guest_email Email гостя для проверки скидки.
        @param service_ids Список кортежей (ID услуги, количество).
        @return float Общая стоимость бронирования.
        """
        self.ensure_connection()
        try:
            # Получение цены номера
            self.cursor.execute("SELECT price_per_night FROM rooms WHERE id = ?", (room_id,))
            price_per_night = self.cursor.fetchone()[0]

            # Расчет количества ночей
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
            nights = (check_out - check_in).days

            # Получение скидки клиента
            self.cursor.execute("SELECT discount FROM clients WHERE email = ?", (guest_email,))
            discount = self.cursor.fetchone()
            discount = discount[0] if discount else 0

            # Стоимость номера с учетом скидки
            room_cost = price_per_night * nights * (1 - discount / 100)

            # Стоимость услуг
            services_cost = 0.0
            if service_ids:
                for service_id, quantity in service_ids:
                    self.cursor.execute("SELECT price FROM services WHERE id = ?", (service_id,))
                    service_price = self.cursor.fetchone()[0]
                    services_cost += service_price * quantity

            return round(room_cost + services_cost, 2)
        except sqlite3.Error as e:
            logging.error(f"Ошибка расчета общей стоимости: {e}")
            raise

    def close(self):
        """
        @brief Закрытие соединения с базой данных.
        """
        logging.info("Закрытие соединения с базой данных")
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                self.cursor = None
            except sqlite3.Error as e:
                logging.error(f"Ошибка при закрытии соединения: {e}")