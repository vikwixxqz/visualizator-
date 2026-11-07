"""
drawer.py — отрисовка структур данных на сцене QGraphicsScene.

QGraphicsScene — это «холст», на который можно добавлять графические
примитивы: прямоугольники, эллипсы, линии, текст. QGraphicsView
(создаётся в gui.py) показывает эту сцену в окне.

Класс Drawer ничего не знает об алгоритмах: он получает готовое
состояние (список значений, граф, корень дерева) и словарь подсветки
marks, и просто рисует картинку. Перед каждым шагом сцена очищается
и рисуется заново — это проще, чем двигать отдельные фигуры.
"""

import math

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QFont, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from structures import CURRENT, NEW, DELETE, FOUND, VISITED

# Цвета подсветки: смысловой ключ -> цвет заливки
COLORS = {
    None: "#dbe9f6",       # обычный элемент — светло-голубой
    CURRENT: "#ffd54f",    # текущий — жёлтый
    NEW: "#81c784",        # добавленный — зелёный
    DELETE: "#e57373",     # удаляемый — красный
    FOUND: "#4dd0e1",      # найденный — бирюзовый
    VISITED: "#b39ddb",    # посещённый — сиреневый
}
EMPTY_COLOR = "#f4f4f4"    # пустая ячейка массива
LINE_COLOR = "#2c3e50"     # цвет линий и текста
HINT_COLOR = "#7f8c8d"     # цвет подписей (индексы, head, top...)

CELL_W = 60   # ширина ячейки
CELL_H = 50   # высота ячейки


class Drawer:
    """Рисует структуры данных на переданной сцене."""

    def __init__(self, scene):
        self.scene = scene
        self.pen = QPen(QColor(LINE_COLOR), 2)
        self.value_font = QFont("Arial", 13, QFont.Bold)
        self.hint_font = QFont("Arial", 10)
        self.title_font = QFont("Arial", 12, QFont.Bold)

    # ------------------------------------------------------------------
    # Базовые примитивы
    # ------------------------------------------------------------------
    def clear(self):
        self.scene.clear()

    def text(self, x, y, text, font=None, color=LINE_COLOR, center=True):
        """Нарисовать текст. Если center=True — (x, y) это центр надписи."""
        item = QGraphicsSimpleTextItem(str(text))
        item.setFont(font or self.value_font)
        item.setBrush(QBrush(QColor(color)))
        rect = item.boundingRect()
        if center:
            item.setPos(x - rect.width() / 2, y - rect.height() / 2)
        else:
            item.setPos(x, y)
        self.scene.addItem(item)
        return item

    def cell(self, x, y, value, mark=None, w=CELL_W, h=CELL_H):
        """Прямоугольная ячейка со значением внутри."""
        color = EMPTY_COLOR if value is None else COLORS.get(mark, COLORS[None])
        self.scene.addRect(QRectF(x, y, w, h), self.pen, QBrush(QColor(color)))
        if value is not None:
            self.text(x + w / 2, y + h / 2, value)

    def circle(self, cx, cy, r, label, mark=None):
        """Круг (вершина графа или узел дерева) с подписью."""
        color = COLORS.get(mark, COLORS[None])
        self.scene.addEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r), self.pen, QBrush(QColor(color)))
        self.text(cx, cy, label)

    def arrow(self, x1, y1, x2, y2, color=LINE_COLOR, width=2, head=True):
        """Линия со стрелкой на конце (x2, y2).

        Наконечник — треугольник. Угол линии считаем через atan2,
        затем откладываем две точки под углом ±25° назад от конца.
        """
        pen = QPen(QColor(color), width)
        self.scene.addLine(x1, y1, x2, y2, pen)
        if not head:
            return
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 11
        p1 = QPointF(x2 - size * math.cos(angle - math.radians(25)),
                     y2 - size * math.sin(angle - math.radians(25)))
        p2 = QPointF(x2 - size * math.cos(angle + math.radians(25)),
                     y2 - size * math.sin(angle + math.radians(25)))
        self.scene.addPolygon(QPolygonF([QPointF(x2, y2), p1, p2]), pen, QBrush(QColor(color)))

    def empty_message(self, text):
        """Надпись для пустой структуры."""
        self.text(0, 0, text, self.title_font, HINT_COLOR)

    # ------------------------------------------------------------------
    # Линейные структуры
    # ------------------------------------------------------------------
    def draw_array(self, values, marks):
        """Массив: ряд ячеек, под каждой — индекс."""
        self.clear()
        self.text(0, -40, f"Массив, n = {sum(v is not None for v in values)}",
                  self.title_font, center=False)
        if not values:
            self.empty_message("Массив пуст")
            return
        for i, value in enumerate(values):
            x = i * CELL_W
            self.cell(x, 0, value, marks.get(i))
            self.text(x + CELL_W / 2, CELL_H + 15, f"[{i}]", self.hint_font, HINT_COLOR)

    def draw_stack(self, values, marks):
        """Стек: вертикальный столбец, вершина сверху."""
        self.clear()
        self.text(0, -40, f"Стек (LIFO), размер = {len(values)}", self.title_font, center=False)
        n = len(values)
        # «стакан»: левая, правая и нижняя стенки
        height = max(n, 1) * CELL_H + 10
        wall = QPen(QColor(LINE_COLOR), 3)
        self.scene.addLine(-5, 0, -5, height, wall)
        self.scene.addLine(CELL_W + 5, 0, CELL_W + 5, height, wall)
        self.scene.addLine(-5, height, CELL_W + 5, height, wall)
        if n == 0:
            self.text(CELL_W / 2, height / 2, "пусто", self.hint_font, HINT_COLOR)
            return
        for i, value in enumerate(values):
            # элемент 0 (дно) рисуем внизу, последний (вершина) — вверху
            y = height - 5 - (i + 1) * CELL_H
            self.cell(0, y, value, marks.get(i))
            self.text(CELL_W + 35, y + CELL_H / 2, f"[{i}]", self.hint_font, HINT_COLOR)
        top_y = height - 5 - n * CELL_H + CELL_H / 2
        self.text(-80, top_y - 8, "top", self.hint_font, HINT_COLOR, center=False)
        self.arrow(-50, top_y, -10, top_y)

    def draw_queue(self, values, marks):
        """Очередь: горизонтальная лента, слева голова (front), справа хвост (rear)."""
        self.clear()
        self.text(0, -60, f"Очередь (FIFO), размер = {len(values)}", self.title_font, center=False)
        n = len(values)
        if n == 0:
            self.empty_message("Очередь пуста")
            return
        for i, value in enumerate(values):
            self.cell(i * CELL_W, 0, value, marks.get(i))
        # подписи front и rear со стрелками сверху
        if n == 1:
            self.text(CELL_W / 2, -32, "front = rear", self.hint_font, HINT_COLOR)
        else:
            self.text(CELL_W / 2, -32, "front", self.hint_font, HINT_COLOR)
            rear_x = (n - 1) * CELL_W + CELL_W / 2
            self.text(rear_x, -32, "rear", self.hint_font, HINT_COLOR)
            self.arrow(rear_x, -22, rear_x, -3)
        self.arrow(CELL_W / 2, -22, CELL_W / 2, -3)
        # направления движения элементов
        self.arrow(-10, CELL_H / 2, -60, CELL_H / 2, HINT_COLOR)
        self.text(-60, CELL_H + 15, "выход", self.hint_font, HINT_COLOR)
        right = n * CELL_W
        self.arrow(right + 60, CELL_H / 2, right + 10, CELL_H / 2, HINT_COLOR)
        self.text(right + 60, CELL_H + 15, "вход", self.hint_font, HINT_COLOR)

    # ------------------------------------------------------------------
    # Односвязный список
    # ------------------------------------------------------------------
    def draw_linked_list(self, values, marks):
        """Узел рисуется как прямоугольник из двух частей: [значение | next].
        Из части next выходит стрелка к следующему узлу."""
        self.clear()
        self.text(0, -70, f"Односвязный список, узлов = {len(values)}", self.title_font, center=False)
        value_w = 55     # ширина части со значением
        ptr_w = 25       # ширина части со ссылкой
        gap = 45         # расстояние между узлами (под стрелку)
        step = value_w + ptr_w + gap
        # указатель head
        self.text(value_w / 2, -38, "head", self.hint_font, HINT_COLOR)
        if not values:
            self.arrow(value_w / 2, -25, value_w / 2, 5)
            self.text(value_w / 2, 20, "None", self.hint_font, HINT_COLOR)
            return
        self.arrow(value_w / 2, -25, value_w / 2, -2)
        for i, value in enumerate(values):
            x = i * step
            self.cell(x, 0, value, marks.get(i), w=value_w)
            self.cell(x + value_w, 0, "", marks.get(i), w=ptr_w)
            # точка в ячейке next — «из неё выходит ссылка»
            px = x + value_w + ptr_w / 2
            self.scene.addEllipse(QRectF(px - 4, CELL_H / 2 - 4, 8, 8), self.pen,
                                  QBrush(QColor(LINE_COLOR)))
            if i < len(values) - 1:
                self.arrow(px, CELL_H / 2, x + step - 2, CELL_H / 2)
            else:
                # последний узел ссылается на None
                self.arrow(px, CELL_H / 2, x + step - 5, CELL_H / 2)
                self.text(x + step + 18, CELL_H / 2, "None", self.hint_font, HINT_COLOR)
            self.text(x + (value_w + ptr_w) / 2, CELL_H + 15, f"узел {i}", self.hint_font, HINT_COLOR)

    # ------------------------------------------------------------------
    # Граф
    # ------------------------------------------------------------------
    def draw_graph(self, graph, marks):
        """Вершины располагаются равномерно по окружности:
        вершина i имеет угол 2π·i/n. Рёбра — линии между центрами
        (у ориентированного графа — со стрелками)."""
        self.clear()
        n = graph.size()
        if n == 0:
            self.empty_message("Граф не построен")
            return
        kind = "Ориентированный" if graph.directed else "Неориентированный"
        r = 24                                   # радиус вершины
        radius = max(110, 32 * n)                # радиус окружности расположения
        self.text(-radius, -radius - 70, f"{kind} граф: |V| = {n}, |E| = {graph.edge_count()}",
                  self.title_font, center=False)
        pos = {}
        for i, name in enumerate(graph.vertices):
            angle = 2 * math.pi * i / n - math.pi / 2   # первая вершина — сверху
            pos[name] = (radius * math.cos(angle), radius * math.sin(angle))

        for u, v in graph.edges():
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            # подсвечено ли ребро (при обходе дерево обхода выделяется)
            used = (u, v) in marks or (not graph.directed and (v, u) in marks)
            color = "#7e57c2" if used else LINE_COLOR
            width = 4 if used else 2
            # укорачиваем линию на радиус, чтобы она начиналась и
            # заканчивалась на границе кругов, а не в центре
            length = math.hypot(x2 - x1, y2 - y1)
            dx, dy = (x2 - x1) / length, (y2 - y1) / length
            self.arrow(x1 + dx * r, y1 + dy * r, x2 - dx * r, y2 - dy * r,
                       color, width, head=graph.directed)

        for name in graph.vertices:
            x, y = pos[name]
            self.circle(x, y, r, name, marks.get(name))

    # ------------------------------------------------------------------
    # Бинарное дерево поиска
    # ------------------------------------------------------------------
    def draw_tree(self, root, marks):
        """Раскладка дерева:
          x — номер узла при симметричном обходе (левое–узел–правое),
              поэтому узлы не перекрываются и меньшие ключи всегда левее;
          y — глубина узла.
        """
        self.clear()
        if root is None:
            self.empty_message("Дерево пустое")
            return
        positions = {}           # id(узла) -> (x, y)
        counter = [0]            # список, чтобы менять значение внутри рекурсии
        dx, dy = 50, 75

        def layout(node, depth):
            if node is None:
                return
            layout(node.left, depth + 1)
            positions[id(node)] = (counter[0] * dx, depth * dy)
            counter[0] += 1
            layout(node.right, depth + 1)

        layout(root, 0)
        height = max(y for _, y in positions.values()) // dy
        self.text(0, -60, f"Бинарное дерево поиска: n = {counter[0]}, высота h = {height}",
                  self.title_font, center=False)

        r = 21

        def draw_edges(node):
            """Сначала рисуем все рёбра, чтобы узлы потом легли поверх них."""
            for child in (node.left, node.right):
                if child is not None:
                    x1, y1 = positions[id(node)]
                    x2, y2 = positions[id(child)]
                    self.scene.addLine(x1, y1, x2, y2, self.pen)
                    draw_edges(child)

        def draw_nodes(node):
            if node is None:
                return
            x, y = positions[id(node)]
            self.circle(x, y, r, node.key, marks.get(node.key))
            draw_nodes(node.left)
            draw_nodes(node.right)

        draw_edges(root)
        draw_nodes(root)
