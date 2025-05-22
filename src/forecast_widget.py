"""
@file forecast_widget.py
@brief Модуль для создания виджета прогноза в интерфейсе пользователя.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QMessageBox

from forecast import Forecast


class ForecastWidget(QWidget):
    """
    @brief Виджет для отображения и управления прогнозами.
    """
    def __init__(self, db):
        """
        @brief Инициализация виджета прогноза.
        @param db Экземпляр класса Database для работы с базой данных.
        """
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        """
        @brief Инициализация пользовательского интерфейса виджета.
        """
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Прогноз бронирований и доходов")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        params_layout = QHBoxLayout()

        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["Бронирования", "Доход"])
        params_layout.addWidget(QLabel("Тип данных:"))
        params_layout.addWidget(self.analysis_type)

        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        params_layout.addWidget(QLabel("Начальная дата:"))
        params_layout.addWidget(self.start_date)

        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        params_layout.addWidget(QLabel("Конечная дата:"))
        params_layout.addWidget(self.end_date)

        self.forecast_periods = QComboBox()
        self.forecast_periods.addItems(["1 месяц", "3 месяца", "6 месяцев", "12 месяцев"])
        self.forecast_periods.setCurrentText("3 месяца")
        params_layout.addWidget(QLabel("Период прогноза:"))
        params_layout.addWidget(self.forecast_periods)

        btn_generate = QPushButton("Сформировать прогноз")
        btn_generate.clicked.connect(self.generate_forecast)
        params_layout.addWidget(btn_generate)

        layout.addLayout(params_layout)

        self.forecast_table = QTableWidget()
        self.forecast_table.setColumnCount(6)
        self.forecast_table.setHorizontalHeaderLabels(
            [
                "Месяц",
                "Фактическое",
                "Прогноз",
                "Абс. ошибка",
                "Квадр. ошибка",
                "Отн. ошибка (%)",
            ]
        )
        self.forecast_table.setSortingEnabled(True)
        layout.addWidget(self.forecast_table)

        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def generate_forecast(self):
        """
        @brief Генерация прогноза с использованием скользящей средней.
        """
        data_type = "bookings" if self.analysis_type.currentText() == "Бронирования" else "revenue"
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        period_text = self.forecast_periods.currentText()
        periods = {
            "1 месяц": 1,
            "3 месяца": 3,
            "6 месяцев": 6,
            "12 месяцев": 12,
        }[period_text]

        try:
            time_series = self.db.get_time_series(data_type, start_date, end_date)
            if not time_series or len(time_series) < 3:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Недостаточно данных для прогноза (нужно минимум 3 месяца)",
                )
                return

            months, values = zip(*time_series)
            values = list(values)

            n = 3
            forecast_values = Forecast.forecast_values(values, n, periods)
            if not forecast_values:
                QMessageBox.warning(self, "Ошибка", "Невозможно рассчитать прогноз")
                return

            self.forecast_table.setRowCount(len(values) + periods)
            actual_values = values + [None] * periods
            predicted_values = values[: len(values)] + forecast_values
            errors = Forecast.calculate_errors(
                values[-min(len(forecast_values), len(values)):],
                forecast_values[: min(len(forecast_values), len(values))],
            )

            for i, month in enumerate(months):
                self.forecast_table.setItem(i, 0, QTableWidgetItem(month))
                self.forecast_table.setItem(
                    i,
                    1,
                    QTableWidgetItem(str(actual_values[i]) if actual_values[i] else ""),
                )
                self.forecast_table.setItem(
                    i, 2, QTableWidgetItem(str(predicted_values[i]))
                )

            last_month = months[-1]
            for i in range(periods):
                self.forecast_table.setItem(
                    len(months) + i, 0, QTableWidgetItem(last_month)
                )
                self.forecast_table.setItem(
                    len(months) + i, 2, QTableWidgetItem(str(forecast_values[i]))
                )

            mean_abs_error, mean_sq_error, mean_rel_error = errors
            self.forecast_table.setItem(
                0, 3, QTableWidgetItem(f"{mean_abs_error:.2f}")
            )
            self.forecast_table.setItem(
                0, 4, QTableWidgetItem(f"{mean_sq_error:.2f}")
            )
            self.forecast_table.setItem(
                0,
                5,
                QTableWidgetItem(
                    f"{mean_rel_error:.2f} "
                    f"({Forecast.interpret_accuracy(mean_rel_error)})"
                ),
            )

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(months, values, label="Фактические", marker="o")
            ax.plot(
                months + [last_month] * periods,
                predicted_values,
                label="Прогноз",
                marker="x",
                linestyle="--",
            )
            ax.set_xlabel("Месяц")
            ax.set_ylabel(
                "Количество бронирований" if data_type == "bookings" else "Доход (руб.)"
            )
            ax.legend()
            ax.grid(True)
            plt.setp(ax.get_xticklabels(), rotation=45)
            self.canvas.draw()

            for i in range(periods):
                self.db.save_forecast(
                    last_month,
                    data_type,
                    None,
                    forecast_values[i],
                    mean_rel_error if i == 0 else None,
                )

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось сформировать прогноз: {str(e)}"
            )