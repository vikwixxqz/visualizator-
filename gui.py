"""
gui.py — главное окно программы.

Окно состоит из:
  * главного меню (Файл, Структура, Анимация, Справка);
  * панели инструментов (быстрые кнопки + регулятор скорости);
  * левой части — список структур и панель с формами текущей структуры;
  * центральной части — холст QGraphicsView, на котором рисуется структура;
  * нижней части — панель «Анализ сложности» и история шагов.

Пошаговая анимация устроена так: операция структуры возвращает список
шагов (Step). Окно запоминает этот список и по таймеру QTimer
показывает шаги один за другим. Таймер можно поставить на паузу
и листать шаги вручную кнопкой «Следующий шаг».
"""

import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (QAction, QActionGroup, QDialog, QFileDialog, QGraphicsScene,
                             QGraphicsView, QGroupBox, QHBoxLayout, QLabel, QListWidget,
                             QMainWindow, QMessageBox, QPlainTextEdit, QScrollArea, QSlider,
                             QSplitter, QStackedWidget, QVBoxLayout, QWidget)

import complexity
from experiment import ExperimentDialog
from drawer import COLORS, Drawer
from input_parser import InputError, read_text_file
from logger import SessionLogger
from panels import ArrayPanel, BSTPanel, GraphPanel, LinkedListPanel, QueuePanel, StackPanel
from structures import CURRENT, DELETE, FOUND, NEW, VISITED, StructureError

# журнал лежит рядом с программой, а не в «текущей папке» запуска
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_log.txt")


class MainWindow(QMainWindow):
    """Главное окно программной оболочки."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Визуализация различных структур данных")
        self.resize(1300, 820)

        self.logger = SessionLogger(LOG_PATH)

        # --- состояние анимации ---
        self.anim_panel = None    # панель, чьи шаги сейчас проигрываются
        self.anim_steps = []      # список шагов Step
        self.anim_index = 0       # номер следующего шага
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_step)   # каждый «тик» — следующий шаг

        # --- холст для рисования ---
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor("white"))
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)   # сглаживание линий
        self.drawer = Drawer(self.scene)

        self.create_central_area()
        self.create_actions()
        self.create_menu()
        self.create_toolbar()
        self.statusBar().showMessage(f"Сеанс начат {self.logger.session_start}. "
                                     f"Журнал: {LOG_PATH}")

        self.structure_list.setCurrentRow(0)   # по умолчанию открыт «Массив»

    # ==================================================================
    #                       ПОСТРОЕНИЕ ИНТЕРФЕЙСА
    # ==================================================================
    def create_central_area(self):
        """Боковое меню, холст, панель сложности и история."""
        # --- левая часть: список структур + формы ---
        self.panels = [ArrayPanel(self), StackPanel(self), QueuePanel(self),
                       LinkedListPanel(self), GraphPanel(self), BSTPanel(self)]
        self.structure_list = QListWidget()
        self.structure_list.setFont(QFont("Arial", 11))
        self.structure_list.setMaximumHeight(150)
        self.stack = QStackedWidget()   # показывает одну панель из нескольких
        for panel in self.panels:
            self.structure_list.addItem(panel.title)
            self.stack.addWidget(panel)
        self.structure_list.currentRowChanged.connect(self.switch_structure)

        scroll = QScrollArea()          # прокрутка, если форма не влезает
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.stack)
        # прокрутка только по вертикали — горизонтальная полоса не нужна
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("<b>Структуры данных</b>"))
        left_layout.addWidget(self.structure_list)
        left_layout.addWidget(scroll)
        left.setMinimumWidth(370)
        left.setMaximumWidth(420)

        # --- центр: холст + строка с текущим шагом ---
        canvas = QWidget()
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.view)
        self.step_label = QLabel("Выберите структуру и выполните операцию")
        self.step_label.setFont(QFont("Arial", 12))
        self.step_label.setWordWrap(True)
        self.step_label.setStyleSheet("padding: 6px; background: #eef3f8; color: #1d2b3a;")
        canvas_layout.addWidget(self.step_label)

        # --- низ: анализ сложности + история шагов ---
        info_group = QGroupBox("Анализ сложности")
        info_layout = QVBoxLayout(info_group)
        self.lbl_algorithm = QLabel("Алгоритм: —")
        self.lbl_complexity = QLabel("O(…)")
        self.lbl_complexity.setFont(QFont("Arial", 20, QFont.Bold))
        self.lbl_complexity.setStyleSheet("color: #c0392b;")
        self.lbl_estimate = QLabel("")
        self.lbl_ops = QLabel("")
        self.lbl_explain = QLabel("")
        info_layout.addWidget(self.lbl_algorithm)
        info_layout.addWidget(self.lbl_complexity)
        for label in (self.lbl_algorithm, self.lbl_estimate, self.lbl_ops, self.lbl_explain):
            label.setWordWrap(True)
        info_layout.addWidget(self.lbl_estimate)
        info_layout.addWidget(self.lbl_ops)
        info_layout.addWidget(self.lbl_explain)
        info_layout.addWidget(self.create_legend())
        info_layout.addStretch()

        history_group = QGroupBox("История шагов и операций")
        history_layout = QVBoxLayout(history_group)
        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setFont(QFont("Courier New", 10))
        history_layout.addWidget(self.history)

        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(info_group)
        bottom.addWidget(history_group)
        bottom.setSizes([450, 550])

        right = QSplitter(Qt.Vertical)
        right.addWidget(canvas)
        right.addWidget(bottom)
        right.setSizes([520, 280])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left)
        main_splitter.addWidget(right)
        main_splitter.setSizes([380, 920])
        self.setCentralWidget(main_splitter)

    def create_legend(self):
        """Легенда цветов подсветки."""
        legend = QWidget()
        layout = QHBoxLayout(legend)
        layout.setContentsMargins(0, 6, 0, 0)
        names = [(CURRENT, "текущий"), (NEW, "добавлен"), (DELETE, "удаляется"),
                 (FOUND, "найден"), (VISITED, "посещён")]
        for key, caption in names:
            label = QLabel(caption)
            label.setStyleSheet(f"background: {COLORS[key]}; color: black; "
                                "padding: 2px 6px; border: 1px solid #555;")
            layout.addWidget(label)
        layout.addStretch()
        return legend

    def create_actions(self):
        """Действия (QAction) используются и в меню, и на панели инструментов."""
        self.act_open = QAction("Загрузить из файла…", self)
        self.act_open.setShortcut("Ctrl+O")
        self.act_open.triggered.connect(lambda: self.execute(self.open_file))

        self.act_save_image = QAction("Сохранить изображение…", self)
        self.act_save_image.setShortcut("Ctrl+S")
        self.act_save_image.triggered.connect(self.save_image)

        self.act_log = QAction("Журнал сеанса", self)
        self.act_log.setShortcut("Ctrl+L")
        self.act_log.triggered.connect(self.show_log)

        self.act_exit = QAction("Выход", self)
        self.act_exit.setShortcut("Ctrl+Q")
        self.act_exit.triggered.connect(self.close)

        self.act_pause = QAction("Пауза", self)
        self.act_pause.setCheckable(True)      # кнопка-переключатель
        self.act_pause.setShortcut("Space")
        self.act_pause.toggled.connect(self.toggle_pause)

        self.act_step = QAction("Следующий шаг", self)
        self.act_step.setShortcut("Right")
        self.act_step.triggered.connect(self.manual_step)

        self.act_finish = QAction("Показать результат", self)
        self.act_finish.setShortcut("End")
        self.act_finish.triggered.connect(self.finish_animation)

        self.act_random = QAction("Случайные данные", self)
        self.act_random.setShortcut("Ctrl+G")
        self.act_random.triggered.connect(lambda: self.execute(self.current_panel().fill_random))

        self.act_experiment = QAction("Эксперимент со сложностью…", self)
        self.act_experiment.setShortcut("Ctrl+E")
        self.act_experiment.triggered.connect(self.show_experiment)

        self.act_reset = QAction("Очистить структуру", self)
        self.act_reset.setShortcut("Ctrl+R")
        self.act_reset.triggered.connect(self.reset_structure)

    def create_menu(self):
        """Главное меню окна."""
        menu = self.menuBar()

        file_menu = menu.addMenu("Файл")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save_image)
        file_menu.addSeparator()
        file_menu.addAction(self.act_log)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        # пункты меню «Структура» дублируют левый список;
        # QActionGroup делает так, что отмечен только один пункт
        struct_menu = menu.addMenu("Структура")
        self.structure_actions = []
        group = QActionGroup(self)
        for i, panel in enumerate(self.panels):
            action = QAction(panel.title, self, checkable=True)
            action.setShortcut(f"Ctrl+{i + 1}")
            # i=i — «запоминаем» текущее значение i для каждой лямбды
            action.triggered.connect(lambda checked, i=i: self.structure_list.setCurrentRow(i))
            group.addAction(action)
            struct_menu.addAction(action)
            self.structure_actions.append(action)
        struct_menu.addSeparator()
        struct_menu.addAction(self.act_random)
        struct_menu.addAction(self.act_reset)

        analysis_menu = menu.addMenu("Анализ")
        analysis_menu.addAction(self.act_experiment)
        analysis_menu.addAction("Таблица сложности", self.show_complexity_table)

        anim_menu = menu.addMenu("Анимация")
        anim_menu.addAction(self.act_pause)
        anim_menu.addAction(self.act_step)
        anim_menu.addAction(self.act_finish)

        help_menu = menu.addMenu("Справка")
        help_menu.addAction("Форматы входных файлов", self.show_formats)
        help_menu.addAction("О программе", self.show_about)

    def create_toolbar(self):
        """Панель инструментов с основными действиями и скоростью анимации."""
        toolbar = self.addToolBar("Инструменты")
        toolbar.setMovable(False)
        for action in (self.act_open, self.act_random, self.act_save_image, self.act_log):
            toolbar.addAction(action)
        toolbar.addSeparator()
        for action in (self.act_pause, self.act_step, self.act_finish, self.act_reset):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addAction(self.act_experiment)
        # регулятор скорости — на отдельной строке панели инструментов
        self.addToolBarBreak()
        toolbar = self.addToolBar("Скорость анимации")
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel("  Скорость анимации: медленно "))
        # слайдер задаёт «скорость», а задержку таймера считаем как 2100 - значение
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 2000)
        self.speed_slider.setValue(1300)
        self.speed_slider.setFixedWidth(160)
        self.speed_slider.valueChanged.connect(self.change_speed)
        toolbar.addWidget(self.speed_slider)
        toolbar.addWidget(QLabel(" быстро  "))
        self.speed_label = QLabel()
        toolbar.addWidget(self.speed_label)
        self.change_speed()

    # ==================================================================
    #                     ВЫПОЛНЕНИЕ ОПЕРАЦИЙ
    # ==================================================================
    def execute(self, handler):
        """Безопасный вызов обработчика кнопки.

        Все ожидаемые ошибки (неверный ввод, пустой стек...) превращаются
        во всплывающее предупреждение и запись в журнал. Любая другая
        ошибка тоже перехватывается, чтобы программа не закрылась аварийно.
        """
        try:
            handler()
        except (InputError, StructureError) as e:
            self.logger.log_error(str(e))
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:   # непредвиденная ошибка
            self.logger.log_error(f"Непредвиденная ошибка: {e!r}")
            QMessageBox.critical(self, "Непредвиденная ошибка", str(e))

    def current_panel(self):
        return self.stack.currentWidget()

    def show_operation(self, panel, algorithm, key, sizes, input_data, result, steps, ops):
        """Вызывается панелью после выполнения операции:
        вывод сложности, запись в журнал, запуск анимации."""
        notation, explanation = complexity.COMPLEXITY[key]
        estimate = complexity.estimate(notation, sizes)

        self.lbl_algorithm.setText(f"<b>{panel.title}</b>: {algorithm}")
        self.lbl_complexity.setText(notation)
        self.lbl_estimate.setText("Подстановка размеров: " + estimate)
        self.lbl_ops.setText(f"Фактически выполнено элементарных операций: <b>{ops}</b>")
        self.lbl_explain.setText("Почему так: " + explanation)

        self.logger.log_operation(panel.title, algorithm, input_data, result,
                                  f"{notation}; {estimate}", ops)
        self.add_history(f"▶ {algorithm} — {notation}\n  Результат: {result}")
        self.start_animation(panel, steps)

    def add_history(self, text):
        self.history.appendPlainText(text)

    def render(self, panel, state, marks):
        """Нарисовать состояние и подогнать масштаб холста."""
        panel.draw_state(state, marks)
        self.fit_scene()

    def fit_scene(self):
        """Если рисунок больше окна — уменьшаем масштаб, чтобы он влез целиком.
        Если меньше — показываем в натуральную величину по центру."""
        rect = self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self.scene.setSceneRect(rect)
        self.view.resetTransform()
        viewport = self.view.viewport().size()
        if rect.width() > viewport.width() or rect.height() > viewport.height():
            self.view.fitInView(rect, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        """При изменении размера окна заново подгоняем масштаб рисунка."""
        super().resizeEvent(event)
        self.fit_scene()

    # ==================================================================
    #                          АНИМАЦИЯ
    # ==================================================================
    def start_animation(self, panel, steps):
        self.timer.stop()
        self.anim_panel = panel
        self.anim_steps = steps
        self.anim_index = 0
        if not steps:
            panel.redraw()
            return
        self.next_step()                     # первый шаг показываем сразу
        if not self.act_pause.isChecked() and self.anim_index < len(self.anim_steps):
            self.timer.start(self.delay())

    def next_step(self):
        """Показать очередной шаг (вызывается таймером или вручную)."""
        if self.anim_panel is None or self.anim_index >= len(self.anim_steps):
            self.timer.stop()
            return
        step = self.anim_steps[self.anim_index]
        self.render(self.anim_panel, step.state, step.marks)
        total = len(self.anim_steps)
        self.anim_index += 1
        self.step_label.setText(f"Шаг {self.anim_index} из {total}: {step.text}")
        self.add_history(f"  {self.anim_index:>2}. {step.text}")
        if self.anim_index >= total:
            self.timer.stop()
            self.step_label.setText(self.step_label.text() + "   ✔ готово")

    def manual_step(self):
        """Кнопка «Следующий шаг»: включаем паузу и листаем вручную."""
        if not self.act_pause.isChecked():
            self.act_pause.setChecked(True)
        self.next_step()

    def finish_animation(self):
        """Сразу показать все оставшиеся шаги (переход к результату)."""
        self.timer.stop()
        while self.anim_panel is not None and self.anim_index < len(self.anim_steps):
            self.next_step()

    def stop_animation(self):
        """Прервать анимацию (например, при смене структуры)."""
        self.timer.stop()
        self.anim_panel = None
        self.anim_steps = []
        self.anim_index = 0

    def toggle_pause(self, paused):
        self.act_pause.setText("Продолжить" if paused else "Пауза")
        if paused:
            self.timer.stop()
        elif self.anim_panel is not None and self.anim_index < len(self.anim_steps):
            self.timer.start(self.delay())

    def delay(self):
        """Задержка между шагами в миллисекундах."""
        return 2100 - self.speed_slider.value()

    def change_speed(self):
        self.speed_label.setText(f"{self.delay()} мс/шаг ")
        self.timer.setInterval(self.delay())

    # ==================================================================
    #                    ОБРАБОТЧИКИ МЕНЮ
    # ==================================================================
    def switch_structure(self, row):
        """Переключение на другую структуру в боковом меню."""
        self.stop_animation()
        self.stack.setCurrentIndex(row)
        # пункты меню создаются позже списка, поэтому проверяем, что они уже есть
        if hasattr(self, "structure_actions"):
            self.structure_actions[row].setChecked(True)
        self.lbl_algorithm.setText(f"<b>{self.panels[row].title}</b>: выберите операцию")
        self.lbl_complexity.setText("O(…)")
        for label in (self.lbl_estimate, self.lbl_ops, self.lbl_explain):
            label.setText("")
        self.step_label.setText("Введите данные вручную или загрузите их из файла (Ctrl+O)")
        self.panels[row].redraw()

    def reset_structure(self):
        self.stop_animation()
        self.current_panel().reset()
        self.add_history(f"■ Структура «{self.current_panel().title}» очищена")
        self.step_label.setText("Структура очищена")

    def open_file(self):
        """Загрузить данные для текущей структуры из текстового файла."""
        panel = self.current_panel()
        examples = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
        path, _ = QFileDialog.getOpenFileName(self, f"Данные для: {panel.title}", examples,
                                              "Текстовые файлы (*.txt);;Все файлы (*)")
        if not path:          # пользователь нажал «Отмена»
            return
        text = read_text_file(path)
        self.add_history(f"📄 Загружен файл {os.path.basename(path)}")
        panel.load_file_text(text, os.path.basename(path))

    def save_image(self):
        """Сохранить текущий рисунок в PNG (удобно для пояснительной записки)."""
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "structure.png",
                                              "Изображение PNG (*.png)")
        if path:
            self.view.grab().save(path)
            self.statusBar().showMessage(f"Изображение сохранено: {path}", 5000)

    def show_log(self):
        """Окно с содержимым журнала session_log.txt."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Журнал сеанса — session_log.txt")
        dialog.resize(750, 550)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit(self.logger.read_all())
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 10))
        layout.addWidget(text)
        text.moveCursor(text.textCursor().End)   # прокрутка к последним записям
        dialog.exec_()

    def show_experiment(self):
        """Окно экспериментальной проверки сложности (experiment.py)."""
        self.stop_animation()
        dialog = ExperimentDialog(self, self.logger)
        dialog.exec_()

    def show_formats(self):
        lines = [f"<b>{p.title}</b>: {p.file_hint}" for p in self.panels]
        QMessageBox.information(self, "Форматы входных файлов",
                                "<br><br>".join(lines) +
                                "<br><br>Кодировка файлов — UTF-8. Примеры лежат в папке examples.")

    def show_complexity_table(self):
        rows = "".join(f"<tr><td>{key}</td><td><b>{o}</b></td><td>{text}</td></tr>"
                       for key, (o, text) in complexity.COMPLEXITY.items())
        box = QMessageBox(self)
        box.setWindowTitle("Таблица сложности операций")
        box.setText(f"<table border='1' cellpadding='3'>{rows}</table>")
        box.exec_()

    def show_about(self):
        QMessageBox.about(self, "О программе",
                          "<b>Визуализация различных структур данных</b><br>"
                          "Курсовая работа по дисциплине «Алгоритмы обработки данных».<br><br>"
                          "Python 3 + PyQt5.<br>Массив, стек, очередь, односвязный список, "
                          "граф, бинарное дерево поиска.")
