import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import re
import sqlite3
from datetime import date


def sqlite_like(template_, value_):  # эта и последующие функции
    # служат для обеспечения работоспособности функций LIKE, UPPER, LOWER языка SQL для русского текста
    return sqlite_like_escape(template_, value_, None)


def sqlite_like_escape(template_, value_, escape_):
    re_ = re.compile(template_.lower().
                     replace(".", "\\.").replace("^", "\\^").replace("$", "\\$").
                     replace("*", "\\*").replace("+", "\\+").replace("?", "\\?").
                     replace("{", "\\{").replace("}", "\\}").replace("(", "\\(").
                     replace(")", "\\)").replace("[", "\\[").replace("]", "\\]").
                     replace("_", ".").replace("%", ".*?"))
    return re_.match(value_.lower()) is not None


def sqlite_nocase_collation(value1_, value2_):
    return (value1_.encode('utf-8').lower() < value2_.encode('utf-8').lower()) - (
            value1_.encode('utf-8').lower() > value2_.encode('utf-8').lower())


def create_db(con):
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS dishes("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "name varchar(255),"
                "calories int,"
                "proteins int,"
                "fats int,"
                "carbs int,"
                "date varchar(255))")


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.con = sqlite3.connect("food.db")
        create_db(self.con)

        # self.con.create_collation("BINARY", sqlite_nocase_collation)
        # self.con.create_collation("NOCASE", sqlite_nocase_collation)
        #
        # self.con.create_function("LIKE", 2, sqlite_like)

        self.fill_table()

    def initUI(self):
        self.setWindowTitle("Трекер для Тора")
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QtWidgets.QTabWidget(self)

        self.add_food_tab = QtWidgets.QWidget()
        self.chart_tab = QtWidgets.QWidget()

        self.tab_widget.addTab(self.add_food_tab, "Добавить блюдо")
        self.tab_widget.addTab(self.chart_tab, "График калорий")

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        self.name_input = QtWidgets.QLineEdit(self)
        self.name_input.setPlaceholderText("Название блюда")

        self.calories_input = QtWidgets.QLineEdit(self)
        self.calories_input.setPlaceholderText("Калорий на 100г")

        self.proteins_input = QtWidgets.QLineEdit(self)
        self.proteins_input.setPlaceholderText("Белков на 100г")

        self.fats_input = QtWidgets.QLineEdit(self)
        self.fats_input.setPlaceholderText("Жиров на 100г")

        self.carbs_input = QtWidgets.QLineEdit(self)
        self.carbs_input.setPlaceholderText("Углеводов на 100г")

        self.date_input = QtWidgets.QDateEdit(self)
        self.date_input.setDate(date.today())

        add_button = QtWidgets.QPushButton("Добавить блюдо", self)
        add_button.clicked.connect(self.add_dish)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Название блюда:", self.name_input)
        form_layout.addRow("Калории:", self.calories_input)
        form_layout.addRow("Белки:", self.proteins_input)
        form_layout.addRow("Жиры:", self.fats_input)
        form_layout.addRow("Углеводы:", self.carbs_input)
        form_layout.addRow("Дата:", self.date_input)
        form_layout.addWidget(add_button)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Название', 'Калории', 'Белки', 'Жиры', 'Углеводы', 'Дата'])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        form_layout.addWidget(self.table)

        self.add_food_tab.setLayout(form_layout)

        fig, ax = plt.subplots()
        self.canvas = FigureCanvas(fig)
        self.date_from = QtWidgets.QDateEdit(self)

        self.date_to = QtWidgets.QDateEdit(self)
        self.date_to.setDate(date.today())

        self.show_chart_button = QtWidgets.QPushButton("Показать график", self)
        self.show_chart_button.clicked.connect(self.show_chart)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("С этой даты:", self.date_from)
        form_layout.addRow("До этой даты:", self.date_to)
        form_layout.addWidget(self.show_chart_button)

        self.chart_layout = QtWidgets.QVBoxLayout()
        self.chart_layout.addLayout(form_layout)
        self.chart_layout.addWidget(self.canvas)

        self.chart_tab.setLayout(self.chart_layout)

        self.setLayout(main_layout)

    def add_dish(self):
        name = self.name_input.text()
        calories = self.calories_input.text()
        proteins = self.proteins_input.text()
        fats = self.fats_input.text()
        carbs = self.carbs_input.text()
        date = self.date_input.date().toString("yyyyMMdd")

        if not all([name, calories, proteins, fats, carbs, date]):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        cur = self.con.cursor()
        cur.execute("INSERT INTO dishes (name, calories, proteins, fats, carbs, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, int(calories), int(proteins), int(fats), int(carbs), date))
        self.con.commit()

        self.fill_table()
        self.name_input.clear()
        self.calories_input.clear()
        self.proteins_input.clear()
        self.fats_input.clear()
        self.carbs_input.clear()
        self.date_input.clear()

    def fill_table(self):
        row_position = self.table.rowCount()
        while row_position >= 0:
            self.table.removeRow(row_position)
            row_position -= 1

        cur = self.con.cursor()
        food_data = cur.execute("SELECT name, calories, proteins, fats, carbs, date FROM dishes")
        for [name, calories, proteins, fats, carbs, date] in food_data.fetchall():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(name))
            self.table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(calories)))
            self.table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(str(proteins)))
            self.table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(str(fats)))
            self.table.setItem(row_position, 4, QtWidgets.QTableWidgetItem(str(carbs)))
            self.table.setItem(row_position, 5, QtWidgets.QTableWidgetItem(date[6:] + '.' + date[4:6] + '.' + date[:4]))

    def show_chart(self):
        date_from = self.date_from.date().toString("yyyyMMdd")
        date_to = self.date_to.date().toString("yyyyMMdd")
        print(date_to, date_from)
        cur = self.con.cursor()
        food_data = cur.execute(
            """SELECT name, calories, date FROM dishes WHERE date <= %s AND date >= %s""" % (date_to, date_from))
        names = []
        calories = []
        for [name, calor, _] in food_data.fetchall():
            names.append(name)
            calories.append(calor)

        fig, ax = plt.subplots()
        ax.plot(names, calories, marker='o')
        ax.set_xlabel('Блюда')
        ax.set_ylabel('Калории')
        ax.set_title('Динамика калорий')

        plt.xticks(rotation=45)
        plt.tight_layout()

        self.chart_layout.removeWidget(self.canvas)
        self.canvas = FigureCanvas(fig)
        chart_window = QtWidgets.QWidget()
        chart_window.setWindowTitle("Динамика изменения калорий")
        chart_window.resize(600, 400)
        self.canvas.draw()

        self.chart_layout.addWidget(self.canvas)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
