from PyQt5.QtWidgets import QDialog, QSpinBox, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QMessageBox


class DiscountDialog(QDialog):
    """Диалог для редактирования скидки клиента."""

    def __init__(self, current_discount):
        """Инициализация диалога редактирования скидки."""
        super().__init__()
        self.setWindowTitle('Редактировать скидку')
        self.setFixedSize(300, 200)  # Установка фиксированного размера окна

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Поле для ввода скидки
        self.discount = QSpinBox()
        self.discount.setRange(0, 50)
        self.discount.setValue(current_discount)
        self.discount.setSuffix('%')
        layout.addWidget(self.discount)

        buttons = QHBoxLayout()

        # Кнопка сохранения
        btn_save = QPushButton('Сохранить')
        btn_save.clicked.connect(self.accept)

        # Кнопка отмены
        btn_cancel = QPushButton('Отмена')
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_discount(self):
        """Получение значения скидки."""
        return self.discount.value()