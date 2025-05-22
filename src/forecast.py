"""
@file forecast.py
@brief Модуль для выполнения прогнозов с использованием скользящей средней.
"""

from math import sqrt


class Forecast:
    """
    @brief Класс для выполнения прогнозов временных рядов.
    """
    @staticmethod
    def forecast_values(data, window_size, periods):
        """
        @brief Вычисление прогнозных значений с использованием скользящей средней.
        @param data Список фактических значений.
        @param window_size Размер окна скользящей средней.
        @param periods Количество периодов для прогноза.
        @return Список прогнозных значений.
        """
        if not data or len(data) < window_size:
            return []

        forecast = []
        for i in range(len(data) - window_size + 1, len(data) + periods):
            if i < len(data):
                window = data[max(0, i - window_size):i]
                avg = sum(window) / len(window)
                forecast.append(avg)
            else:
                window = data[-window_size:]
                avg = sum(window) / len(window)
                forecast.append(avg)

        return forecast

    @staticmethod
    def calculate_errors(actual, predicted):
        """
        @brief Вычисление ошибок прогноза.
        @param actual Список фактических значений.
        @param predicted Список прогнозных значений.
        @return Кортеж (средняя абсолютная ошибка, среднеквадратичная ошибка,
                средняя относительная ошибка в процентах).
        """
        if len(actual) != len(predicted) or not actual:
            return (0.0, 0.0, 0.0)

        n = len(actual)
        abs_error = sum(abs(a - p) for a, p in zip(actual, predicted)) / n
        sq_error = sqrt(sum((a - p) ** 2 for a, p in zip(actual, predicted)) / n)
        rel_error = (
            sum(abs((a - p) / a) * 100 for a, p in zip(actual, predicted) if a != 0) / n
        )

        return (abs_error, sq_error, rel_error)

    @staticmethod
    def interpret_accuracy(mean_rel_error):
        """
        @brief Интерпретация точности прогноза по средней относительной ошибке.
        @param mean_rel_error Средняя относительная ошибка в процентах.
        @return Текстовая интерпретация точности.
        """
        if mean_rel_error < 10:
            return "Высокая точность"
        elif mean_rel_error < 20:
            return "Средняя точность"
        else:
            return "Низкая точность"