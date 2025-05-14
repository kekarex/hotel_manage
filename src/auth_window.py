import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox,
                             QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import sqlite3
from database import Database
from admin_dashboard import AdminDashboard
from guest_dashboard import GuestDashboard


class AuthWindow(QMainWindow):
    """Окно авторизации с выбором роли и функционалом входа/регистрации."""

    def __init__(self):
        """Инициализация окна авторизации."""
        super().__init__()
        self.db = Database()  # Инициализация базы данных
        self.setWindowTitle('Система управления отелем')  # Установка заголовка окна
        self.setFixedSize(1000, 800)  # Установка фиксированного размера окна

        self.stacked_widget = QStackedWidget()  # Создание виджета для переключения экранов
        self.setCentralWidget(self.stacked_widget)

        self.init_role_selection()  # Инициализация экрана выбора роли
        self.init_admin_login()  # Инициализация формы входа для администратора
        self.init_guest_login()  # Инициализация формы входа для гостя
        self.init_guest_register()  # Инициализация формы регистрации гостя

        self.stacked_widget.setCurrentIndex(0)  # Установка начального экрана

    def init_role_selection(self):
        """Инициализация экрана выбора роли."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Добавление логотипа отеля
        logo = QLabel()
        pixmap = QPixmap('assets/hotel_logo.png')
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)

        # Заголовок экрана
        title = QLabel('Выберите вашу роль:')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Кнопка для администратора
        btn_admin = QPushButton('Администратор')
        btn_admin.setFont(QFont('Arial', 14))
        btn_admin.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        # Кнопка для гостя
        btn_guest = QPushButton('Гость')
        btn_guest.setFont(QFont('Arial', 14))
        btn_guest.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        layout.addWidget(btn_admin)
        layout.addWidget(btn_guest)

        self.stacked_widget.addWidget(widget)

    def init_admin_login(self):
        """Инициализация формы входа для администратора."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок формы
        title = QLabel('Вход для администратора')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()

        # Поле для логина
        self.admin_username = QLineEdit()
        self.admin_username.setPlaceholderText('Логин')
        form.addRow('Логин:', self.admin_username)

        # Поле для пароля
        self.admin_password = QLineEdit()
        self.admin_password.setPlaceholderText('Пароль')
        self.admin_password.setEchoMode(QLineEdit.Password)
        form.addRow('Пароль:', self.admin_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        # Кнопка входа
        btn_login = QPushButton('Войти')
        btn_login.clicked.connect(self.admin_login)

        # Кнопка возврата
        btn_back = QPushButton('Назад')
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_login)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def init_guest_login(self):
        """Инициализация формы входа для гостя."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок формы
        title = QLabel('Вход для гостя')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()

        # Поле для логина
        self.guest_username = QLineEdit()
        self.guest_username.setPlaceholderText('Логин')
        form.addRow('Логин:', self.guest_username)

        # Поле для пароля
        self.guest_password = QLineEdit()
        self.guest_password.setPlaceholderText('Пароль')
        self.guest_password.setEchoMode(QLineEdit.Password)
        form.addRow('Пароль:', self.guest_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        # Кнопка возврата
        btn_back = QPushButton('Назад')
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        # Кнопка входа
        btn_login = QPushButton('Войти')
        btn_login.clicked.connect(self.guest_login)

        # Кнопка регистрации
        btn_register = QPushButton('Зарегистрироваться')
        btn_register.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_login)
        buttons.addWidget(btn_register)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def init_guest_register(self):
        """Инициализация формы регистрации гостя."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Заголовок формы
        title = QLabel('Регистрация гостя')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()

        # Поле для ФИО
        self.guest_register_fullname = QLineEdit()
        self.guest_register_fullname.setPlaceholderText('ФИО')
        form.addRow('ФИО:', self.guest_register_fullname)

        # Поле для email
        self.guest_register_email = QLineEdit()
        self.guest_register_email.setPlaceholderText('Email')
        form.addRow('Email:', self.guest_register_email)

        # Поле для телефона
        self.guest_register_phone = QLineEdit()
        self.guest_register_phone.setPlaceholderText('Телефон')
        form.addRow('Телефон:', self.guest_register_phone)

        # Поле для логина
        self.guest_register_username = QLineEdit()
        self.guest_register_username.setPlaceholderText('Логин')
        form.addRow('Логин:', self.guest_register_username)

        # Поле для пароля
        self.guest_register_password = QLineEdit()
        self.guest_register_password.setPlaceholderText('Пароль')
        self.guest_register_password.setEchoMode(QLineEdit.Password)
        form.addRow('Пароль:', self.guest_register_password)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        # Кнопка регистрации
        btn_register = QPushButton('Зарегистрироваться')
        btn_register.clicked.connect(self.register_guest)

        # Кнопка возврата
        btn_back = QPushButton('Назад')
        btn_back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        buttons.addWidget(btn_back)
        buttons.addWidget(btn_register)

        layout.addLayout(buttons)

        self.stacked_widget.addWidget(widget)

    def clear_fields(self):
        """Очистка всех полей ввода."""
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
        """Обработка входа администратора."""
        username = self.admin_username.text().strip()
        password = self.admin_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return

        try:
            user = self.db.get_user(username, password)
            if not user:
                QMessageBox.warning(self, 'Ошибка', 'Неверные учетные данные')
                return

            if user[3].lower() != 'admin':
                QMessageBox.warning(self, 'Ошибка',
                                    'Недостаточно прав для входа как администратор')
                return

            self.clear_fields()
            self.open_admin_dashboard(user)

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')
            logging.error(f"Ошибка входа администратора: {e}")

    def guest_login(self):
        """Обработка входа гостя."""
        username = self.guest_username.text().strip()
        password = self.guest_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return

        try:
            self.db.cursor.execute(
                """
                SELECT * FROM users WHERE username=? AND password=? AND role='guest'
                AND is_active=1
                """, (username, password)
            )
            user = self.db.cursor.fetchone()

            if not user:
                QMessageBox.warning(
                    self, 'Ошибка',
                    'Неверные учетные данные или недостаточно прав для входа как гость'
                )
                return

            self.clear_fields()
            self.open_guest_dashboard(user)

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')
            logging.error(f"Ошибка входа гостя: {e}")

    def register_guest(self):
        """Обработка регистрации гостя."""
        fullname = self.guest_register_fullname.text().strip()
        email = self.guest_register_email.text().strip()
        phone = self.guest_register_phone.text().strip()
        username = self.guest_register_username.text().strip()
        password = self.guest_register_password.text().strip()

        if not all([fullname, email, username, password]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля')
            return

        if '@' not in email or '.' not in email.split('@')[-1]:
            QMessageBox.warning(self, 'Ошибка', 'Введите корректный email')
            return

        try:
            success = self.db.add_user(username, password, 'guest', fullname, email, phone)
            if success:
                self.db.cursor.execute(
                    "INSERT INTO clients (full_name, email, phone) VALUES (?, ?, ?)",
                    (fullname, email, phone)
                )
                self.db.conn.commit()
                QMessageBox.information(
                    self, 'Успех',
                    'Регистрация прошла успешно. Теперь вы можете войти.'
                )
                self.clear_fields()
                self.stacked_widget.setCurrentIndex(2)
            else:
                QMessageBox.warning(
                    self, 'Ошибка',
                    'Пользователь с таким логином или email уже существует'
                )
        except sqlite3.Error as e:
            QMessageBox.warning(self, 'Ошибка', f'Ошибка при регистрации: {str(e)}')
            logging.error(f"Ошибка регистрации гостя: {e}")

    def logout(self):
        """Выход из системы и очистка полей."""
        self.clear_fields()
        self.stacked_widget.setCurrentIndex(0)

    def open_admin_dashboard(self, user):
        """Открытие панели администратора."""
        self.admin_dashboard = AdminDashboard(user, self.db)
        self.admin_dashboard.show()
        self.close()

    def open_guest_dashboard(self, user):
        """Открытие панели гостя."""
        self.guest_dashboard = GuestDashboard(user, self.db)
        self.guest_dashboard.show()
        self.close()

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        self.db.close()  # Закрытие соединения с базой данных
        event.accept()