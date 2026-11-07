"""
structures.py — реализация структур данных.

В этом модуле нет ничего, связанного с графическим интерфейсом: только
сами структуры и алгоритмы их обработки. Это сделано специально, чтобы
логику можно было проверить отдельно от окна программы.

Главная идея визуализации: каждая операция (вставка, удаление, поиск...)
во время работы «фотографирует» состояние структуры на каждом важном шаге.
Такой снимок хранится в объекте Step. После выполнения операции интерфейс
просто проигрывает список шагов по таймеру, как слайд-шоу.

Кроме того, каждая операция считает число выполненных элементарных
действий (сравнений, сдвигов, переназначений ссылок) в поле self.ops.
Это число выводится рядом с теоретической оценкой сложности.
"""

import copy
from collections import deque


# ----------------------------------------------------------------------
# Цвета подсветки (ключи). Сами цвета задаются в drawer.py,
# здесь только «смысловые» имена, чтобы не зависеть от интерфейса.
# ----------------------------------------------------------------------
CURRENT = "current"    # элемент, с которым алгоритм работает прямо сейчас
NEW = "new"            # только что добавленный элемент
DELETE = "delete"      # элемент, который удаляется
FOUND = "found"        # найденный элемент
VISITED = "visited"    # уже посещённая вершина / узел


class StructureError(Exception):
    """Ошибка выполнения операции: пустая структура, неверный индекс,
    переполнение и т.п. Интерфейс перехватывает её и показывает
    пользователю всплывающее сообщение, а не «падает»."""
    pass


class Step:
    """Один шаг визуализации.

    text  — текстовое пояснение шага (выводится под рисунком);
    state — снимок (копия) состояния структуры в этот момент;
    marks — словарь подсветки: {позиция или ключ: цвет}.
    """

    def __init__(self, text, state, marks=None):
        self.text = text
        self.state = state
        self.marks = marks if marks is not None else {}


class BaseStructure:
    """Общий предок всех структур.

    Хранит список шагов последней операции и счётчик элементарных операций.
    Наследники обязаны переопределить метод snapshot() — он возвращает
    копию текущего состояния для рисования.
    """

    def __init__(self):
        self.steps = []   # шаги последней выполненной операции
        self.ops = 0      # число элементарных операций в последней операции
        # Записывать ли шаги анимации. В режиме «Эксперимент» (experiment.py)
        # структуры содержат тысячи элементов: снимки на каждом шаге заняли бы
        # слишком много памяти и времени, поэтому там запись отключается
        # и считается только число операций ops.
        self.record_steps = True

    def start_operation(self):
        """Вызывается в начале каждой операции: очищает шаги и счётчик."""
        self.steps = []
        self.ops = 0

    def snapshot(self):
        """Вернуть копию состояния. Переопределяется в наследниках."""
        raise NotImplementedError

    def add_step(self, text, marks=None):
        """Сохранить шаг: текст + снимок состояния + подсветка."""
        if not self.record_steps:
            return
        self.steps.append(Step(text, self.snapshot(), marks))


# ======================================================================
#                              МАССИВ
# ======================================================================
class ArrayStructure(BaseStructure):
    """Массив — элементы лежат подряд, доступ по индексу за O(1).

    Внутри используется обычный список Python, но вставку и удаление
    мы делаем «вручную» циклом со сдвигом элементов, как в классическом
    массиве. Встроенный list.insert() тоже сдвигает элементы, просто
    делает это незаметно, а нам нужно показать каждый сдвиг.
    """

    MAX_SIZE = 20   # ограничение, чтобы рисунок помещался на экране

    def __init__(self):
        super().__init__()
        self.data = []

    def snapshot(self):
        # list(...) создаёт новую копию списка, чтобы дальнейшие
        # изменения self.data не испортили уже сохранённый шаг
        return list(self.data)

    def size(self):
        return len(self.data)

    def clear(self):
        self.data = []

    def build(self, values):
        """Создание массива из последовательности — O(n)."""
        if len(values) > self.MAX_SIZE:
            raise StructureError(f"Массив может содержать не более {self.MAX_SIZE} элементов.")
        self.start_operation()
        self.data = []
        self.add_step("Создан пустой массив")
        for v in values:
            self.data.append(v)
            self.ops += 1
            self.add_step(f"Записываем {v} в ячейку [{len(self.data) - 1}]",
                          {len(self.data) - 1: NEW})
        self.add_step(f"Массив создан, размер n = {len(self.data)}")

    def append(self, value):
        """Добавление в конец — O(1): сдвигать ничего не нужно."""
        if len(self.data) >= self.MAX_SIZE:
            raise StructureError("Массив заполнен (достигнут максимальный размер).")
        self.start_operation()
        self.data.append(value)
        self.ops = 1
        self.add_step(f"Значение {value} записано в первую свободную ячейку [{len(self.data) - 1}]",
                      {len(self.data) - 1: NEW})

    def insert(self, index, value):
        """Вставка на позицию index — O(n).

        Алгоритм: добавляем в конец пустую ячейку, затем идём справа
        налево и сдвигаем каждый элемент на одну позицию вправо,
        пока не освободится ячейка index. В неё записываем значение.
        Число сдвигов = n - index.
        """
        n = len(self.data)
        if index < 0 or index > n:
            raise StructureError(f"Индекс вставки должен быть от 0 до {n}.")
        if n >= self.MAX_SIZE:
            raise StructureError("Массив заполнен (достигнут максимальный размер).")
        self.start_operation()
        self.data.append(None)   # новая пустая ячейка в конце
        self.add_step(f"Увеличиваем размер массива: добавлена пустая ячейка [{n}]", {n: CURRENT})
        # сдвиг вправо: от последней ячейки к позиции index
        for i in range(n, index, -1):
            self.data[i] = self.data[i - 1]
            self.data[i - 1] = None
            self.ops += 1
            self.add_step(f"Сдвиг: элемент {self.data[i]} переходит из [{i - 1}] в [{i}]",
                          {i: CURRENT})
        self.data[index] = value
        self.ops += 1
        self.add_step(f"Записываем {value} в освободившуюся ячейку [{index}]", {index: NEW})

    def remove(self, index):
        """Удаление по индексу — O(n): элементы правее сдвигаются влево."""
        n = len(self.data)
        if n == 0:
            raise StructureError("Массив пуст — удалять нечего.")
        if index < 0 or index >= n:
            raise StructureError(f"Индекс удаления должен быть от 0 до {n - 1}.")
        self.start_operation()
        removed = self.data[index]
        self.add_step(f"Удаляем элемент {removed} из ячейки [{index}]", {index: DELETE})
        self.data[index] = None
        # сдвиг влево: каждый следующий элемент занимает место предыдущего
        for i in range(index, n - 1):
            self.data[i] = self.data[i + 1]
            self.data[i + 1] = None
            self.ops += 1
            self.add_step(f"Сдвиг: элемент {self.data[i]} переходит из [{i + 1}] в [{i}]",
                          {i: CURRENT})
        self.data.pop()   # убираем последнюю (теперь пустую) ячейку
        self.ops += 1
        self.add_step(f"Размер массива уменьшен до {len(self.data)}")
        return removed

    def search(self, value):
        """Линейный поиск — O(n): просматриваем элементы по очереди."""
        self.start_operation()
        for i, item in enumerate(self.data):
            self.ops += 1   # одно сравнение
            if item == value:
                self.add_step(f"[{i}] = {item} — значение найдено!", {i: FOUND})
                return i
            self.add_step(f"Сравниваем [{i}] = {item} с {value} — не совпадает", {i: CURRENT})
        self.add_step(f"Просмотрены все {len(self.data)} элементов, значение {value} не найдено")
        return -1

    def get(self, index):
        """Доступ по индексу — O(1): адрес ячейки вычисляется сразу."""
        if index < 0 or index >= len(self.data):
            raise StructureError(f"Индекс должен быть от 0 до {len(self.data) - 1}.")
        self.start_operation()
        self.ops = 1
        self.add_step(f"Сразу обращаемся к ячейке [{index}] = {self.data[index]}", {index: FOUND})
        return self.data[index]


# ======================================================================
#                               СТЕК
# ======================================================================
class StackStructure(BaseStructure):
    """Стек (LIFO — последним пришёл, первым вышел).

    Вершина стека — конец списка self.data. Добавление и удаление
    с конца списка Python выполняются за O(1).
    """

    MAX_SIZE = 15

    def __init__(self):
        super().__init__()
        self.data = []

    def snapshot(self):
        return list(self.data)

    def size(self):
        return len(self.data)

    def clear(self):
        self.data = []

    def is_empty(self):
        return len(self.data) == 0

    def build(self, values):
        """Последовательный Push всех значений — O(n)."""
        if len(values) > self.MAX_SIZE:
            raise StructureError(f"Стек может содержать не более {self.MAX_SIZE} элементов.")
        self.start_operation()
        self.data = []
        self.add_step("Создан пустой стек")
        for v in values:
            self.data.append(v)
            self.ops += 1
            self.add_step(f"Push({v}): элемент кладётся на вершину", {len(self.data) - 1: NEW})

    def push(self, value):
        """Push — положить на вершину, O(1)."""
        if len(self.data) >= self.MAX_SIZE:
            raise StructureError("Переполнение стека (достигнут максимальный размер).")
        self.start_operation()
        self.data.append(value)
        self.ops = 1
        self.add_step(f"Push({value}): элемент {value} стал новой вершиной", {len(self.data) - 1: NEW})

    def pop(self):
        """Pop — снять элемент с вершины, O(1)."""
        if self.is_empty():
            raise StructureError("Стек пуст — операция Pop невозможна.")
        self.start_operation()
        top = len(self.data) - 1
        self.add_step(f"Pop(): снимаем вершину {self.data[top]}", {top: DELETE})
        value = self.data.pop()
        self.ops = 1
        if self.data:
            self.add_step(f"Удалён {value}. Новая вершина: {self.data[-1]}", {len(self.data) - 1: CURRENT})
        else:
            self.add_step(f"Удалён {value}. Стек пуст")
        return value

    def peek(self):
        """Peek — посмотреть вершину без удаления, O(1)."""
        if self.is_empty():
            raise StructureError("Стек пуст — смотреть нечего.")
        self.start_operation()
        self.ops = 1
        self.add_step(f"Peek(): на вершине лежит {self.data[-1]}", {len(self.data) - 1: FOUND})
        return self.data[-1]


# ======================================================================
#                              ОЧЕРЕДЬ
# ======================================================================
class QueueStructure(BaseStructure):
    """Очередь (FIFO — первым пришёл, первым вышел).

    Используется collections.deque, а не обычный список: у списка
    удаление из начала pop(0) выполняется за O(n) (все элементы
    сдвигаются), а у deque метод popleft() работает за O(1).
    """

    MAX_SIZE = 15

    def __init__(self):
        super().__init__()
        self.data = deque()

    def snapshot(self):
        return list(self.data)

    def size(self):
        return len(self.data)

    def clear(self):
        self.data = deque()

    def is_empty(self):
        return len(self.data) == 0

    def build(self, values):
        """Последовательный Enqueue всех значений — O(n)."""
        if len(values) > self.MAX_SIZE:
            raise StructureError(f"Очередь может содержать не более {self.MAX_SIZE} элементов.")
        self.start_operation()
        self.data = deque()
        self.add_step("Создана пустая очередь")
        for v in values:
            self.data.append(v)
            self.ops += 1
            self.add_step(f"Enqueue({v}): элемент встаёт в конец очереди", {len(self.data) - 1: NEW})

    def enqueue(self, value):
        """Enqueue — добавить в конец (хвост), O(1)."""
        if len(self.data) >= self.MAX_SIZE:
            raise StructureError("Очередь переполнена (достигнут максимальный размер).")
        self.start_operation()
        self.data.append(value)
        self.ops = 1
        self.add_step(f"Enqueue({value}): элемент добавлен в хвост очереди", {len(self.data) - 1: NEW})

    def dequeue(self):
        """Dequeue — извлечь из начала (головы), O(1)."""
        if self.is_empty():
            raise StructureError("Очередь пуста — операция Dequeue невозможна.")
        self.start_operation()
        self.add_step(f"Dequeue(): извлекаем первый элемент {self.data[0]}", {0: DELETE})
        value = self.data.popleft()
        self.ops = 1
        if self.data:
            self.add_step(f"Извлечён {value}. Теперь первым стоит {self.data[0]}", {0: CURRENT})
        else:
            self.add_step(f"Извлечён {value}. Очередь пуста")
        return value

    def peek(self):
        """Peek (Front) — посмотреть первый элемент, O(1)."""
        if self.is_empty():
            raise StructureError("Очередь пуста — смотреть нечего.")
        self.start_operation()
        self.ops = 1
        self.add_step(f"Front(): первым в очереди стоит {self.data[0]}", {0: FOUND})
        return self.data[0]


# ======================================================================
#                        ОДНОСВЯЗНЫЙ СПИСОК
# ======================================================================
class ListNode:
    """Узел односвязного списка: значение + ссылка на следующий узел."""

    def __init__(self, value):
        self.value = value
        self.next = None   # None означает «следующего узла нет»


class LinkedListStructure(BaseStructure):
    """Односвязный список.

    Храним только ссылку на первый узел (head). Чтобы добраться до
    k-го узла, нужно пройти по ссылкам k раз — поэтому поиск O(n).
    Зато сама вставка/удаление — это переназначение пары ссылок, O(1).
    """

    MAX_SIZE = 12

    def __init__(self):
        super().__init__()
        self.head = None

    def snapshot(self):
        """Для рисования достаточно списка значений по порядку узлов."""
        values = []
        node = self.head
        while node is not None:
            values.append(node.value)
            node = node.next
        return values

    def size(self):
        return len(self.snapshot())

    def clear(self):
        self.head = None

    def build(self, values):
        """Создание списка: каждый новый узел цепляем к последнему — O(n).
        Ссылку на последний узел (tail) держим в локальной переменной,
        поэтому каждый раз проходить список с начала не нужно."""
        if len(values) > self.MAX_SIZE:
            raise StructureError(f"Список может содержать не более {self.MAX_SIZE} узлов.")
        self.start_operation()
        self.head = None
        tail = None
        self.add_step("Создан пустой список: head = None")
        for i, v in enumerate(values):
            node = ListNode(v)
            if self.head is None:
                self.head = node
                self.add_step(f"Узел {v} стал первым: head → {v}", {0: NEW})
            else:
                tail.next = node
                self.add_step(f"Ссылка next узла {tail.value} теперь указывает на новый узел {v}", {i: NEW})
            tail = node
            self.ops += 1

    def _check_size(self):
        if self.size() >= self.MAX_SIZE:
            raise StructureError(f"Список может содержать не более {self.MAX_SIZE} узлов.")

    def push_front(self, value):
        """Вставка в начало — O(1): всего две операции со ссылками."""
        self._check_size()
        self.start_operation()
        node = ListNode(value)
        node.next = self.head      # 1) новый узел указывает на бывший первый
        self.head = node           # 2) head указывает на новый узел
        self.ops = 2
        self.add_step(f"new.next = head; head = new — узел {value} стал первым", {0: NEW})

    def push_back(self, value):
        """Вставка в конец — O(n): сначала нужно дойти до последнего узла."""
        self._check_size()
        self.start_operation()
        node = ListNode(value)
        if self.head is None:
            self.head = node
            self.ops = 1
            self.add_step(f"Список был пуст: head → {value}", {0: NEW})
            return
        current = self.head
        index = 0
        self.add_step(f"Начинаем с head: узел {current.value}", {0: CURRENT})
        while current.next is not None:   # идём до узла, у которого next = None
            current = current.next
            index += 1
            self.ops += 1
            self.add_step(f"Переход по ссылке next → узел {current.value}", {index: CURRENT})
        current.next = node
        self.ops += 1
        self.add_step(f"Последний узел {current.value} теперь ссылается на новый узел {value}",
                      {index + 1: NEW})

    def insert_at(self, position, value):
        """Вставка на позицию position (0 — в начало) — O(n).

        Доходим до узла с номером position-1 (предыдущий), затем:
            new.next  = prev.next
            prev.next = new
        """
        n = self.size()
        if position < 0 or position > n:
            raise StructureError(f"Позиция вставки должна быть от 0 до {n}.")
        if position == 0:
            self.push_front(value)
            return
        self._check_size()
        self.start_operation()
        prev = self.head
        self.add_step(f"Ищем узел перед позицией {position}. Начинаем с head: {prev.value}", {0: CURRENT})
        for i in range(1, position):
            prev = prev.next
            self.ops += 1
            self.add_step(f"Переход по ссылке next → узел {prev.value}", {i: CURRENT})
        node = ListNode(value)
        node.next = prev.next          # новый узел указывает туда же, куда prev
        prev.next = node               # prev указывает на новый узел
        self.ops += 2
        after = node.next.value if node.next else "None"
        self.add_step(f"new.next = {after}; {prev.value}.next = new — узел {value} вставлен, "
                      f"остальные узлы не сдвигались", {position - 1: CURRENT, position: NEW})

    def remove(self, value):
        """Удаление первого узла с заданным значением — O(n).

        Ищем узел, запоминая предыдущий (prev). Затем «перешагиваем»
        удаляемый узел: prev.next = current.next.
        """
        if self.head is None:
            raise StructureError("Список пуст — удалять нечего.")
        self.start_operation()
        prev = None
        current = self.head
        index = 0
        while current is not None:
            self.ops += 1
            if current.value == value:
                self.add_step(f"Узел {value} найден — удаляем его", {index: DELETE})
                if prev is None:
                    self.head = current.next          # удаляем первый узел
                    self.add_step("head = head.next — первым стал следующий узел")
                else:
                    prev.next = current.next          # обходим удаляемый узел
                    self.add_step(f"{prev.value}.next = {value}.next — узел исключён из цепочки",
                                  {index - 1: CURRENT})
                self.ops += 1
                return True
            self.add_step(f"Узел {current.value} ≠ {value}, идём дальше", {index: CURRENT})
            prev = current
            current = current.next
            index += 1
        self.add_step(f"Достигнут конец списка (None), узел {value} не найден")
        return False

    def find(self, value):
        """Поиск значения — O(n), проход от head по ссылкам."""
        self.start_operation()
        current = self.head
        index = 0
        while current is not None:
            self.ops += 1
            if current.value == value:
                self.add_step(f"Узел {value} найден на позиции {index}", {index: FOUND})
                return index
            self.add_step(f"Узел {current.value} ≠ {value}, переходим по next", {index: CURRENT})
            current = current.next
            index += 1
        self.add_step(f"Достигнут конец списка, значение {value} не найдено")
        return -1


# ======================================================================
#                                ГРАФ
# ======================================================================
class GraphStructure(BaseStructure):
    """Граф G = (V, E).

    Храним сразу оба представления:
      self.matrix — матрица смежности (список списков из 0 и 1);
      self.adj    — список смежности (словарь: вершина → список соседей).
    В поле self.representation запоминаем, каким способом граф задал
    пользователь — от этого зависит оценка сложности обходов:
      по матрице  — O(V²) (для каждой вершины просматривается вся строка),
      по списку   — O(V + E) (просматриваются только реальные соседи).
    """

    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self.vertices = []        # имена вершин, например ["A", "B", "C"]
        self.matrix = []
        self.adj = {}
        self.directed = False
        self.representation = ""  # "matrix" или "list"

    def snapshot(self):
        # Сам граф во время обхода не меняется, поэтому копировать его
        # не нужно — меняется только подсветка (marks).
        return self

    def size(self):
        return len(self.vertices)

    def edge_count(self):
        """Число рёбер (для неориентированного каждое ребро считаем один раз)."""
        total = sum(len(neighbors) for neighbors in self.adj.values())
        return total if self.directed else total // 2

    def edges(self):
        """Список рёбер в виде пар (u, v) для рисования."""
        result = []
        for u in self.vertices:
            for v in self.adj[u]:
                # у неориентированного графа ребро u–v встречается дважды,
                # оставляем одну пару
                if self.directed or self.vertices.index(u) < self.vertices.index(v):
                    result.append((u, v))
        return result

    def build_from_matrix(self, names, matrix):
        """Построение графа по матрице смежности — O(V²):
        нужно просмотреть все V·V ячеек."""
        self.start_operation()
        self.vertices = list(names)
        self.matrix = [list(row) for row in matrix]
        self.adj = {name: [] for name in names}
        n = len(names)
        for i in range(n):
            for j in range(n):
                self.ops += 1
                if matrix[i][j] == 1:
                    self.adj[names[i]].append(names[j])
        self.directed = not self._is_symmetric()
        self.representation = "matrix"
        self.add_step(self._build_message())

    def build_from_list(self, names, adj):
        """Построение по списку смежности — O(V + E)."""
        self.start_operation()
        self.vertices = list(names)
        index = {name: i for i, name in enumerate(names)}
        # соседей упорядочиваем по номеру вершины, чтобы обходы
        # шли «в алфавитном порядке», как в примерах пояснительной записки
        self.adj = {}
        for name in names:
            self.adj[name] = sorted(adj[name], key=lambda v: index[v])
            self.ops += 1 + len(adj[name])
        n = len(names)
        self.matrix = [[0] * n for _ in range(n)]
        for u in names:
            for v in self.adj[u]:
                self.matrix[index[u]][index[v]] = 1
        self.directed = not self._is_symmetric()
        self.representation = "list"
        self.add_step(self._build_message())

    def _is_symmetric(self):
        """Если матрица симметрична (a[i][j] == a[j][i]), граф неориентированный."""
        n = len(self.matrix)
        for i in range(n):
            for j in range(n):
                if self.matrix[i][j] != self.matrix[j][i]:
                    return False
        return True

    def _build_message(self):
        kind = "ориентированный" if self.directed else "неориентированный"
        return f"Построен {kind} граф: |V| = {self.size()}, |E| = {self.edge_count()}"

    def neighbors(self, vertex):
        """Соседи вершины. Если граф задан матрицей — честно просматриваем
        всю строку матрицы (V операций), если списком — только список."""
        if self.representation == "matrix":
            i = self.vertices.index(vertex)
            result = []
            for j in range(len(self.vertices)):
                self.ops += 1
                if self.matrix[i][j] == 1:
                    result.append(self.vertices[j])
            return result
        self.ops += len(self.adj[vertex]) + 1
        return self.adj[vertex]

    def bfs(self, start):
        """Поиск в ширину. Используется очередь: сначала посещаем всех
        соседей стартовой вершины, потом соседей соседей и т.д."""
        self.start_operation()
        visited = [start]
        queue = deque([start])
        marks = {start: CURRENT}
        self.add_step(f"Старт из {start}. Очередь: [{start}]", dict(marks))
        while queue:
            u = queue.popleft()
            marks[u] = CURRENT
            self.add_step(f"Извлекаем {u} из очереди, просматриваем соседей", dict(marks))
            for v in self.neighbors(u):
                if v not in visited:
                    visited.append(v)
                    queue.append(v)
                    marks[v] = NEW
                    marks[(u, v)] = VISITED    # подсвечиваем ребро обхода
                    self.add_step(f"Сосед {v} не посещён → в очередь. Очередь: [{', '.join(queue)}]",
                                  dict(marks))
            marks[u] = VISITED
        self.add_step("Обход BFS завершён. Порядок: " + ", ".join(visited), dict(marks))
        return visited

    def dfs(self, start):
        """Поиск в глубину (рекурсивный): идём от вершины как можно
        глубже, а когда идти некуда — возвращаемся назад."""
        self.start_operation()
        visited = []
        marks = {}
        self._dfs_visit(start, None, visited, marks)
        self.add_step("Обход DFS завершён. Порядок: " + ", ".join(visited), dict(marks))
        return visited

    def _dfs_visit(self, u, parent, visited, marks):
        """Рекурсивная часть DFS."""
        visited.append(u)
        marks[u] = CURRENT
        if parent is not None:
            marks[(parent, u)] = VISITED
        self.add_step(f"Заходим в вершину {u}. Посещены: {', '.join(visited)}", dict(marks))
        for v in self.neighbors(u):
            if v not in visited:
                marks[u] = VISITED
                self._dfs_visit(v, u, visited, marks)
                marks[u] = CURRENT
                self.add_step(f"Возврат в вершину {u}", dict(marks))
        marks[u] = VISITED

    def matrix_text(self):
        """Матрица смежности в виде текста (для панели истории)."""
        header = "   " + " ".join(f"{v:>2}" for v in self.vertices)
        lines = [header]
        for name, row in zip(self.vertices, self.matrix):
            lines.append(f"{name:>2} " + " ".join(f"{x:>2}" for x in row))
        return "\n".join(lines)

    def list_text(self):
        """Список смежности в виде текста."""
        return "\n".join(f"{v}: {', '.join(self.adj[v]) or '—'}" for v in self.vertices)


# ======================================================================
#                      БИНАРНОЕ ДЕРЕВО ПОИСКА
# ======================================================================
class TreeNode:
    """Узел BST: ключ и ссылки на левого и правого потомков."""

    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


class BSTStructure(BaseStructure):
    """Бинарное дерево поиска.

    Свойство BST: все ключи левого поддерева меньше ключа узла,
    все ключи правого — больше. Поэтому при поиске/вставке на каждом
    узле мы выбираем только одно направление и спускаемся по одной
    ветви. Сложность — O(h), где h — высота дерева:
      O(log n) у сбалансированного дерева, O(n) у вырожденного.
    """

    MAX_SIZE = 31

    def __init__(self):
        super().__init__()
        self.root = None

    def snapshot(self):
        # deepcopy копирует всё дерево целиком (все узлы),
        # иначе все шаги указывали бы на одно и то же, уже изменённое, дерево
        return copy.deepcopy(self.root)

    def clear(self):
        self.root = None

    def size(self):
        return self._count(self.root)

    def _count(self, node):
        if node is None:
            return 0
        return 1 + self._count(node.left) + self._count(node.right)

    def height(self):
        """Высота: число рёбер на самом длинном пути от корня до листа.
        Пустое дерево имеет высоту -1, дерево из одного узла — 0."""
        return self._height(self.root)

    def _height(self, node):
        if node is None:
            return -1
        return 1 + max(self._height(node.left), self._height(node.right))

    def build(self, keys):
        """Пошаговое построение дерева по последовательности ключей."""
        if len(set(keys)) > self.MAX_SIZE:
            raise StructureError(f"Дерево может содержать не более {self.MAX_SIZE} узлов.")
        self.start_operation()
        self.root = None
        self.add_step("Создано пустое дерево")
        for key in keys:
            self._insert(key)

    def insert(self, key):
        """Вставка одного ключа."""
        if self.size() >= self.MAX_SIZE:
            raise StructureError(f"Дерево может содержать не более {self.MAX_SIZE} узлов.")
        self.start_operation()
        return self._insert(key)

    def _insert(self, key):
        """Итеративная вставка: спускаемся от корня, сравнивая ключи."""
        if self.root is None:
            self.root = TreeNode(key)
            self.ops += 1
            self.add_step(f"Дерево пустое — {key} становится корнем", {key: NEW})
            return True
        node = self.root
        path = {}                      # подсветка пройденного пути
        while True:
            self.ops += 1              # одно сравнение
            path[node.key] = CURRENT
            if key == node.key:
                self.add_step(f"Ключ {key} уже есть в дереве — дубликаты не добавляются",
                              {node.key: FOUND})
                return False
            if key < node.key:
                self.add_step(f"{key} < {node.key} → идём в левое поддерево", dict(path))
                if node.left is None:
                    node.left = TreeNode(key)
                    break
                node = node.left
            else:
                self.add_step(f"{key} > {node.key} → идём в правое поддерево", dict(path))
                if node.right is None:
                    node.right = TreeNode(key)
                    break
                node = node.right
        side = "левым" if key < node.key else "правым"
        path[key] = NEW
        self.add_step(f"Свободное место найдено: {key} становится {side} потомком узла {node.key}",
                      dict(path))
        return True

    def search(self, key):
        """Поиск ключа — спуск по одной ветви, O(h)."""
        self.start_operation()
        node = self.root
        path = {}
        while node is not None:
            self.ops += 1
            if key == node.key:
                path[key] = FOUND
                self.add_step(f"Ключ {key} найден!", dict(path))
                return True
            path[node.key] = CURRENT
            if key < node.key:
                self.add_step(f"{key} < {node.key} → влево", dict(path))
                node = node.left
            else:
                self.add_step(f"{key} > {node.key} → вправо", dict(path))
                node = node.right
        self.add_step(f"Дошли до пустой ссылки — ключа {key} в дереве нет", dict(path))
        return False

    def delete(self, key):
        """Удаление ключа. Три случая:
          1) у узла нет детей — просто убираем его;
          2) один ребёнок — ставим ребёнка на место узла;
          3) два ребёнка — находим минимальный узел правого поддерева
             (преемника), копируем его ключ в удаляемый узел и удаляем
             преемника (у него не больше одного ребёнка).
        """
        if self.root is None:
            raise StructureError("Дерево пустое — удалять нечего.")
        self.start_operation()
        # --- шаг 1: поиск удаляемого узла с запоминанием родителя ---
        parent = None
        node = self.root
        path = {}
        while node is not None and node.key != key:
            self.ops += 1
            path[node.key] = CURRENT
            self.add_step(f"Ищем {key}: сравниваем с {node.key}", dict(path))
            parent = node
            node = node.left if key < node.key else node.right
        if node is None:
            self.add_step(f"Ключ {key} не найден — удаление невозможно", dict(path))
            return False
        self.ops += 1
        path[key] = DELETE

        # --- шаг 2: случай с двумя детьми сводим к случаю с одним ---
        if node.left is not None and node.right is not None:
            self.add_step(f"У узла {key} два потомка — ищем минимальный узел в правом поддереве",
                          dict(path))
            succ_parent = node
            succ = node.right
            while succ.left is not None:
                self.ops += 1
                path[succ.key] = CURRENT
                self.add_step(f"Спускаемся влево: {succ.key}", dict(path))
                succ_parent = succ
                succ = succ.left
            path[succ.key] = FOUND
            self.add_step(f"Преемник — {succ.key}. Копируем его ключ на место {key}", dict(path))
            node.key = succ.key
            # теперь удаляем преемника (у него нет левого ребёнка)
            parent, node = succ_parent, succ
            self.add_step(f"Ключ заменён, удаляем старый узел-преемник", {node.key: FOUND})
        else:
            kind = "лист (нет потомков)" if node.left is None and node.right is None else "один потомок"
            self.add_step(f"Узел {key}: {kind}", dict(path))

        # --- шаг 3: удаление узла, у которого не больше одного ребёнка ---
        child = node.left if node.left is not None else node.right
        if parent is None:
            self.root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        self.ops += 1
        self.add_step(f"Удаление завершено. Высота дерева: {self.height()}")
        return True

    # ------------------------------------------------------------------
    # Обходы дерева
    # ------------------------------------------------------------------
    # Три «глубинных» обхода отличаются только тем, КОГДА посещается узел
    # относительно своих поддеревьев:
    #   прямой (pre-order):        узел → левое → правое
    #   симметричный (in-order):   левое → узел → правое
    #   обратный (post-order):     левое → правое → узел
    # Поэтому они реализованы одной рекурсивной функцией _traverse
    # с параметром order. Каждый узел посещается один раз — O(n).
    TRAVERSAL_NAMES = {
        "pre": "Прямой обход (узел → левое → правое)",
        "in": "Симметричный обход (левое → узел → правое)",
        "post": "Обратный обход (левое → правое → узел)",
    }

    def traverse(self, order):
        """Выполнить обход: order = "pre", "in" или "post"."""
        if self.root is None:
            raise StructureError("Дерево пустое — обходить нечего.")
        self.start_operation()
        result = []
        marks = {}
        self.add_step(self.TRAVERSAL_NAMES[order])
        self._traverse(self.root, order, result, marks)
        self.add_step("Обход завершён: " + ", ".join(map(str, result)), dict(marks))
        return result

    def inorder(self):
        """Симметричный обход. У BST он выдаёт ключи по возрастанию."""
        return self.traverse("in")

    def _traverse(self, node, order, result, marks):
        if node is None:
            return
        if order == "pre":
            self._visit(node, result, marks)
        self._traverse(node.left, order, result, marks)
        if order == "in":
            self._visit(node, result, marks)
        self._traverse(node.right, order, result, marks)
        if order == "post":
            self._visit(node, result, marks)

    def _visit(self, node, result, marks):
        """Посещение узла: добавляем ключ в результат и сохраняем шаг."""
        result.append(node.key)
        self.ops += 1
        marks[node.key] = CURRENT
        self.add_step(f"Посещаем {node.key}. Результат: {', '.join(map(str, result))}", dict(marks))
        marks[node.key] = VISITED

    # ------------------------------------------------------------------
    # Характеристики дерева
    # ------------------------------------------------------------------
    def find_min(self):
        """Минимальный ключ — самый левый узел: идём влево, пока можно. O(h)."""
        return self._find_extreme("left")

    def find_max(self):
        """Максимальный ключ — самый правый узел: идём вправо, пока можно. O(h)."""
        return self._find_extreme("right")

    def _find_extreme(self, side):
        if self.root is None:
            raise StructureError("Дерево пустое.")
        self.start_operation()
        word = "влево" if side == "left" else "вправо"
        node = self.root
        path = {}
        while True:
            self.ops += 1
            # getattr(node, "left") — то же самое, что node.left
            nxt = getattr(node, side)
            if nxt is None:
                break
            path[node.key] = CURRENT
            self.add_step(f"У узла {node.key} есть потомок {word} → переходим к {nxt.key}", dict(path))
            node = nxt
        path[node.key] = FOUND
        kind = "Минимум" if side == "left" else "Максимум"
        self.add_step(f"Идти {word} больше некуда. {kind} = {node.key}", dict(path))
        return node.key

    def compute_height(self):
        """Пошаговое вычисление высоты: высота узла =
        1 + max(высота левого поддерева, высота правого поддерева),
        высота пустого поддерева = -1. Каждый узел обрабатывается
        один раз (обратный обход) — O(n)."""
        if self.root is None:
            raise StructureError("Дерево пустое.")
        self.start_operation()
        marks = {}
        h = self._height_steps(self.root, marks)
        self.add_step(f"Высота дерева h = {h}", dict(marks))
        return h

    def _height_steps(self, node, marks):
        if node is None:
            return -1
        left = self._height_steps(node.left, marks)
        right = self._height_steps(node.right, marks)
        self.ops += 1
        h = 1 + max(left, right)
        marks[node.key] = CURRENT
        self.add_step(f"Узел {node.key}: 1 + max({left}, {right}) = {h}", dict(marks))
        marks[node.key] = VISITED
        return h

    def count_leaves(self):
        """Подсчёт листьев (узлов без потомков) — обход всех узлов, O(n)."""
        if self.root is None:
            raise StructureError("Дерево пустое.")
        self.start_operation()
        marks = {}
        leaves = []
        stack = [self.root]          # обход с помощью явного стека
        while stack:
            node = stack.pop()
            self.ops += 1
            if node.left is None and node.right is None:
                leaves.append(node.key)
                marks[node.key] = FOUND
                self.add_step(f"Узел {node.key} — лист (нет потомков). Листьев: {len(leaves)}",
                              dict(marks))
            else:
                marks[node.key] = VISITED
                self.add_step(f"Узел {node.key} — внутренний, проверяем его потомков", dict(marks))
            # правого кладём первым, чтобы левый был извлечён раньше
            for child in (node.right, node.left):
                if child is not None:
                    stack.append(child)
        self.add_step(f"Листьев: {len(leaves)} ({', '.join(map(str, leaves))})", dict(marks))
        return leaves
