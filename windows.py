import os
import sys
import pickle
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QDialog, QMessageBox, QInputDialog
from multiprocessing import Process
from cryptography.fernet import Fernet

from dialogs import ScriptDialog
from keyboard import KeyboardListener


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.fernet = self.get_secret_key()
        self.setFixedSize(1200, 400)

        keyboard_label = QLabel(self)
        keyboard_pixmap = QPixmap("keyboard.png")
        keyboard_label.setPixmap(keyboard_pixmap)
        keyboard_label.setGeometry(0, 0, 800, 400)

        widget = QWidget(self)
        self.keyboard_layout = QGridLayout(widget)
        self.setCentralWidget(widget)

        buttons = [
            ["esc", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"],
            ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "backspace"],
            ["tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["caps_lock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "enter"],
            ["shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "shift_r"],
            ["ctrl_l", "cmd", "alt_l", "space", "alt_gr", "cmd_r", "ctrl_r"]
        ]

        for row in range(len(buttons)):
            for col in range(len(buttons[row])):
                button_label = buttons[row][col]
                button = QPushButton(button_label, self)
                button.setStyleSheet('background-color: gray')
                button.setFixedSize(60, 60)
                button.clicked.connect(self.on_key_pressed)
                self.keyboard_layout.addWidget(button, row, col)

        button = QPushButton('Запустить', self)
        button.setStyleSheet('background-color: red')
        button.setFixedSize(180, 60)
        button.clicked.connect(self.start_program)
        self.keyboard_layout.addWidget(button)

        load_config_button = QPushButton('Загрузить конфигурацию', self)
        load_config_button.setStyleSheet('background-color: orange')
        load_config_button.setFixedSize(180, 60)
        load_config_button.clicked.connect(self.load_config)
        self.keyboard_layout.addWidget(load_config_button)

        create_config_button = QPushButton('Сохранить конфигурацию', self)
        create_config_button.setStyleSheet('background-color: yellow')
        create_config_button.setFixedSize(180, 60)
        create_config_button.clicked.connect(self.create_config)
        self.keyboard_layout.addWidget(create_config_button)

    def load_config(self):
        with open('config.pkl', 'rb') as f:
            data = pickle.load(f)
        options = data.get('configs', {}).keys()
        if options:
            insert, _ = QInputDialog.getText(self, 'Выберите конфигурацию', 'Введите название:')
            buttons = data['configs'].get(insert)
            buttons_dict = self.get_all_buttons_dict()
            for key, value in buttons.items():
                buttons_dict.get(key).script_address = value
                buttons_dict.get(key).setStyleSheet('background-color: blue')

    def create_config(self):
        insert, _ = QInputDialog.getText(self, 'Сохранение конфигурации', 'Введите название:')
        buttons = self.get_buttons_with_macros()
        buttons_scripts = {}
        for button in buttons:
            buttons_scripts[button.text()] = button.script_address
        with open('config.pkl', 'rb') as f:
            data = pickle.load(f)

        configs = data.get('configs', {})
        configs[insert] = buttons_scripts
        data['configs'] = configs
        with open('config.pkl', 'wb') as f:
            pickle.dump(data, f)

    def get_secret_key(self):
        if os.path.exists('config.pkl'):
            with open('config.pkl', 'rb') as f:
                secret_key = pickle.load(f).get('secret_key')
        else:
            self.ask_for_activation_key()
            with open('config.pkl', 'wb') as f:
                secret_key = Fernet.generate_key()
                pickle.dump(
                    {'secret_key': secret_key},
                    f
                )
        return Fernet(secret_key)

    def ask_for_activation_key(self):
        insert, _ = QInputDialog.getText(self, 'Активация программы', 'Введите ключ:')
        if not str(insert).isdigit():
            QMessageBox.information(self, "Внимание", "ключ не действителен.")
            sys.exit()

    def start_program(self):
        buttons = self.get_buttons_with_macros()
        for button in buttons:
            button.macros_script = self.read_script(button)
        QMessageBox.information(
            self,
            "Внимание",
            "ПОСЛЕ клика кнопки 'OK' будут запущены макросы. для остановки макросов нажмите f8"
        )
        listener = KeyboardListener(keyboard_mapping=buttons)
        Process(target=listener.listen_keyboard()).start()

    def read_script(self, button):
        with open(f'{button.script_address}', 'r') as file:
            script = file.read()
            return script

    def on_key_pressed(self):
        try:
            script_address = self.sender().script_address
        except AttributeError:
            script_address = ''
        button_text = self.sender().text()
        dialog = ScriptDialog(button_text, script_address, self.fernet)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            file_name = dialog.get_file_name()
            if file_name:
                self.sender().setStyleSheet('background-color: blue')
            else:
                self.sender().setStyleSheet('background-color: gray')
            self.sender().script_address = file_name

    def get_all_buttons_dict(self):
        buttons = {}
        for row in range(self.keyboard_layout.rowCount()):
            for col in range(self.keyboard_layout.columnCount()):
                item = self.keyboard_layout.itemAtPosition(row, col)
                if item is not None and isinstance(item.widget(), QPushButton):
                    buttons[item.widget().text()] = item.widget()
        return buttons

    def get_buttons_with_macros(self):
        buttons = []
        for row in range(self.keyboard_layout.rowCount()):
            for col in range(self.keyboard_layout.columnCount()):
                item = self.keyboard_layout.itemAtPosition(row, col)
                if item is not None and isinstance(item.widget(), QPushButton):
                    try:
                        if item.widget().script_address:
                            buttons.append(item.widget())
                    except Exception as exc:
                        pass
        return buttons
