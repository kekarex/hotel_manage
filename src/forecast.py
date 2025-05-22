"""
@file forecast.py
@brief Модуль, реализующий класс для расчета прогнозных данных и оценки точности.
"""

from typing import List, Tuple
import math


class Forecast:
    """
    @brief Класс для расчета прогнозных данных и оценки точности.
    """
    @staticmethod
    def moving_average(data: List[float], n: int) -> List[float]:
        """
        @brief Рассчитывает скользящую среднюю для временного ряда.
        @param data Список значений временного ряда.
        @param n Размер окна скользящей средней.
        @return List[float] Список значений скользящей средней.
        """
        if len(data) < n:
            return []
        moving_averages = []
        for i in range(len(data) - n + 1):
            window = data[i:i + n]
            moving_averages.append(sum(window) / n)
        return moving_averages

    @staticmethod
    def forecast_values(data: List[float], n: int, periods: int) -> List[float]:
        """
        @brief Рассчитывает прогнозные значения на заданное число периодов.
        @param data Список исторических данных.
        @param n Размер окна скользящей средней.
        @param periods Количество периодов для прогноза.
        @return List[float] Список прогнозных значений.
        """
        if len(data) < n:
            return []
        forecasts = []
        current_data = data[:]
        for _ in range(periods):
            ma = Forecast.moving_average(current_data, n)
            if len(ma) < 2:
                break
            # y_{t+1} = m_{t-1} + (1/n) * (y_t - y_{t-1})
            y_t = current_data[-1]
            y_t_minus_1 = current_data[-2]
            m_t_minus_1 = ma[-2]
            forecast = m_t_minus_1 + (1 / n) * (y_t - y_t_minus_1)
            forecasts.append(round(forecast, 2))
            current_data.append(forecast)
        return forecasts

    @staticmethod
    def calculate_errors(actual: List[float], predicted: List[float]) -> Tuple[float, float, float]:
        """
        @brief Рассчитывает ошибки прогноза.
        @param actual Список фактических значений.
        @param predicted Список предсказанных значений.
        @return Tuple[float, float, float] Кортеж (средняя абсолютная ошибка, среднеквадратичная ошибка, средняя относительная ошибка).
        """
        if len(actual) != len(predicted) or len(actual) == 0:
            return 0.0, 0.0, 0.0
        k = len(actual)
        absolute_errors = [abs(actual[i] - predicted[i]) for i in range(k)]
        squared_errors = [(actual[i] - predicted[i]) ** 2 for i in range(k)]
        relative_errors = [(absolute_errors[i] / actual[i]) * 100 if actual[i] != 0 else 0 for i in range(k)]

        # Средняя абсолютная ошибка
        mean_absolute_error = sum(absolute_errors) / k
        # Средняя квадратическая ошибка
        mean_squared_error = math.sqrt(sum(squared_errors) / k)
        # Средняя относительная ошибка
        mean_relative_error = sum(relative_errors) / k

        return mean_absolute_error, mean_squared_error, mean_relative_error

    @staticmethod
    def interpret_accuracy(mean_relative_error: float) -> str:
        """
        @brief Интерпретирует точность прогноза.
        @param mean_relative_error Средняя относительная ошибка.
        @return str Текстовая интерпретация точности ('Высокая', 'Хорошая', 'Удовлетворительная', 'Неудовлетворительная').
        """
        if mean_relative_error < 10:
            return "Высокая"
        elif mean_relative_error <= 20:
            return "Хорошая"
        elif mean_relative_error <= 50:
            return "Удовлетворительная"
        else:
            return "Неудовлетворительная"