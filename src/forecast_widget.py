"""
@file forecast_widget.py
@brief Модуль, реализующий виджет для отображения прогнозов в интерфейсе.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from src.forecast import Forecast
import logging


class ForecastWidget(QWidget):
    """
    @brief Виджет для отображения прогнозов доходов и бронирований.
    """
    def __init__(self, db, parent=None):
        """
        @brief Инициализация виджета прогноза.
        @param db Экземпляр класса Database для работы с базой данных.
        @param parent Родительский виджет (опционально).
        """
        super().__init__(parent)
        self.db = db
        self.forecast = Forecast()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """
        @brief Инициализация пользовательского интерфейса виджета.
        """
        self.layout = QVBoxLayout()

        # График
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Метки для ошибок
        self.error_label = QLabel("Ошибки прогноза: MAE: Н/Д, RMSE: Н/Д, MRE: Н/Д")
        self.accuracy_label = QLabel("Точность прогноза: Н/Д")
        self.layout.addWidget(self.error_label)
        self.layout.addWidget(self.accuracy_label)

        self.setLayout(self.layout)

    def load_data(self):
        """
        @brief Загрузка данных для построения прогноза.
        """
        try:
            self.db.ensure_connection()
            query = """
            SELECT strftime('%Y-%m', check_in_date) as month, SUM(total_price) as revenue
            FROM bookings
            WHERE status IN ('checked_in', 'checked_out')
            GROUP BY month
            ORDER BY month
            """
            df = pd.read_sql_query(query, self.db.conn)
            if df.empty:
                self.error_label.setText("Нет данных для анализа")
                return

            # Исторические данные
            months = df['month'].tolist()
            revenues = df['revenue'].tolist()

            # Логирование данных для отладки
            logging.info(f"Данные для графика: months={months}, revenues={revenues}")

            # Параметры прогноза
            n = 3  # Окно скользящей средней
            periods = 3  # Прогноз на 3 месяца

            # Прогноз
            forecast_revenues = self.forecast.forecast_values(revenues, n, periods)
            forecast_months = [f"{int(months[-1][:4]) + (int(months[-1][5:7]) + i)//12}-{(int(months[-1][5:7]) + i)%12 or 12:02d}" for i in range(1, periods + 1)]

            # Ошибки (для последних исторических данных)
            if len(revenues) >= n + 1:
                test_actual = revenues[-3:]
                test_predicted = self.forecast.forecast_values(revenues[:-3], n, 3)
                mae, rmse, mre = self.forecast.calculate_errors(test_actual, test_predicted)
                accuracy = self.forecast.interpret_accuracy(mre)
                self.error_label.setText(f"Ошибки прогноза: MAE: {mae:.2f}, RMSE: {rmse:.2f}, MRE: {mre:.2f}%")
                self.accuracy_label.setText(f"Точность прогноза: {accuracy}")
            else:
                self.error_label.setText("Недостаточно данных для расчёта ошибок")

            # Построение графика
            self.ax.clear()
            # Сброс стилей Matplotlib и отключение циклической палитры
            plt.style.use('default')
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#0000FF', '#FF0000'])  # Явно задаём цвета: синий для фактических, красный для прогноза
            # Рисуем линию фактических данных (синий цвет)
            line_actual = self.ax.plot(months, revenues, marker='o', color='#0000FF', label='Исторические доходы')
            if forecast_revenues:
                all_months = months + forecast_months
                all_revenues = revenues + forecast_revenues
                # Рисуем линию прогноза (красный цвет, пунктир)
                line_forecast = self.ax.plot(all_months[-periods-1:], all_revenues[-periods-1:], marker='o', linestyle='--', color='#FF0000', label='Прогноз')
            self.ax.set_title('Доход по месяцам и прогноз')
            self.ax.set_xlabel('Месяц')
            self.ax.set_ylabel('Доход (руб.)')
            self.ax.legend()
            plt.xticks(rotation=45)
            self.figure.tight_layout()
            self.canvas.draw()

            # Логирование для проверки применения цвета
            logging.info(f"Цвет линии фактических данных: {line_actual[0].get_color()}")
            if forecast_revenues:
                logging.info(f"Цвет линии прогноза: {line_forecast[0].get_color()}")

            logging.info(f"Загружены данные для прогноза: {len(months)} месяцев")
        except sqlite3.Error as e:
            logging.error(f"Ошибка загрузки данных для прогноза: {e}")
            self.error_label.setText(f"Ошибка: {str(e)}")