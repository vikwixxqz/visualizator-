"""
experiment.py — экспериментальная проверка временной сложности.

Идея: теоретическая оценка O(f(n)) говорит, что число операций растёт
примерно как c·f(n), где c — некоторая константа. Значит, если выполнить
операцию для разных n и поделить фактическое число операций на f(n),
отношение должно получаться примерно одинаковым (≈ c).
Если отношение стабильно — оценка подтверждена на практике.

Для каждого n программа:
  1) создаёт структуру из n случайных элементов;
  2) выполняет измеряемую операцию (для поиска — несколько раз
     со случайными ключами и берёт среднее);
  3) берёт счётчик ops, который ведут сами алгоритмы в structures.py.

Структуры здесь те же самые, что и в визуализации, только:
  * record_steps = False — шаги анимации не записываются;
  * MAX_SIZE увеличен — ограничение «чтобы влезло на экран» не нужно.
"""

import math
import random
import sys

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog, QGraphicsScene,
                             QGraphicsSimpleTextItem, QGraphicsView, QHBoxLayout, QHeaderView,
                             QLabel, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
                             QVBoxLayout)

from structures import (ArrayStructure, BSTStructure, GraphStructure, LinkedListStructure,
                        QueueStructure, StackStructure)

# Цвета линий графика (по порядку серий) и оформления
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"
GRID = "#e3e2de"

SEARCH_REPEATS = 100  # сколько раз повторяем поиск, чтобы взять среднее


# ======================================================================
#                 Подготовка структур для измерений
# ======================================================================
def prepare(structure):
    """Отключить запись шагов и снять ограничение на размер.
    MAX_SIZE задаём у самого объекта — он «перекрывает» значение класса."""
    structure.record_steps = False
    structure.MAX_SIZE = 10 ** 7
    return structure


def random_values(n):
    """n различных случайных чисел."""
    return random.sample(range(10 * n + 10), n)


def theory(notation, n, edges=0):
    """Значение функции f(n) из оценки O(f(n)) для конкретного n."""
    if notation == "O(1)":
        return 1
    if notation == "O(n)":
        return n
    if notation == "O(log n)":
        return math.log2(n)
    if notation == "O(V²)":
        return n * n
    if notation == "O(V + E)":
        return n + edges
    raise ValueError(notation)


# ----------------------------------------------------------------------
# Функции измерения. Каждая получает n и возвращает пару
# (число операций, число рёбер — нужно только для графов, иначе 0).
# ----------------------------------------------------------------------
def measure_array_search(n):
    """Средний линейный поиск существующего элемента."""
    a = prepare(ArrayStructure())
    values = random_values(n)
    a.build(values)
    total = 0
    for key in random.sample(values, min(SEARCH_REPEATS, n)):
        a.search(key)
        total += a.ops
    return total / min(SEARCH_REPEATS, n), 0


def measure_bst_search_random(n):
    """Поиск в дереве, построенном из случайной последовательности."""
    t = prepare(BSTStructure())
    values = random_values(n)
    t.build(values)
    total = 0
    for key in random.sample(values, min(SEARCH_REPEATS, n)):
        t.search(key)
        total += t.ops
    return total / min(SEARCH_REPEATS, n), 0


def measure_bst_search_sorted(n):
    """Поиск в дереве из отсортированных ключей — оно вырождается в цепочку."""
    t = prepare(BSTStructure())
    values = list(range(n))
    t.build(values)
    total = 0
    for key in random.sample(values, min(SEARCH_REPEATS, n)):
        t.search(key)
        total += t.ops
    return total / min(SEARCH_REPEATS, n), 0


def measure_array_insert_front(n):
    """Вставка в начало массива: сдвигаются все n элементов."""
    a = prepare(ArrayStructure())
    a.build(random_values(n))
    a.insert(0, -1)
    return a.ops, 0


def measure_list_push_front(n):
    """Вставка в начало списка: меняются только две ссылки."""
    lst = prepare(LinkedListStructure())
    lst.build(random_values(n))
    lst.push_front(-1)
    return lst.ops, 0


def measure_list_push_back(n):
    """Вставка в конец списка: нужно дойти до последнего узла."""
    lst = prepare(LinkedListStructure())
    lst.build(random_values(n))
    lst.push_back(-1)
    return lst.ops, 0


def measure_stack_push(n):
    s = prepare(StackStructure())
    s.build(random_values(n))
    s.push(-1)
    return s.ops, 0


def measure_queue_dequeue(n):
    q = prepare(QueueStructure())
    q.build(random_values(n))
    q.dequeue()
    return q.ops, 0


def random_sparse_graph(n):
    """Случайный разреженный связный граф: цепочка 0–1–2–…–(n-1)
    (чтобы обход дошёл до всех вершин) плюс n случайных рёбер."""
    names = [str(i) for i in range(n)]
    adj = {name: set() for name in names}
    for i in range(n - 1):
        adj[names[i]].add(names[i + 1])
        adj[names[i + 1]].add(names[i])
    for _ in range(n):
        u, v = random.sample(range(n), 2)
        adj[names[u]].add(names[v])
        adj[names[v]].add(names[u])
    return names, {name: list(neighbors) for name, neighbors in adj.items()}


def measure_bfs(n, representation):
    """BFS по одному и тому же графу, заданному матрицей или списком."""
    names, adj = random_sparse_graph(n)
    g = prepare(GraphStructure())
    if representation == "matrix":
        index = {name: i for i, name in enumerate(names)}
        matrix = [[0] * n for _ in range(n)]
        for u in names:
            for v in adj[u]:
                matrix[index[u]][index[v]] = 1
        g.build_from_matrix(names, matrix)
    else:
        g.build_from_list(names, adj)
    g.bfs(names[0])
    return g.ops, g.edge_count()


# ----------------------------------------------------------------------
# Список экспериментов: название, размеры n, серии (название, O, функция)
# ----------------------------------------------------------------------
EXPERIMENTS = [
    ("Поиск: массив O(n) и бинарное дерево O(log n)",
     [100, 200, 400, 600, 800, 1000, 1500, 2000],
     [("Массив: линейный поиск", "O(n)", measure_array_search),
      ("BST: поиск (случайные ключи)", "O(log n)", measure_bst_search_random)]),

    ("BST: сбалансированное и вырожденное дерево",
     [50, 100, 200, 300, 400, 500, 700, 1000],
     [("BST из случайных ключей", "O(log n)", measure_bst_search_random),
      ("BST из отсортированных ключей", "O(n)", measure_bst_search_sorted)]),

    ("Вставка в начало: массив O(n) и односвязный список O(1)",
     [100, 200, 400, 600, 800, 1000, 1500, 2000],
     [("Массив: вставка в начало", "O(n)", measure_array_insert_front),
      ("Список: вставка в начало", "O(1)", measure_list_push_front)]),

    ("Односвязный список: вставка в конец O(n) и в начало O(1)",
     [100, 200, 400, 600, 800, 1000, 1500, 2000],
     [("Список: вставка в конец", "O(n)", measure_list_push_back),
      ("Список: вставка в начало", "O(1)", measure_list_push_front)]),

    ("Стек и очередь: операции O(1)",
     [100, 200, 400, 600, 800, 1000, 1500, 2000],
     [("Стек: Push", "O(1)", measure_stack_push),
      ("Очередь: Dequeue", "O(1)", measure_queue_dequeue)]),

    ("Граф, обход BFS: матрица O(V²) и список смежности O(V + E)",
     [25, 50, 100, 150, 200, 250, 300],
     [("BFS по матрице смежности", "O(V²)", lambda n: measure_bfs(n, "matrix")),
      ("BFS по списку смежности", "O(V + E)", lambda n: measure_bfs(n, "list"))]),
]


def run_experiment(sizes, series):
    """Выполнить все измерения. Возвращает список результатов по сериям:
    [(название, O, [(n, операций, f(n)), ...]), ...]"""
    # у вырожденного дерева рекурсивные функции (подсчёт узлов, высота)
    # уходят на глубину n, поэтому увеличиваем допустимую глубину рекурсии
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
    random.seed(2026)   # фиксированное зерно — повторный запуск даёт те же числа
    results = []
    for name, notation, func in series:
        points = []
        for n in sizes:
            ops, edges = func(n)
            points.append((n, ops, theory(notation, n, edges)))
            QApplication.processEvents()   # чтобы окно не «зависало»
        results.append((name, notation, points))
    return results


# ======================================================================
#                          Рисование графика
# ======================================================================
def nice_max(value):
    """Округлить максимум оси вверх до «красивого» числа (1, 2, 5 · 10^k)."""
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    for k in (1, 2, 5, 10):
        if value <= k * power:
            return k * power
    return 10 * power


def draw_chart(scene, results, title):
    """Линейный график: по оси X — размер n, по оси Y — число операций.
    Одна ось Y для всех серий, чтобы их можно было честно сравнить."""
    scene.clear()
    scene.setBackgroundBrush(QColor(SURFACE))
    width, height = 860, 300            # размеры области построения
    font = QFont("Arial", 10)
    title_font = QFont("Arial", 12, QFont.Bold)

    def text(x, y, value, f=font, color=TEXT_MUTED, align="left"):
        item = QGraphicsSimpleTextItem(str(value))
        item.setFont(f)
        item.setBrush(QBrush(QColor(color)))
        w = item.boundingRect().width()
        h = item.boundingRect().height()
        dx = {"left": 0, "center": -w / 2, "right": -w}[align]
        item.setPos(x + dx, y - h / 2)
        scene.addItem(item)
        return w   # ширина надписи — нужна, чтобы расставить элементы легенды

    max_n = max(p[0] for _, _, points in results for p in points)
    max_ops = nice_max(max(p[1] for _, _, points in results for p in points))

    # пересчёт «данные → координаты на сцене»; ось Y направлена вниз,
    # поэтому y = height - ...
    def to_x(n):
        return n / max_n * width

    def to_y(ops):
        return height - ops / max_ops * height

    text(0, -60, title, title_font, TEXT)

    # сетка и подписи оси Y (5 делений)
    grid_pen = QPen(QColor(GRID), 1)
    for i in range(6):
        value = max_ops * i / 5
        y = to_y(value)
        scene.addLine(0, y, width, y, grid_pen)
        label = f"{value:,.0f}".replace(",", " ") if value >= 10 else f"{value:g}"
        text(-8, y, label, align="right")
    text(-8, -22, "операций", align="right")

    # подписи оси X
    axis_pen = QPen(QColor(TEXT_MUTED), 1)
    scene.addLine(0, height, width, height, axis_pen)
    sizes = [p[0] for p in results[0][2]]
    for n in sizes:
        text(to_x(n), height + 14, n, align="center")
    text(width, height + 34, "размер n", align="right")

    # линии серий
    for index, (name, notation, points) in enumerate(results):
        color = QColor(SERIES_COLORS[index % len(SERIES_COLORS)])
        pen = QPen(color, 2)
        coords = [(to_x(n), to_y(ops)) for n, ops, _ in points]
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            scene.addLine(x1, y1, x2, y2, pen)
        for (x, y), (n, ops, _) in zip(coords, points):
            # маркер точки с белой обводкой; подсказка появляется при наведении
            dot = scene.addEllipse(QRectF(x - 4.5, y - 4.5, 9, 9),
                                   QPen(QColor(SURFACE), 2), QBrush(color))
            dot.setToolTip(f"{name}\nn = {n}: {ops:.1f} операций")
        # подпись в конце линии: название оценки
        last_x, last_y = coords[-1]
        text(last_x + 10, last_y, notation, QFont("Arial", 10, QFont.Bold), TEXT)

    # легенда над графиком
    x = 0
    for index, (name, notation, _) in enumerate(results):
        color = QColor(SERIES_COLORS[index % len(SERIES_COLORS)])
        scene.addRect(QRectF(x, -34, 14, 4), QPen(Qt.NoPen), QBrush(color))
        label_width = text(x + 20, -32, f"{name} — {notation}", color=TEXT)
        x += 20 + label_width + 30


# ======================================================================
#                          Окно эксперимента
# ======================================================================
class ExperimentDialog(QDialog):
    """Окно «Эксперимент: сложность на практике»."""

    def __init__(self, parent, logger):
        super().__init__(parent)
        self.logger = logger
        self.setWindowTitle("Эксперимент: проверка сложности на практике")
        self.resize(1100, 760)

        layout = QVBoxLayout(self)
        explain = QLabel(
            "Программа строит структуры из n случайных элементов, выполняет операцию и берёт "
            "число элементарных операций, которое посчитал сам алгоритм. Если отношение "
            "«факт / f(n)» почти не меняется с ростом n, оценка O(f(n)) подтверждается.")
        explain.setWordWrap(True)
        layout.addWidget(explain)

        row = QHBoxLayout()
        row.addWidget(QLabel("Эксперимент:"))
        self.combo = QComboBox()
        for title, _, _ in EXPERIMENTS:
            self.combo.addItem(title)
        row.addWidget(self.combo, 1)
        run_button = QPushButton("Запустить")
        run_button.clicked.connect(self.run)
        row.addWidget(run_button)
        save_button = QPushButton("Сохранить график…")
        save_button.clicked.connect(self.save_image)
        row.addWidget(save_button)
        layout.addLayout(row)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        # таблица — точные числа к графику
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Операция", "n", "Факт. операций", "f(n) из оценки", "Факт / f(n)"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.view)
        splitter.addWidget(self.table)
        splitter.setSizes([430, 260])
        layout.addWidget(splitter, 1)

        self.conclusion = QLabel("Выберите эксперимент и нажмите «Запустить».")
        self.conclusion.setWordWrap(True)
        self.conclusion.setStyleSheet("padding: 6px; background: #eef3f8; color: #1d2b3a;")
        layout.addWidget(self.conclusion)

    def run(self):
        title, sizes, series = EXPERIMENTS[self.combo.currentIndex()]
        self.conclusion.setText("Идут измерения…")
        QApplication.setOverrideCursor(Qt.WaitCursor)   # курсор «часики»
        try:
            results = run_experiment(sizes, series)
        finally:
            QApplication.restoreOverrideCursor()
        self.show_table(results)
        draw_chart(self.scene, results, title)
        self.fit_chart()
        self.conclusion.setText(self.make_conclusion(results))
        self.write_log(title, results)

    def fit_chart(self):
        """Вписать график в область просмотра целиком."""
        if self.scene.items():
            self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20),
                                Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        """При изменении размера окна график заново вписывается."""
        super().resizeEvent(event)
        self.fit_chart()

    def show_table(self, results):
        rows = [(name, n, ops, f) for name, _, points in results for n, ops, f in points]
        self.table.setRowCount(len(rows))
        for i, (name, n, ops, f) in enumerate(rows):
            values = [name, str(n), f"{ops:.1f}", f"{f:.1f}", f"{ops / f:.3f}"]
            for j, value in enumerate(values):
                item = QTableWidgetItem(value)
                if j > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, j, item)

    @staticmethod
    def ratio_spread(points):
        """Разброс отношения факт / f(n) по второй половине измерений
        (на малых n сильнее влияют константы, поэтому их не берём)."""
        ratios = [ops / f for _, ops, f in points[len(points) // 2:]]
        return min(ratios), max(ratios)

    def make_conclusion(self, results):
        """Текстовый вывод: во сколько раз вырос n и число операций."""
        parts = []
        for name, notation, points in results:
            n0, ops0, _ = points[0]
            n1, ops1, _ = points[-1]
            low, high = self.ratio_spread(points)
            parts.append(f"<b>{name}</b> ({notation}): n выросло в {n1 / n0:.0f} раз, "
                         f"операций — в {ops1 / ops0:.1f} раза; отношение факт / f(n) "
                         f"держится в пределах {low:.2f}…{high:.2f}.")
        return "<br>".join(parts)

    def write_log(self, title, results):
        """Результаты эксперимента — в общий журнал session_log.txt."""
        for name, notation, points in results:
            data = ", ".join(f"n={n}: {ops:.1f}" for n, ops, _ in points)
            low, high = self.ratio_spread(points)
            self.logger.log_operation("Эксперимент", f"{title} / {name}",
                                      "случайные данные, n = " + ", ".join(str(p[0]) for p in points),
                                      data, f"{notation}; факт / f(n) = {low:.2f}…{high:.2f}",
                                      "см. результат")

    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить график", "experiment.png",
                                              "Изображение PNG (*.png)")
        if path:
            self.view.grab().save(path)
