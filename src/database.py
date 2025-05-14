import sqlite3
import logging
from datetime import datetime, timedelta


class Database:
    """Класс для работы с базой данных SQLite для системы управления отелем."""

    def __init__(self):
        """Инициализация соединения с базой данных и создание таблиц."""
        self.conn = sqlite3.connect('hotel.db')  # Подключение к базе данных
        self.cursor = self.conn.cursor()  # Создание курсора
        self.create_tables()  # Создание таблиц
        try:
            # Проверка наличия столбца is_active в таблице users
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'is_active' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
                self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка проверки/добавления столбца is_active: {e}")
            raise
        self.check_data_integrity()  # Проверка целостности данных
        self.create_default_admin()  # Создание администраторов по умолчанию

    def create_tables(self):
        """Создание всех необходимых таблиц в базе данных."""
        self.cursor.execute("PRAGMA foreign_keys = ON")  # Включение поддержки внешних ключей

        # Создание таблицы пользователей
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

        # Создание таблицы номеров
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

        # Создание таблицы бронирований
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

        # Создание таблицы услуг
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Создание таблицы связи бронирований и услуг
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

        # Создание таблицы клиентов
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

        # Создание таблицы отзывов
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

        self.conn.commit()  # Сохранение изменений

    def check_data_integrity(self):
        """Проверка целостности базы данных."""
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
        """Создание администраторов по умолчанию, если они отсутствуют."""
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

        self.conn.commit()  # Сохранение изменений

    def add_user(self, username, password, role, full_name, email, phone=None):
        """Добавление нового пользователя в базу данных."""
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
        """Получение данных пользователя из базы данных."""
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?", (username, password)
            )
            user = self.cursor.fetchone()
            if user:
                logging.info(f"Найден пользователь: {user}")
            else:
                logging.warning(f"Пользователь не найден: {username}")
            return user
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения пользователя: {e}")
            return None

    def get_available_rooms(self, check_in, check_out, room_type=None, capacity=None):
        """Получение списка доступных номеров на указанные даты."""
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

    def close(self):
        """Закрытие соединения с базой данных."""
        self.conn.close()