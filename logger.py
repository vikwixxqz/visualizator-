"""
logger.py — запись протокола работы в файл session_log.txt.

Каждый запуск программы — это «сеанс». В начале сеанса в файл пишется
заголовок с датой и временем запуска, затем после каждой операции —
строка с названием алгоритма, исходными данными, результатом,
оценкой сложности и временем выполнения.

Файл открывается в режиме "a" (append — дозапись), поэтому записи
прошлых сеансов не стираются.
"""

import os
from datetime import datetime

# Формат даты и времени по заданию: ДД.ММ.ГГГГ ЧЧ:ММ:СС
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"


def now_text():
    """Текущие дата и время строкой в нужном формате."""
    return datetime.now().strftime(DATE_FORMAT)


class SessionLogger:
    """Журнал сеанса работы программы."""

    def __init__(self, path):
        self.path = path
        self.session_start = now_text()   # время начала сеанса
        self._write("\n" + "=" * 70 + "\n"
                    f"СЕАНС РАБОТЫ от {self.session_start}\n"
                    + "=" * 70 + "\n")

    def _write(self, text):
        """Дописать текст в конец файла. Ошибку записи (например, нет прав
        на папку) не пробрасываем дальше: программа должна работать
        и без журнала, поэтому просто выводим предупреждение в консоль."""
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            print("Не удалось записать журнал:", e)

    def log_operation(self, structure, algorithm, input_data, result, complexity, ops):
        """Записать результат выполнения алгоритма."""
        self._write(
            f"[{now_text()}] (сеанс {self.session_start})\n"
            f"  Структура:        {structure}\n"
            f"  Алгоритм:         {algorithm}\n"
            f"  Исходные данные:  {input_data}\n"
            f"  Результат:        {result}\n"
            f"  Сложность:        {complexity}\n"
            f"  Элем. операций:   {ops}\n"
            + "-" * 70 + "\n"
        )

    def log_error(self, message):
        """Записать сообщение об ошибке ввода или выполнения."""
        self._write(f"[{now_text()}] ОШИБКА: {message}\n" + "-" * 70 + "\n")

    def read_all(self):
        """Прочитать весь журнал (для окна «Журнал сеанса»)."""
        if not os.path.exists(self.path):
            return "Журнал пока пуст."
        with open(self.path, "r", encoding="utf-8") as f:
            return f.read()
