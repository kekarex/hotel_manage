"""
@file auth_window.py
@brief Модуль, реализующий окно авторизации для системы управления отелем.
"""

import logging

import sqlite3

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QStackedWidget

from src.admin_dashboard import AdminDashboard
from src.database import Database
from src.guest_dashboard import GuestDashboard


class AuthWindow(QMainWindow):
    """
    @brief Класс окна авторизации с выбором роли и функционалом входа/регистрации.
    """
    def __init__(self, db):
        """
        @brief Инициализация окна авторизации.
        @param db Экземпляр класса Database для работы с базой данных.
        """
        super().__init__()
        self.db = db
        logging.info(f"AuthWindow получил экземпляр Database: {id(self.db)}")
        self.setWindowTitle("Система управления отелем")
        self.setFixedSize(1000, 800)

        self.setWindowIcon(QIcon("assets/hotel_icon.png"))

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_role_selection()
        self.init_admin_login()
        self.init_guest_login()
        self.init_guest_register()

        self.stacked_widget.setCurrentIndex(0)

    def init_role_selection(self):
        """
        @brief Инициализация экрана выбора роли пользователя.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Добавление логотипа отеля
        '''logo = QLabel()
        pixmap = QPixmap('assets/hotel_logo.png')
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)'''

        welcome_label = QLabel("Добро пожаловать!")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        welcome_label.setFont(font)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 40px; color: #000000;")
        welcome_label.update()
        layout.addWidget(welcome_label)
        layout.addSpacing(20)

        title = QLabel("Выберите вашу роль:")
        font = QFont()
        font.setPointSize(18)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #000000;")
        title.update()
        layout.addWidget(title)

        btn_admin = QPushButton("Администратор")
        btn_admin.setFont(QFont("Arial", 14))
        btn_admin.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        btn_guest = QPushButton("Гость")
        btn_guest.setFont(QFont("Arial", 14))
        btn_guest.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        layout.addWidget(btn_admin)
        layout.addWidget(btn_guest)

        self.stacked_widget.addWidget(widget)

    def init_admin_login(self):
        """
        @brief Инициализация формы входа для администратора.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel("Вход для администратора")
        font = QFont()
        font.setPointSize(24)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: #000000;")
        title.update()
        layout.addWidget(title)

        form = QFormLayout()

        self.admin_username = QLineEdit()
        self.admin_username.setPlaceholderText("Логин")
        form.addRow("Логин:", self.admin_username)

        self.admin_password = QLineEdit()
        self.admin_password.setPlaceholderText("Пароль")
        self.admin_password.setEchoMode(QLineEdit.Password)
        form.addRow("Пароль:", self.admin_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.admin_login)

        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_login)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def init_guest_login(self):
        """
        @brief Инициализация формы входа для гостя.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel("Вход для гостя")
        font = QFont()
        font.setPointSize(24)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: #000000;")
        title.update()
        layout.addWidget(title)

        form = QFormLayout()

        self.guest_username = QLineEdit()
        self.guest_username.setPlaceholderText("Логин")
        form.addRow("Логин:", self.guest_username)

        self.guest_password = QLineEdit()
        self.guest_password.setPlaceholderText("Пароль")
        self.guest_password.setEchoMode(QLineEdit.Password)
        form.addRow("Пароль:", self.guest_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.guest_login)

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_login)
        buttons.addWidget(btn_register)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def init_guest_register(self):
        """
        @brief Инициализация формы регистрации гостя.
        """
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel("Регистрация гостя")
        title.setFont(QFont("Arial", 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()

        self.guest_register_fullname = QLineEdit()
        self.guest_register_fullname.setPlaceholderText("ФИО")
        form.addRow("ФИО:", self.guest_register_fullname)

        self.guest_register_email = QLineEdit()
        self.guest_register_email.setPlaceholderText("Email")
        form.addRow("Email:", self.guest_register_email)

        self.guest_register_phone = QLineEdit()
        self.guest_register_phone.setPlaceholderText("Телефон")
        form.addRow("Телефон:", self.guest_register_phone)

        self.guest_register_username = QLineEdit()
        self.guest_register_username.setPlaceholderText("Логин")
        form.addRow("Логин:", self.guest_register_username)

        self.guest_register_password = QLineEdit()
        self.guest_register_password.setPlaceholderText("Пароль")
        self.guest_register_password.setEchoMode(QLineEdit.Password)
        form.addRow("Пароль:", self.guest_register_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.clicked.connect(self.register_guest)

        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_register)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def clear_fields(self):
        """
        @brief Очистка всех полей ввода.
        """
        self.admin_username.clear()
        self.admin_password.clear()
        self.guest_username.clear()
        self.guest_password.clear()
        self.guest_register_fullname.clear()
        self.guest_register_email.clear()
        self.guest_register_phone.clear()
        self.guest_register_username.clear()
        self.guest_register_password.clear()

    def admin_login(self):
        """
        @brief Обработка входа администратора.
        """
        username = self.admin_username.text().strip()
        password = self.admin_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        try:
            self.db.ensure_connection()
            user = self.db.get_user(username, password)
            if not user:
                logging.warning(f"Неуспешная авторизация администратора: {username}")
                QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")
                return

            if user[3].lower() != "admin":
                logging.warning(f"Недостаточно прав для {username}")
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Недостаточно прав для входа как администратор",
                )
                return

            logging.info(f"Успешная авторизация администратора: {username}")
            self.clear_fields()
            self.open_admin_dashboard(user)

        except Exception as e:
            logging.error(f"Ошибка входа администратора: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def guest_login(self):
        """
        @brief Обработка входа гостя.
        """
        username = self.guest_username.text().strip()
        password = self.guest_password.text().strip()

        if not username or not password:
            logging.warning("Пустой логин или пароль для гостя")
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        try:
            self.db.ensure_connection()
            self.db.cursor.execute(
                """
                SELECT * FROM users WHERE username=? AND password=? AND role='guest'
                AND is_active=1
                """,
                (username, password),
            )
            user = self.db.cursor.fetchone()

            if not user:
                logging.warning(f"Неуспешная авторизация гостя: {username}")
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Неверные учетные данные или недостаточно прав для входа как гость",
                )
                return

            logging.info(f"Успешная авторизация гостя: {username}")
            self.clear_fields()
            self.open_guest_dashboard(user)

        except Exception as e:
            logging.error(f"Ошибка входа гостя: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def register_guest(self):
        """
        @brief Обработка регистрации нового гостя.
        """
        fullname = self.guest_register_fullname.text().strip()
        email = self.guest_register_email.text().strip()
        phone = self.guest_register_phone.text().strip()
        username = self.guest_register_username.text().strip()
        password = self.guest_register_password.text().strip()

        if not all([fullname, email, username, password]):
            logging.warning("Не заполнены обязательные поля при регистрации")
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
            return

        if "@" not in email or "." not in email.split("@")[-1]:
            logging.warning(f"Некорректный email при регистрации: {email}")
            QMessageBox.warning(self, "Ошибка", "Введите корректный email")
            return

        try:
            self.db.ensure_connection()
            success = self.db.add_user(username, password, "guest", fullname, email, phone)
            if success:
                self.db.cursor.execute(
                    "INSERT INTO clients (full_name, email, phone) VALUES (?, ?, ?)",
                    (fullname, email, phone),
                )
                self.db.conn.commit()
                logging.info(f"Успешная регистрация гостя: {username}")
                QMessageBox.information(
                    self,
                    "Успех",
                    "Регистрация прошла успешно. Теперь вы можете войти.",
                )
                self.clear_fields()
                self.stacked_widget.setCurrentIndex(2)
            else:
                logging.warning(f"Пользователь существует: {username} или {email}")
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Пользователь с таким логином или email уже существует",
                )
        except sqlite3.Error as e:
            logging.error(f"Ошибка регистрации гостя: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка при регистрации: {str(e)}")

    def logout(self):
        """
        @brief Выход из системы и очистка полей.
        """
        logging.info("Выход из системы")
        self.clear_fields()
        self.stacked_widget.setCurrentIndex(0)

    def open_admin_dashboard(self, user):
        """
        @brief Открытие панели администратора.
        @param user Кортеж с данными пользователя.
        """
        logging.info(f"Открытие AdminDashboard для пользователя: {user[1]}")
        self.admin_dashboard = AdminDashboard(user, self.db)
        self.admin_dashboard.show()
        self.close()

    def open_guest_dashboard(self, user):
        """
        @brief Открытие панели гостя.
        @param user Кортеж с данными пользователя.
        """
        logging.info(f"Открытие GuestDashboard для пользователя: {user[1]}")
        self.guest_dashboard = GuestDashboard(user, self.db)
        self.guest_dashboard.show()
        self.close()

    def closeEvent(self, event):
        """
        @brief Обработка события закрытия окна.
        @param event Событие закрытия окна.
        """
        logging.info("Закрытие AuthWindow")
        event.accept()