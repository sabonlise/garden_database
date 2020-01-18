from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QTableWidgetItem
from mainForm import Ui_MainWindow
import addDialog
import editDialog
import remind
import sqlite3
import sys
import time as tm

path = 'garden.db'
con = sqlite3.connect(path)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS trees (id INTEGER PRIMARY KEY AUTOINCREMENT, 
kind TEXT, latin TEXT, russian TEXT, age INT,
landing_year INT, curtain TEXT, amount INT, height INT, 
diameter INT, longitude TEXT, latitude TEXT, time TIME)''')


class MainApp(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        self.setupUi(self)
        self.load_database()
        self.initUi()
        self.con = sqlite3.connect(path)
        self.modified = {}
        self.titles = None

        self.add = AddDialog()
        self.edit = EditDialog()
        self.prompt = Reminder()

    def initUi(self):  # инициализация объектов
        self.setupUi(self)
        self.load_database()
        self.show()
        # Подключаем все кнопки к функциям
        self.btn_add.clicked.connect(self.show_add_dialog)
        self.btn_delete.clicked.connect(self.delete_data)
        self.btn_edit.clicked.connect(self.show_edit_dialog)
        self.btn_save.clicked.connect(self.save_data)
        self.pushButton.clicked.connect(self.search_data)  # кнопка поиска
        self.btn_prompt.clicked.connect(self.show_prompt_dialog)  # кнопка напоминания о поливах
        self.tableWidget.itemChanged.connect(self.item_changed)

    def load_database(self):
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)
        con = sqlite3.connect(path)
        content = 'SELECT * FROM trees'
        res = con.execute(content)
        for row_index, row_data in enumerate(res):
            self.tableWidget.insertRow(row_index)
            for col_index, col_data in enumerate(row_data):
                self.tableWidget.setItem(row_index, col_index, QTableWidgetItem(str(col_data)))
        # Загружаем базу в tableWidget
        con.close()

    def show_add_dialog(self):
        self.add.btn_add.clicked.connect(self.add_data)
        self.add.btn_clear.clicked.connect(self.clear_data)
        self.add.exec_()

    def show_edit_dialog(self):
        self.edit.buttonBox.accepted.connect(self.update_data)
        self.edit.exec_()

    def clear_data(self):
        self.add.kind.setText('')
        self.add.latin.setText('')
        self.add.russian.setText('')
        self.add.age.setText('')
        self.add.landing_yaer.setText('')
        self.add.curtain.setText('')
        self.add.amount.setText('')
        self.add.height.setText('')
        self.add.diameter.setText('')
        self.add.longitude.setText('')
        self.add.latitude.setText('')

    def show_prompt_dialog(self):
        try:
            cur = self.con.cursor()
            result = cur.execute(f'SELECT kind, longitude, latitude, time FROM trees ORDER BY time').fetchall()
            # Сортируем таблицу по времени полива
            self.prompt.tableWidget.setRowCount(len(result))
            self.prompt.tableWidget.setColumnCount(len(result[0]))
            for i, elem in enumerate(result):
                for j, val in enumerate(elem):
                    self.prompt.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
            self.prompt.exec_()
            # Выводим всё на виджет открывшегося окна
        except Exception as err:
            pass

    def add_data(self):
        try:
            kind = self.add.kind.text()
            latin = self.add.latin.text()
            russian = self.add.russian.text()
            age = self.add.age.text()
            landing_year = self.add.landing_yaer.text()
            curtain = self.add.curtain.text()
            amount = self.add.amount.text()
            height = self.add.height.text()
            diameter = self.add.diameter.text()
            longitude = self.add.longitude.text()
            latitude = self.add.latitude.text()
            time = self.add.timeEdit.text()
            val = (kind, latin, russian, age, landing_year, curtain, amount, height, diameter, longitude, latitude, time)
            sql = '''INSERT INTO 
            trees(kind, latin, russian, age, landing_year, curtain, amount, height, diameter, longitude, latitude, time)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            cur.execute(sql, val)
            con.commit()
            # Добавляем новый элемент в базу
            self.load_database()
        except Exception as error:  # логируем ошибки
            with open('../data/log.txt', encoding='utf8', mode='a') as f:  # логируем ошибки
                f.write(f'{tm.strftime("[%Y-%m-%d %H:%M]", tm.localtime())} add_data: {error}\n')

    def delete_data(self):
        rows = list(set([i.row() for i in self.tableWidget.selectedItems()]))
        # Получаем список строк без повторов
        ids = [self.tableWidget.item(i, 0).text() for i in rows]
        # Получаем номера записей, которые нужно будет удалить
        valid = QMessageBox.question(self, '',
                                     "Действительно удалить элемент(ы) под номером " +
                                     ",".join(ids), QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            cur = self.con.cursor()
            cur.execute("DELETE from trees WHERE ID in (" +
                        ", ".join('?' * len(ids)) + ")", ids)
            self.con.commit()
            # Сохраняем изменения
            self.load_database()

    def update_data(self):
        try:
            cur = self.con.cursor()
            result = cur.execute("SELECT * FROM trees WHERE id=?",
                                 (self.edit.textEdit.toPlainText(),)).fetchall()
            # Находим нужный нам элемент по введённому номеру
            self.tableWidget.setRowCount(len(result))
            self.tableWidget.setColumnCount(len(result[0]))
            self.titles = [description[0] for description in cur.description]
            # Заполняем таблицу полученными элементами
            for i, elem in enumerate(result):
                for j, val in enumerate(elem):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
            self.modified = {}
            # Выводим весь ряд элемента на виджет
        except Exception as err:
            with open('../data/log.txt', encoding='utf8', mode='a') as f:  # логируем ошибки
                f.write(f'{tm.strftime("[%Y-%m-%d %H:%M]", tm.localtime())} update_result: {err}\n')

    def search_data(self):
        try:
            cur = self.con.cursor()
            result = cur.execute(f'SELECT * FROM trees WHERE kind like "%{self.search.text()}%"').fetchall()
            # Выполняем поиск по столбцу "Семейство" из введённого текста в QLineEdit
            self.tableWidget.setRowCount(len(result))
            self.tableWidget.setColumnCount(len(result[0]))
            for i, elem in enumerate(result):
                for j, val in enumerate(elem):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
            # Выводим всё на виджет
        except Exception:
            self.search.setText('Ничего не найдено')

    def item_changed(self, item):
        try:
            # Если значение в ячейке было изменено,
            # то в словарь записывается пара: название поля, новое значение
            self.modified[self.titles[item.column()]] = item.text()
        except TypeError:
            pass
            # Пропускаем ошибки неверного типа, так как они будут возникать (но ни на что не влиять)
            # после функции add_data, так как данные будут не изменяться, а добавляться

    def save_data(self):
        try:
            if self.modified:
                cur = self.con.cursor()
                que = "UPDATE trees SET\n"
                for key in self.modified.keys():
                    que += "{}='{}'\n".format(key, self.modified.get(key))
                que += "WHERE id = ?"
                cur.execute(que, (self.edit.textEdit.toPlainText(),))
                self.con.commit()
                # Сохраняем внесённые изменения
                self.load_database()
        except Exception as err:
            with open('../data/log.txt', encoding='utf8', mode='a') as f:  # логируем ошибки
                f.write(f'{tm.strftime("[%Y-%m-%d %H:%M]", tm.localtime())} save_data: {err}\n')

    def remind(self):
        try:
            cur = self.con.cursor()
            result = cur.execute(f'SELECT kind, longitude, latitude, time FROM trees ORDER BY time').fetchall()
            # Выполняем поиск по столбцу "Семейство" из введённого текста в QLineEdit
            self.self.prompt.tableWidget.setRowCount(len(result))
            self.self.prompt.tableWidget.setColumnCount(len(result[0]))
            for i, elem in enumerate(result):
                for j, val in enumerate(elem):
                    self.self.prompt.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
            # Выводим всё на виджет
        except Exception:
            self.search.setText('Ничего не найдено')


class AddDialog(QDialog, addDialog.Ui_Dialog):

    def __init__(self, parent=None):
        super(AddDialog, self).__init__(parent)
        self.setupUi(self)


class EditDialog(QDialog, editDialog.Ui_Dialog):

    def __init__(self, parent=None):
        super(EditDialog, self).__init__(parent)
        self.setupUi(self)


class Reminder(QDialog, remind.Ui_Dialog):

    def __init__(self, parent=None):
        super(Reminder, self).__init__(parent)
        self.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec())
