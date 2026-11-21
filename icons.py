"""
icons.py — иконки для меню, панели инструментов и списка структур.

Иконки не загружаются из файлов, а рисуются программно с помощью QPainter
на прозрачной картинке QPixmap. Так программе не нужны дополнительные
файлы, а все значки получаются в одном стиле и в тех же цветах,
что и рисунки структур (см. drawer.py).

Каждая иконка рисуется в «логических» координатах 32×32, а сама картинка
имеет размер 64×64 — painter.scale(2, 2) увеличивает рисунок в два раза,
поэтому значки остаются чёткими и на экранах с высоким разрешением.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

LINE = QColor("#2c3e50")      # контур
FILL = QColor("#dbe9f6")      # обычная заливка (как у ячеек структур)
ACCENT = QColor("#ffd54f")    # жёлтый акцент
GREEN = QColor("#81c784")
RED = QColor("#e57373")
WHITE = QColor("white")


def _start():
    """Создать прозрачную картинку и «кисть» для рисования на ней."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)   # сглаживание
    painter.scale(2, 2)                             # рисуем в координатах 32×32
    painter.setPen(QPen(LINE, 2))
    return pixmap, painter


def _finish(pixmap, painter):
    """Закончить рисование и превратить картинку в иконку."""
    painter.end()
    return QIcon(pixmap)


def _triangle(painter, points, color):
    """Закрашенный многоугольник по списку точек (x, y)."""
    painter.setBrush(QBrush(color))
    painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))


def _arrow(painter, x1, y, x2):
    """Горизонтальная стрелка слева направо (x1 → x2)."""
    painter.drawLine(QPointF(x1, y), QPointF(x2 - 4, y))
    _triangle(painter, [(x2, y), (x2 - 5, y - 3.5), (x2 - 5, y + 3.5)], LINE)


# ======================================================================
#                   Иконки панели инструментов
# ======================================================================
def open_icon():
    """Папка — «Загрузить из файла»."""
    pixmap, p = _start()
    p.setBrush(QBrush(ACCENT))
    p.drawPolygon(QPolygonF([QPointF(3, 8), QPointF(12, 8), QPointF(15, 11), QPointF(29, 11),
                             QPointF(29, 26), QPointF(3, 26)]))
    return _finish(pixmap, p)


def random_icon():
    """Игральный кубик — «Случайные данные»."""
    pixmap, p = _start()
    p.setBrush(QBrush(WHITE))
    p.drawRoundedRect(QRectF(4, 4, 24, 24), 5, 5)
    p.setBrush(QBrush(LINE))
    for x, y in [(10, 10), (16, 16), (22, 22), (22, 10), (10, 22)]:
        p.drawEllipse(QPointF(x, y), 2, 2)
    return _finish(pixmap, p)


def save_icon():
    """Картинка с горами и солнцем — «Сохранить изображение»."""
    pixmap, p = _start()
    p.setBrush(QBrush(FILL))
    p.drawRect(QRectF(3, 5, 26, 22))
    p.setBrush(QBrush(ACCENT))
    p.drawEllipse(QPointF(22, 11), 2.5, 2.5)
    _triangle(p, [(5, 25), (13, 14), (20, 25)], GREEN)
    _triangle(p, [(15, 25), (21, 18), (27, 25)], GREEN)
    return _finish(pixmap, p)


def log_icon():
    """Лист с текстом — «Журнал сеанса»."""
    pixmap, p = _start()
    p.setBrush(QBrush(WHITE))
    p.drawRect(QRectF(7, 3, 18, 26))
    for y in (9, 14, 19, 24):
        p.drawLine(QPointF(11, y), QPointF(21, y))
    return _finish(pixmap, p)


def pause_icon():
    """Две вертикальные полосы — «Пауза»."""
    pixmap, p = _start()
    p.setBrush(QBrush(LINE))
    p.drawRect(QRectF(9, 7, 4, 18))
    p.drawRect(QRectF(19, 7, 4, 18))
    return _finish(pixmap, p)


def play_icon():
    """Треугольник — «Продолжить» (показывается, когда стоит пауза)."""
    pixmap, p = _start()
    _triangle(p, [(10, 6), (25, 16), (10, 26)], GREEN)
    return _finish(pixmap, p)


def step_icon():
    """Треугольник с чертой — «Следующий шаг»."""
    pixmap, p = _start()
    _triangle(p, [(8, 7), (20, 16), (8, 25)], LINE)
    p.setBrush(QBrush(LINE))
    p.drawRect(QRectF(22, 7, 3, 18))
    return _finish(pixmap, p)


def finish_icon():
    """Два треугольника с чертой — «Показать результат» (перемотка в конец)."""
    pixmap, p = _start()
    _triangle(p, [(3, 8), (13, 16), (3, 24)], LINE)
    _triangle(p, [(13, 8), (23, 16), (13, 24)], LINE)
    p.setBrush(QBrush(LINE))
    p.drawRect(QRectF(25, 8, 3, 16))
    return _finish(pixmap, p)


def reset_icon():
    """Корзина — «Очистить структуру»."""
    pixmap, p = _start()
    p.drawLine(QPointF(6, 8), QPointF(26, 8))
    p.drawLine(QPointF(13, 8), QPointF(13, 5))
    p.drawLine(QPointF(13, 5), QPointF(19, 5))
    p.drawLine(QPointF(19, 5), QPointF(19, 8))
    p.setBrush(QBrush(RED))
    p.drawPolygon(QPolygonF([QPointF(8, 10), QPointF(24, 10), QPointF(22, 28), QPointF(10, 28)]))
    for x in (13, 16, 19):
        p.drawLine(QPointF(x, 14), QPointF(x, 24))
    return _finish(pixmap, p)


def help_icon():
    """Круг со знаком вопроса — пункты справки."""
    pixmap, p = _start()
    p.setBrush(QBrush(FILL))
    p.drawEllipse(QPointF(16, 16), 13, 13)
    font = p.font()
    font.setBold(True)
    font.setPixelSize(18)
    p.setFont(font)
    p.drawText(QRectF(3, 3, 26, 26), Qt.AlignCenter, "?")
    return _finish(pixmap, p)


def table_icon():
    """Таблица — «Таблица сложности»."""
    pixmap, p = _start()
    p.setBrush(QBrush(WHITE))
    p.drawRect(QRectF(4, 5, 24, 22))
    p.setBrush(QBrush(FILL))
    p.drawRect(QRectF(4, 5, 24, 6))
    p.drawLine(QPointF(4, 18), QPointF(28, 18))
    p.drawLine(QPointF(13, 5), QPointF(13, 27))
    return _finish(pixmap, p)


def exit_icon():
    """Дверь со стрелкой — «Выход»."""
    pixmap, p = _start()
    p.setBrush(QBrush(FILL))
    p.drawRect(QRectF(4, 4, 14, 24))
    _arrow(p, 12, 16, 29)
    return _finish(pixmap, p)


# ======================================================================
#                 Иконки структур данных (список слева)
# ======================================================================
def array_icon():
    """Ряд ячеек, одна выделена."""
    pixmap, p = _start()
    for i in range(3):
        p.setBrush(QBrush(ACCENT if i == 1 else FILL))
        p.drawRect(QRectF(2 + i * 9.3, 10, 9.3, 12))
    return _finish(pixmap, p)


def stack_icon():
    """Ящики друг на друге в «стакане»."""
    pixmap, p = _start()
    p.drawLine(QPointF(6, 4), QPointF(6, 29))
    p.drawLine(QPointF(26, 4), QPointF(26, 29))
    p.drawLine(QPointF(6, 29), QPointF(26, 29))
    for i in range(3):
        p.setBrush(QBrush(GREEN if i == 2 else FILL))
        p.drawRect(QRectF(9, 21 - i * 7, 14, 6))
    return _finish(pixmap, p)


def queue_icon():
    """Лента ячеек и стрелка движения."""
    pixmap, p = _start()
    for i in range(3):
        p.setBrush(QBrush(FILL))
        p.drawRect(QRectF(4 + i * 8, 7, 8, 10))
    _arrow(p, 4, 24, 28)
    return _finish(pixmap, p)


def linked_list_icon():
    """Два узла, соединённые стрелкой-ссылкой."""
    pixmap, p = _start()
    p.setBrush(QBrush(FILL))
    p.drawRect(QRectF(2, 10, 10, 12))
    p.drawRect(QRectF(20, 10, 10, 12))
    _arrow(p, 12, 16, 20)
    return _finish(pixmap, p)


def graph_icon():
    """Четыре вершины и рёбра между ними."""
    pixmap, p = _start()
    points = [(7, 8), (25, 7), (8, 25), (24, 24)]
    for a, b in [(0, 1), (0, 2), (1, 3), (2, 3), (0, 3)]:
        p.drawLine(QPointF(*points[a]), QPointF(*points[b]))
    p.setBrush(QBrush(FILL))
    for x, y in points:
        p.drawEllipse(QPointF(x, y), 4.5, 4.5)
    return _finish(pixmap, p)


def tree_icon():
    """Корень и два потомка."""
    pixmap, p = _start()
    p.drawLine(QPointF(16, 8), QPointF(7, 24))
    p.drawLine(QPointF(16, 8), QPointF(25, 24))
    p.setBrush(QBrush(ACCENT))
    p.drawEllipse(QPointF(16, 8), 5, 5)
    p.setBrush(QBrush(FILL))
    p.drawEllipse(QPointF(7, 24), 5, 5)
    p.drawEllipse(QPointF(25, 24), 5, 5)
    return _finish(pixmap, p)


# иконки структур в том же порядке, что и панели в gui.py
STRUCTURE_ICONS = [array_icon, stack_icon, queue_icon, linked_list_icon, graph_icon, tree_icon]
