"""
panels.py — панели управления для каждой структуры данных.

Каждая панель — это виджет в левой части окна: поля ввода и кнопки
операций. Панель «владеет» своей структурой данных (объект из
structures.py): по нажатию кнопки она читает и проверяет ввод,
вызывает нужный метод структуры и передаёт результат главному окну
(метод report), которое выводит сложность, пишет журнал и запускает
пошаговую анимацию.

Общая часть всех панелей вынесена в базовый класс BasePanel,
а классы-наследники отличаются только своими полями и кнопками.
"""

import random

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QButtonGroup, QComboBox, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPlainTextEdit, QPushButton, QRadioButton,
                             QSpinBox, QVBoxLayout, QWidget)

from input_parser import (InputError, MAX_VERTICES, detect_graph_format, parse_adjacency_list,
                          parse_int, parse_matrix, parse_numbers, vertex_names)
from structures import (ArrayStructure, BSTStructure, GraphStructure, LinkedListStructure,
                        QueueStructure, StackStructure)


class BasePanel(QWidget):
    """Базовая панель: заголовок, удобные функции создания полей и кнопок,
    общая логика отчёта об операции.

    Наследник должен:
      - задать title (название структуры) и file_hint (формат файла);
      - реализовать draw_state() — какой метод Drawer вызывать;
      - реализовать load_from_text() — что делать с текстом из файла.
    """

    title = "Структура"
    file_hint = ""

    def __init__(self, main_window, structure):
        super().__init__()
        self.main = main_window          # ссылка на главное окно (gui.MainWindow)
        self.structure = structure       # объект структуры данных
        self.source = "клавиатура"       # откуда пришли данные (для журнала)

        self.box = QVBoxLayout(self)
        header = QLabel(self.title)
        header.setFont(QFont("Arial", 14, QFont.Bold))
        self.box.addWidget(header)
        hint = QLabel("Формат файла: " + self.file_hint)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")
        self.box.addWidget(hint)

    # ---------- функции-помощники для построения формы ----------
    def add_group(self, title):
        """Создать рамку с заголовком и вернуть её внутреннюю раскладку."""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        self.box.addWidget(group)
        return layout

    def add_line(self, layout, label, placeholder="", default=""):
        """Строка «подпись + поле ввода». Возвращает поле QLineEdit."""
        row = QHBoxLayout()
        caption = QLabel(label)
        caption.setMinimumWidth(75)
        row.addWidget(caption)
        edit = QLineEdit(default)
        edit.setPlaceholderText(placeholder)
        row.addWidget(edit)
        layout.addLayout(row)
        return edit

    def add_button(self, layout, text, handler):
        """Кнопка. Обработчик вызывается через main.execute(), который
        перехватывает ошибки и показывает их во всплывающем окне."""
        button = QPushButton(text)
        button.clicked.connect(lambda: self.main.execute(handler))
        layout.addWidget(button)
        return button

    # ---------- общая логика ----------
    def report(self, algorithm, key, sizes, input_data, result):
        """Передать результат операции главному окну."""
        self.main.show_operation(self, algorithm, key, sizes,
                                 f"{input_data} (ввод: {self.source})", result,
                                 self.structure.steps, self.structure.ops)

    def redraw(self):
        """Нарисовать текущее состояние без подсветки."""
        self.main.render(self, self.structure.snapshot(), {})

    def reset(self):
        """Очистить структуру."""
        self.structure.clear()
        self.redraw()

    def load_file_text(self, text, file_name):
        """Загрузка данных из файла: проходим через тот же путь, что и
        ручной ввод, только с пометкой источника для журнала."""
        self.source = f"файл {file_name}"
        try:
            self.load_from_text(text)
        finally:
            self.source = "клавиатура"

    # сколько случайных элементов генерировать (наследники могут изменить)
    random_count = 7

    def fill_random(self):
        """Заполнить структуру случайными данными.

        random.sample(range(1, 100), k) выбирает k РАЗНЫХ чисел от 1 до 99 —
        это важно для дерева поиска, где повторы не добавляются.
        Сгенерированные числа подставляются в поле ввода, а дальше
        работает обычное построение — как при ручном вводе.
        """
        values = random.sample(range(1, 100), self.random_count)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.source = "случайная генерация"
        try:
            self.on_build()
        finally:
            self.source = "клавиатура"

    def draw_state(self, state, marks):
        raise NotImplementedError

    def load_from_text(self, text):
        raise NotImplementedError


# ======================================================================
class ArrayPanel(BasePanel):
    title = "Массив"
    file_hint = "целые числа через пробел, запятую или с новой строки."

    def __init__(self, main_window):
        super().__init__(main_window, ArrayStructure())
        g = self.add_group("Создание массива")
        self.seq_edit = self.add_line(g, "Элементы:", "например: 14 7 23 5 18", "14 7 23 5 18")
        self.add_button(g, "Создать массив", self.on_build)

        g = self.add_group("Операции")
        self.value_edit = self.add_line(g, "Значение:", "целое число", "11")
        self.index_edit = self.add_line(g, "Индекс:", "номер ячейки", "2")
        self.add_button(g, "Добавить в конец — O(1)", self.on_append)
        self.add_button(g, "Вставить по индексу — O(n)", self.on_insert)
        self.add_button(g, "Удалить по индексу — O(n)", self.on_remove)
        self.add_button(g, "Найти значение — O(n)", self.on_search)
        self.add_button(g, "Получить по индексу — O(1)", self.on_get)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_array(state, marks)

    def load_from_text(self, text):
        values = parse_numbers(text)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.on_build()

    def on_build(self):
        values = parse_numbers(self.seq_edit.text())
        self.structure.build(values)
        self.report("Создание массива", "array_build", {"n": len(values)},
                    str(values), f"массив {self.structure.data}")

    def on_append(self):
        value = parse_int(self.value_edit.text(), "Значение")
        before = self.structure.snapshot()
        self.structure.append(value)
        self.report("Добавление в конец", "array_append", {"n": len(before)},
                    f"массив {before}, значение {value}", f"массив {self.structure.data}")

    def on_insert(self):
        value = parse_int(self.value_edit.text(), "Значение")
        index = parse_int(self.index_edit.text(), "Индекс")
        before = self.structure.snapshot()
        self.structure.insert(index, value)
        self.report("Вставка по индексу", "array_insert", {"n": len(before)},
                    f"массив {before}, значение {value}, индекс {index}",
                    f"массив {self.structure.data}, выполнено сдвигов: {len(before) - index}")

    def on_remove(self):
        index = parse_int(self.index_edit.text(), "Индекс")
        before = self.structure.snapshot()
        removed = self.structure.remove(index)
        self.report("Удаление по индексу", "array_remove", {"n": len(before)},
                    f"массив {before}, индекс {index}",
                    f"удалён {removed}, массив {self.structure.data}")

    def on_search(self):
        value = parse_int(self.value_edit.text(), "Значение")
        index = self.structure.search(value)
        result = f"найден в ячейке [{index}]" if index >= 0 else "не найден"
        self.report("Линейный поиск", "array_search", {"n": self.structure.size()},
                    f"массив {self.structure.data}, искомое {value}", result)

    def on_get(self):
        index = parse_int(self.index_edit.text(), "Индекс")
        value = self.structure.get(index)
        self.report("Доступ по индексу", "array_get", {"n": self.structure.size()},
                    f"массив {self.structure.data}, индекс {index}", f"[{index}] = {value}")


# ======================================================================
class StackPanel(BasePanel):
    title = "Стек (LIFO)"
    file_hint = "целые числа через пробел, запятую или с новой строки — кладутся в стек по порядку."

    def __init__(self, main_window):
        super().__init__(main_window, StackStructure())
        g = self.add_group("Создание стека")
        self.seq_edit = self.add_line(g, "Элементы:", "например: 12 9 31", "12 9 31")
        self.add_button(g, "Заполнить стек", self.on_build)

        g = self.add_group("Операции")
        self.value_edit = self.add_line(g, "Значение:", "целое число", "5")
        self.add_button(g, "Push — положить на вершину", self.on_push)
        self.add_button(g, "Pop — снять с вершины", self.on_pop)
        self.add_button(g, "Peek — посмотреть вершину", self.on_peek)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_stack(state, marks)

    def load_from_text(self, text):
        values = parse_numbers(text)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.on_build()

    def on_build(self):
        values = parse_numbers(self.seq_edit.text())
        self.structure.build(values)
        self.report("Заполнение стека (серия Push)", "stack_build", {"n": len(values)},
                    str(values), f"стек (дно → вершина) {self.structure.data}")

    def on_push(self):
        value = parse_int(self.value_edit.text(), "Значение")
        self.structure.push(value)
        self.report("Push", "stack_push", {"n": self.structure.size()},
                    f"значение {value}", f"стек {self.structure.data}")

    def on_pop(self):
        value = self.structure.pop()
        self.report("Pop", "stack_pop", {"n": self.structure.size() + 1},
                    "—", f"извлечено {value}, стек {self.structure.data}")

    def on_peek(self):
        value = self.structure.peek()
        self.report("Peek", "stack_peek", {"n": self.structure.size()},
                    "—", f"вершина = {value}")


# ======================================================================
class QueuePanel(BasePanel):
    title = "Очередь (FIFO)"
    file_hint = "целые числа через пробел, запятую или с новой строки — встают в очередь по порядку."

    def __init__(self, main_window):
        super().__init__(main_window, QueueStructure())
        g = self.add_group("Создание очереди")
        self.seq_edit = self.add_line(g, "Элементы:", "например: 4 8 15 16", "4 8 15 16")
        self.add_button(g, "Заполнить очередь", self.on_build)

        g = self.add_group("Операции")
        self.value_edit = self.add_line(g, "Значение:", "целое число", "23")
        self.add_button(g, "Enqueue — добавить в конец", self.on_enqueue)
        self.add_button(g, "Dequeue — извлечь из начала", self.on_dequeue)
        self.add_button(g, "Front — посмотреть первый", self.on_peek)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_queue(state, marks)

    def load_from_text(self, text):
        values = parse_numbers(text)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.on_build()

    def on_build(self):
        values = parse_numbers(self.seq_edit.text())
        self.structure.build(values)
        self.report("Заполнение очереди (серия Enqueue)", "queue_build", {"n": len(values)},
                    str(values), f"очередь (front → rear) {list(self.structure.data)}")

    def on_enqueue(self):
        value = parse_int(self.value_edit.text(), "Значение")
        self.structure.enqueue(value)
        self.report("Enqueue", "queue_enqueue", {"n": self.structure.size()},
                    f"значение {value}", f"очередь {list(self.structure.data)}")

    def on_dequeue(self):
        value = self.structure.dequeue()
        self.report("Dequeue", "queue_dequeue", {"n": self.structure.size() + 1},
                    "—", f"извлечено {value}, очередь {list(self.structure.data)}")

    def on_peek(self):
        value = self.structure.peek()
        self.report("Front (Peek)", "queue_peek", {"n": self.structure.size()},
                    "—", f"первый элемент = {value}")


# ======================================================================
class LinkedListPanel(BasePanel):
    title = "Односвязный список"
    file_hint = "целые числа через пробел, запятую или с новой строки — значения узлов по порядку."

    def __init__(self, main_window):
        super().__init__(main_window, LinkedListStructure())
        g = self.add_group("Создание списка")
        self.seq_edit = self.add_line(g, "Узлы:", "например: 3 5 13 21", "3 5 13 21")
        self.add_button(g, "Создать список", self.on_build)

        g = self.add_group("Операции")
        self.value_edit = self.add_line(g, "Значение:", "целое число", "8")
        self.pos_edit = self.add_line(g, "Позиция:", "номер узла (с 0)", "2")
        self.add_button(g, "Вставить в начало — O(1)", self.on_push_front)
        self.add_button(g, "Вставить в конец — O(n)", self.on_push_back)
        self.add_button(g, "Вставить на позицию — O(n)", self.on_insert)
        self.add_button(g, "Удалить по значению — O(n)", self.on_remove)
        self.add_button(g, "Найти значение — O(n)", self.on_find)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_linked_list(state, marks)

    def load_from_text(self, text):
        values = parse_numbers(text)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.on_build()

    def chain(self):
        """Текстовое представление списка: 3 → 5 → 13 → None."""
        return " → ".join(map(str, self.structure.snapshot() + ["None"]))

    def on_build(self):
        values = parse_numbers(self.seq_edit.text())
        self.structure.build(values)
        self.report("Создание списка", "list_build", {"n": len(values)},
                    str(values), self.chain())

    def on_push_front(self):
        value = parse_int(self.value_edit.text(), "Значение")
        before = self.chain()
        self.structure.push_front(value)
        self.report("Вставка в начало", "list_push_front", {"n": self.structure.size() - 1},
                    f"{before}, значение {value}", self.chain())

    def on_push_back(self):
        value = parse_int(self.value_edit.text(), "Значение")
        before = self.chain()
        self.structure.push_back(value)
        self.report("Вставка в конец", "list_push_back", {"n": self.structure.size() - 1},
                    f"{before}, значение {value}", self.chain())

    def on_insert(self):
        value = parse_int(self.value_edit.text(), "Значение")
        position = parse_int(self.pos_edit.text(), "Позиция")
        before = self.chain()
        self.structure.insert_at(position, value)
        self.report("Вставка на позицию", "list_insert", {"n": self.structure.size() - 1},
                    f"{before}, значение {value}, позиция {position}", self.chain())

    def on_remove(self):
        value = parse_int(self.value_edit.text(), "Значение")
        before = self.chain()
        n = self.structure.size()
        removed = self.structure.remove(value)
        result = self.chain() if removed else f"узел {value} не найден"
        self.report("Удаление по значению", "list_remove", {"n": n},
                    f"{before}, значение {value}", result)

    def on_find(self):
        value = parse_int(self.value_edit.text(), "Значение")
        index = self.structure.find(value)
        result = f"найден на позиции {index}" if index >= 0 else "не найден"
        self.report("Поиск значения", "list_find", {"n": self.structure.size()},
                    f"{self.chain()}, искомое {value}", result)


# ======================================================================
# Пример графа из пояснительной записки (рисунок 1.4, таблица 1.1)
EXAMPLE_MATRIX = """5
0 1 1 0 0
1 0 0 1 0
1 0 0 1 0
0 1 1 0 1
0 0 0 1 0"""


class GraphPanel(BasePanel):
    title = "Граф"
    file_hint = ("первая строка — число вершин n; далее либо n строк матрицы смежности "
                 "из 0 и 1, либо n строк списка смежности вида «A: B, C». "
                 "Формат определяется автоматически.")

    def __init__(self, main_window):
        super().__init__(main_window, GraphStructure())
        g = self.add_group("Способ задания графа")
        self.radio_matrix = QRadioButton("Матрица смежности")
        self.radio_list = QRadioButton("Список смежности")
        self.radio_matrix.setChecked(True)
        # QButtonGroup делает радиокнопки взаимоисключающими
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_matrix)
        self.mode_group.addButton(self.radio_list)
        g.addWidget(self.radio_matrix)
        g.addWidget(self.radio_list)

        row = QHBoxLayout()
        row.addWidget(QLabel("Вершин:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, MAX_VERTICES)
        self.count_spin.setValue(5)
        row.addWidget(self.count_spin)
        template_button = QPushButton("Шаблон")
        template_button.clicked.connect(lambda: self.main.execute(self.on_template))
        row.addWidget(template_button)
        g.addLayout(row)

        self.editor = QPlainTextEdit(EXAMPLE_MATRIX)
        self.editor.setFont(QFont("Courier New", 11))
        self.editor.setMinimumHeight(150)
        g.addWidget(self.editor)
        self.add_button(g, "Построить граф", self.on_build)

        g = self.add_group("Обходы графа")
        row = QHBoxLayout()
        row.addWidget(QLabel("Старт:"))
        self.start_combo = QComboBox()
        row.addWidget(self.start_combo)
        g.addLayout(row)
        self.add_button(g, "Обход в ширину (BFS)", self.on_bfs)
        self.add_button(g, "Обход в глубину (DFS)", self.on_dfs)
        self.add_button(g, "Показать матрицу и список", self.on_show_tables)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_graph(state, marks)

    def reset(self):
        super().reset()
        self.start_combo.clear()

    def load_from_text(self, text):
        # формат определяем по содержимому и переключаем радиокнопку
        if detect_graph_format(text) == "list":
            self.radio_list.setChecked(True)
        else:
            self.radio_matrix.setChecked(True)
        self.editor.setPlainText(text.strip())
        self.on_build()

    def fill_random(self):
        """Случайный неориентированный граф из 5–8 вершин.

        Для каждой пары вершин i < j «подбрасываем монетку» с вероятностью
        0.35 и ставим 1 сразу в ячейки [i][j] и [j][i] — так матрица
        получается симметричной. Чтобы граф был связным, дополнительно
        соединяем каждую вершину со случайной из предыдущих.
        """
        n = random.randint(5, 8)
        matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if random.random() < 0.35:
                    matrix[i][j] = matrix[j][i] = 1
        for i in range(1, n):
            j = random.randrange(i)
            matrix[i][j] = matrix[j][i] = 1
        self.radio_matrix.setChecked(True)
        self.count_spin.setValue(n)
        self.editor.setPlainText(f"{n}\n" + "\n".join(" ".join(map(str, row)) for row in matrix))
        self.source = "случайная генерация"
        try:
            self.on_build()
        finally:
            self.source = "клавиатура"

    def on_template(self):
        """Заготовка для ввода с клавиатуры: нулевая матрица или пустой список."""
        n = self.count_spin.value()
        names = vertex_names(n)
        if self.radio_matrix.isChecked():
            rows = [" ".join(["0"] * n) for _ in range(n)]
        else:
            rows = [f"{name}: " for name in names]
        self.editor.setPlainText(f"{n}\n" + "\n".join(rows))

    def on_build(self):
        text = self.editor.toPlainText()
        wanted = "matrix" if self.radio_matrix.isChecked() else "list"
        # защита от путаницы: выбран один формат, а введён другой
        if detect_graph_format(text) != wanted:
            other = "список смежности" if wanted == "matrix" else "матрица смежности"
            raise InputError(f"Похоже, что введён {other}. Переключите способ задания графа.")
        if wanted == "matrix":
            names, matrix = parse_matrix(text)
            self.structure.build_from_matrix(names, matrix)
            algorithm, key = "Построение графа по матрице смежности", "graph_build_matrix"
        else:
            names, adj = parse_adjacency_list(text)
            self.structure.build_from_list(names, adj)
            algorithm, key = "Построение графа по списку смежности", "graph_build_list"
        self.start_combo.clear()
        self.start_combo.addItems(self.structure.vertices)
        g = self.structure
        kind = "ориентированный" if g.directed else "неориентированный"
        self.report(algorithm, key, {"V": g.size(), "E": g.edge_count()},
                    " | ".join(text.strip().splitlines()),
                    f"{kind} граф, |V| = {g.size()}, |E| = {g.edge_count()}")
        self.on_show_tables()

    def _check_built(self):
        if self.structure.size() == 0:
            raise InputError("Сначала постройте граф.")

    def _traverse(self, kind):
        self._check_built()
        start = self.start_combo.currentText()
        g = self.structure
        if kind == "bfs":
            order = g.bfs(start)
            name = "Обход в ширину (BFS)"
        else:
            order = g.dfs(start)
            name = "Обход в глубину (DFS)"
        how = "матрица" if g.representation == "matrix" else "список"
        self.report(f"{name}, представление: {how} смежности",
                    f"graph_{kind}_{g.representation}", {"V": g.size(), "E": g.edge_count()},
                    f"граф |V| = {g.size()}, |E| = {g.edge_count()}, старт {start}",
                    "порядок обхода: " + ", ".join(order))

    def on_bfs(self):
        self._traverse("bfs")

    def on_dfs(self):
        self._traverse("dfs")

    def on_show_tables(self):
        self._check_built()
        self.main.add_history("Матрица смежности:\n" + self.structure.matrix_text())
        self.main.add_history("Список смежности:\n" + self.structure.list_text())


# ======================================================================
class BSTPanel(BasePanel):
    title = "Бинарное дерево поиска"
    file_hint = "последовательность целых чисел через пробел, запятую или с новой строки — ключи вставляются по порядку."
    random_count = 10

    def __init__(self, main_window):
        super().__init__(main_window, BSTStructure())
        g = self.add_group("Построение дерева")
        self.seq_edit = self.add_line(g, "Ключи:", "например: 41 18 63 9",
                                      "41 18 63 9 27 52 77 22")
        self.add_button(g, "Построить дерево (пошагово)", self.on_build)

        g = self.add_group("Операции")
        self.key_edit = self.add_line(g, "Ключ:", "целое число", "30")
        self.add_button(g, "Вставить ключ — O(h)", self.on_insert)
        self.add_button(g, "Найти ключ — O(h)", self.on_search)
        self.add_button(g, "Удалить ключ — O(h)", self.on_delete)

        g = self.add_group("Обходы дерева")
        self.add_button(g, "Прямой (pre-order) — O(n)",
                        lambda: self.on_traverse("pre", "Прямой обход (pre-order)", "bst_preorder"))
        self.add_button(g, "Симметричный (in-order) — O(n)",
                        lambda: self.on_traverse("in", "Симметричный обход (in-order)", "bst_inorder"))
        self.add_button(g, "Обратный (post-order) — O(n)",
                        lambda: self.on_traverse("post", "Обратный обход (post-order)", "bst_postorder"))

        g = self.add_group("Характеристики")
        self.add_button(g, "Минимальный ключ — O(h)", self.on_min)
        self.add_button(g, "Максимальный ключ — O(h)", self.on_max)
        self.add_button(g, "Высота дерева — O(n)", self.on_height)
        self.add_button(g, "Количество листьев — O(n)", self.on_leaves)
        self.box.addStretch()

    def draw_state(self, state, marks):
        self.main.drawer.draw_tree(state, marks)

    def load_from_text(self, text):
        values = parse_numbers(text)
        self.seq_edit.setText(" ".join(map(str, values)))
        self.on_build()

    def sizes(self):
        """Текущие размеры дерева для оценки сложности."""
        return {"n": self.structure.size(), "h": max(self.structure.height(), 0)}

    def on_build(self):
        keys = parse_numbers(self.seq_edit.text())
        self.structure.build(keys)
        self.report("Построение BST по последовательности", "bst_build", self.sizes(),
                    str(keys), f"узлов {self.structure.size()}, высота {self.structure.height()}")

    def on_insert(self):
        key = parse_int(self.key_edit.text(), "Ключ")
        inserted = self.structure.insert(key)
        result = "ключ добавлен" if inserted else "ключ уже был в дереве"
        self.report("Вставка в BST", "bst_insert", self.sizes(), f"ключ {key}",
                    f"{result}, высота {self.structure.height()}")

    def on_search(self):
        key = parse_int(self.key_edit.text(), "Ключ")
        found = self.structure.search(key)
        self.report("Поиск в BST", "bst_search", self.sizes(), f"ключ {key}",
                    "найден" if found else "не найден")

    def on_delete(self):
        key = parse_int(self.key_edit.text(), "Ключ")
        sizes = self.sizes()
        deleted = self.structure.delete(key)
        self.report("Удаление из BST", "bst_delete", sizes, f"ключ {key}",
                    "удалён" if deleted else "не найден")

    def on_traverse(self, order, algorithm, key):
        """Один обработчик для трёх обходов в глубину."""
        result = self.structure.traverse(order)
        self.report(algorithm, key, self.sizes(), "—", ", ".join(map(str, result)))

    def on_min(self):
        value = self.structure.find_min()
        self.report("Поиск минимума", "bst_min", self.sizes(), "—", f"минимум = {value}")

    def on_max(self):
        value = self.structure.find_max()
        self.report("Поиск максимума", "bst_max", self.sizes(), "—", f"максимум = {value}")

    def on_height(self):
        h = self.structure.compute_height()
        self.report("Вычисление высоты", "bst_height", self.sizes(), "—", f"высота h = {h}")

    def on_leaves(self):
        leaves = self.structure.count_leaves()
        self.report("Подсчёт листьев", "bst_leaves", self.sizes(), "—",
                    f"листьев {len(leaves)}: {', '.join(map(str, leaves))}")
