"""
main.py — точка входа в программу.

Запуск:  python main.py

Здесь только создаётся объект приложения Qt, главное окно и
запускается цикл обработки событий (app.exec_()) — он работает,
пока пользователь не закроет окно.
"""

import sys

from PyQt5.QtWidgets import QApplication

from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # единый внешний вид на Windows/Linux/macOS
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
