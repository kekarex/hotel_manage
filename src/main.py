import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.database import Database
from src.auth_window import AuthWindow


def main():
    """
    @brief Инициализация и запуск приложения.
    """
    logging.basicConfig(
        filename='hotel_app.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Запуск приложения")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('assets/hotel_icon.png'))  # Установка иконки приложения
    app.setStyle('Fusion')  # Установка стиля интерфейса

    # Применение пользовательских стилей для единообразного UI
    app.setStyleSheet(""" 
        QMainWindow {
            background-color: #f5f5f5;
        }
        QLabel {
            font: 12px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            font-size: 12px;
            margin: 4px 2px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f2f2f2;
        }
        QHeaderView::section {
            background-color: #4CAF50;
            color: white;
            padding: 4px;
        }
        QGroupBox {
            border: 1px solid gray;
            border-radius: 3px;
            margin-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        QTabWidget::pane {
            border-top: 2px solid #C2C7CB;
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                       stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
            border: 2px solid #C4C4C3;
            border-bottom-color: #C2C7CB;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 8ex;
            padding: 2px;
        }
        QTabBar::tab:selected, QTabBar::tab:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                       stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);
        }
        QTabBar::tab:selected {
            border-color: #9B9B9B;
            border-bottom-color: #C2C7CB;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
    """)

    db = Database()  # Создание экземпляра Database
    logging.info(f"Создан экземпляр Database: {id(db)}")

    auth_window = AuthWindow(db)  # Передача db в AuthWindow
    auth_window.show()  # Отображение окна
    exit_code = app.exec_()  # Запуск главного цикла приложения
    db.close()  # Закрытие соединения
    logging.info("Приложение завершено")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()