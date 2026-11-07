"""
main.py — точка входа в программу.

Запуск:  python main.py

Здесь только создаётся объект приложения Qt, главное окно и
запускается цикл обработки событий (app.exec_()) — он работает,
пока пользователь не закроет окно.
"""

import os
import sys

import PyQt5
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication

from gui import MainWindow


def fix_qt_plugin_path():
    """Явно указать Qt, где лежат его плагины.

    На Windows Qt5 часто не может сам найти папку plugins, если в пути
    есть русские буквы (например, C:\\Users\\Вика\\...). Тогда программа
    не запускается с ошибкой «Could not find the Qt platform plugin
    "windows"». Поэтому находим папку плагинов рядом с установленным
    пакетом PyQt5 и передаём её Qt вручную.
    """
    package_dir = os.path.dirname(PyQt5.__file__)
    # в новых версиях PyQt5 папка называется Qt5, в старых — Qt
    for qt_dir in ("Qt5", "Qt"):
        plugins = os.path.join(package_dir, qt_dir, "plugins")
        if os.path.isdir(plugins):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(plugins, "platforms")
            QCoreApplication.setLibraryPaths([plugins])
            break


def main():
    fix_qt_plugin_path()   # обязательно до создания QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # единый внешний вид на Windows/Linux/macOS
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
