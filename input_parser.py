"""
input_parser.py — разбор и проверка входных данных.

Одни и те же функции используются и для ручного ввода (текст из полей
формы), и для чтения из файла. Благодаря этому оба режима ввода работают
одинаково и проверяются по одним правилам («сквозная» поддержка ввода).

Если данные некорректны, функции выбрасывают исключение InputError
с понятным пользователю текстом. Интерфейс ловит его и показывает
всплывающее окно с причиной ошибки.
"""

import re

# Допустимый диапазон значений элементов (чтобы числа помещались в ячейки)
MIN_VALUE = -999
MAX_VALUE = 999
# Максимальное число вершин графа (иначе рисунок становится нечитаемым)
MAX_VERTICES = 15


class InputError(Exception):
    """Ошибка во входных данных (буквы вместо чисел, пустой ввод и т.п.)."""
    pass


def parse_int(text, field_name="значение"):
    """Преобразовать строку в целое число с проверкой.

    int() выбрасывает ValueError, если в строке не число,
    — мы перехватываем его и заменяем на понятное сообщение.
    """
    text = text.strip()
    if text == "":
        raise InputError(f"Поле «{field_name}» не заполнено.")
    try:
        value = int(text)
    except ValueError:
        raise InputError(f"«{text}» — не целое число. Поле «{field_name}» должно содержать целое число.")
    if value < MIN_VALUE or value > MAX_VALUE:
        raise InputError(f"Число {value} вне допустимого диапазона [{MIN_VALUE}; {MAX_VALUE}].")
    return value


def parse_numbers(text):
    """Разобрать последовательность целых чисел.

    Разделителями могут быть пробелы, запятые, точки с запятой и переводы
    строк. re.split разбивает строку по регулярному выражению [\\s,;]+
    (один или несколько пробельных символов, запятых или точек с запятой).
    """
    parts = [p for p in re.split(r"[\s,;]+", text.strip()) if p != ""]
    if not parts:
        raise InputError("Не введено ни одного числа.")
    numbers = []
    for i, part in enumerate(parts, start=1):
        try:
            value = int(part)
        except ValueError:
            raise InputError(f"Элемент №{i} «{part}» не является целым числом.")
        if value < MIN_VALUE or value > MAX_VALUE:
            raise InputError(f"Элемент №{i} ({value}) вне диапазона [{MIN_VALUE}; {MAX_VALUE}].")
        numbers.append(value)
    return numbers


def vertex_names(n):
    """Имена вершин по умолчанию: A, B, C, ... (до 26 вершин)."""
    return [chr(ord("A") + i) for i in range(n)]


def _split_lines(text):
    """Непустые строки текста без пробелов по краям."""
    return [line.strip() for line in text.strip().splitlines() if line.strip() != ""]


def _parse_vertex_count(line):
    """Первая строка описания графа — число вершин."""
    try:
        n = int(line)
    except ValueError:
        raise InputError(f"Первая строка должна содержать число вершин, а не «{line}».")
    if n < 1 or n > MAX_VERTICES:
        raise InputError(f"Число вершин должно быть от 1 до {MAX_VERTICES}.")
    return n


def parse_matrix(text):
    """Разобрать матрицу смежности.

    Формат:
        5            <- число вершин n
        0 1 1 0 0    <- n строк по n чисел (0 или 1)
        ...
    Возвращает (имена вершин, матрица).
    """
    lines = _split_lines(text)
    if not lines:
        raise InputError("Описание графа пустое.")
    n = _parse_vertex_count(lines[0])
    rows = lines[1:]
    if len(rows) != n:
        raise InputError(f"Ожидалось {n} строк матрицы, получено {len(rows)}.")
    matrix = []
    for i, line in enumerate(rows):
        cells = [c for c in re.split(r"[\s,;]+", line) if c != ""]
        if len(cells) != n:
            raise InputError(f"В строке {i + 1} матрицы {len(cells)} чисел, а должно быть {n}.")
        row = []
        for j, cell in enumerate(cells):
            if cell not in ("0", "1"):
                raise InputError(f"Ячейка [{i + 1}][{j + 1}] = «{cell}»: допустимы только 0 и 1.")
            row.append(int(cell))
        if row[i] == 1:
            raise InputError(f"Петля в вершине {i + 1}: на главной диагонали должны быть нули.")
        matrix.append(row)
    return vertex_names(n), matrix


def parse_adjacency_list(text):
    """Разобрать список смежности.

    Формат:
        5            <- число вершин
        A: B, C      <- вершина, двоеточие, соседи через запятую/пробел
        B: A, D
        E:           <- у вершины может не быть соседей
    Возвращает (имена вершин, словарь {вершина: [соседи]}).
    """
    lines = _split_lines(text)
    if not lines:
        raise InputError("Описание графа пустое.")
    n = _parse_vertex_count(lines[0])
    rows = lines[1:]
    if len(rows) != n:
        raise InputError(f"Ожидалось {n} строк списка смежности, получено {len(rows)}.")
    names = []
    raw = {}
    for i, line in enumerate(rows):
        if ":" not in line:
            raise InputError(f"Строка {i + 2}: нет двоеточия. Формат строки — «A: B, C».")
        name, rest = line.split(":", 1)
        name = name.strip()
        if name == "" or " " in name:
            raise InputError(f"Строка {i + 2}: некорректное имя вершины «{name}».")
        if name in raw:
            raise InputError(f"Вершина «{name}» описана дважды.")
        names.append(name)
        raw[name] = [v for v in re.split(r"[\s,;]+", rest.strip()) if v != ""]
    # проверяем, что все соседи — существующие вершины
    for name in names:
        for v in raw[name]:
            if v not in raw:
                raise InputError(f"У вершины {name} указан сосед «{v}», которого нет в списке вершин.")
            if v == name:
                raise InputError(f"Петля в вершине {name} не поддерживается.")
        if len(set(raw[name])) != len(raw[name]):
            raise InputError(f"У вершины {name} сосед указан повторно.")
    return names, raw


def detect_graph_format(text):
    """Определить формат описания графа: если есть двоеточия — это
    список смежности, иначе — матрица."""
    return "list" if ":" in text else "matrix"


def read_text_file(path):
    """Прочитать текстовый файл в кодировке UTF-8.

    Ошибки открытия (нет файла, нет прав) и ошибки кодировки
    превращаются в InputError с понятным текстом.
    """
    try:
        # utf-8-sig дополнительно убирает служебный символ BOM,
        # который добавляет «Блокнот» Windows
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except UnicodeDecodeError:
        raise InputError("Файл не в кодировке UTF-8. Пересохраните его в UTF-8.")
    except OSError as e:
        raise InputError(f"Не удалось открыть файл: {e.strerror}.")
    if text.strip() == "":
        raise InputError("Файл пустой.")
    return text
