import os
import re
import sys
import time  # noqa
import pickle
import getpass
from PySide6.QtGui import QPixmap, QCloseEvent
from PySide6.QtWidgets import QLabel, QPushButton, QWidget, QGridLayout, QMessageBox, QInputDialog, QHBoxLayout
from cryptography.fernet import Fernet
from pynput.keyboard import Key, Listener, Controller  # noqa
from pynput.keyboard._win32 import KeyCode  # noqa

from keyboard import KeyboardListener
from redactor_window import RedactorWindow
from base_window import BaseWindow


class MainWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.fernet = self.get_secret_key()
        self.keyboard_listener = KeyboardListener()
        self.key_class_buttons = self.keyboard_listener.key_class_buttons
        self.keycode_class_buttons = self.keyboard_listener.keycode_class_buttons

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
        button_funcs_does_not_exist = {
            "`": "backtick",
            "-": "hyphen",
            "=": "equal_sign",
            "[": "left_square_bracket",
            "]": "right_square_bracket",
            "\\": "backslash",
            ";": "semicolon",
            "'": "single_quote",
            ":": "colon",
            ".": "period",
            "/": "forward_slash",
            ",": "comma",
            "0": "zero",
            "1": "one",
            "2": "two",
            "3": "three",
            "4": "four",
            "5": "five",
            "6": "six",
            "7": "seven",
            "8": "eight",
            "9": "nine"
        }

        for row in range(len(buttons)):
            for col in range(len(buttons[row])):
                button_label = buttons[row][col]
                button = QPushButton(button_label, self)
                button.setStyleSheet('background-color: gray')
                button.setFixedSize(60, 40)
                button.func_name = button_funcs_does_not_exist.get(button_label, button_label)
                button.clicked.connect(self.on_key_pressed)
                self.keyboard_layout.addWidget(button, row, col)

        bottom_widget = QWidget(self)
        bottom_layout = QHBoxLayout(bottom_widget)

        button = QPushButton('Запустить программу', self)
        button.setStyleSheet('background-color: lightgray')
        button.setFixedSize(180, 40)
        button.clicked.connect(self.start_program)
        bottom_layout.addWidget(button)

        load_presets_button = QPushButton('Загрузить конфигурацию', self)
        load_presets_button.setStyleSheet('background-color: lightgray')
        load_presets_button.setFixedSize(180, 40)
        load_presets_button.clicked.connect(self.load_presets)
        bottom_layout.addWidget(load_presets_button)

        create_presets_button = QPushButton('Сохранить конфигурацию', self)
        create_presets_button.setStyleSheet('background-color: lightgray')
        create_presets_button.setFixedSize(180, 40)
        create_presets_button.clicked.connect(self.create_presets)
        bottom_layout.addWidget(create_presets_button)

        self.keyboard_layout.addWidget(bottom_widget, len(buttons), 0, 1, len(buttons[0]))

    def create_button_function_name(self, button_text):
        pattern = r'[^\w\s]'
        regex = re.compile(pattern)

        if regex.search(button_text):
            return button_text

    def load_presets(self):
        data = self.read_presets()
        presets = data.get('presets', {})
        if presets:
            item, ok = QInputDialog.getItem(self, 'Выберите скрипт', 'Выберите скрипт из списка:', presets.keys(), 0,
                                            False)
            if ok and item:
                buttons = data['presets'].get(item)
                buttons_dict = self.get_all_buttons_dict()
                for key, value in buttons.items():
                    buttons_dict.get(key).script = value
                    buttons_dict.get(key).setStyleSheet('background-color: blue')

    def create_presets(self):
        insert, _ = QInputDialog.getText(self, 'Сохранение конфигурации', 'Введите название:')
        buttons = self.get_buttons_with_macros()
        buttons_scripts = {}
        for button in buttons:
            buttons_scripts[button.text()] = button.script

        data = self.read_presets()
        presets = data.get('presets', {})

        presets[insert] = buttons_scripts
        data['presets'] = presets
        self.write_presets(data)

    def get_secret_key(self):
        if os.path.exists('config.pkl'):
            data = self.read_config()
            secret_key = data.get('secret_key')
            user = data.get('user')
            current_user = getpass.getuser()
            if not secret_key or not user or user != current_user:
                self.ask_for_activation_key()
        else:
            self.ask_for_activation_key()
            data = self.read_config()
            secret_key = Fernet.generate_key()
            data['secret_key'] = secret_key
            self.write_config(data)

            with open('presets.pkl', 'wb') as f:
                pickle.dump(
                    {'presets': {}},
                    f
                )
            with open('scripts.pkl', 'wb') as f:
                pickle.dump(
                    {'scripts': {}},
                    f
                )
        return Fernet(secret_key)

    def ask_for_activation_key(self):
        insert, _ = QInputDialog.getText(self, 'Активация программы', 'Введите ключ:')
        if not str(insert).isdigit():
            QMessageBox.information(self, "Внимание", "ключ не действителен.")
            sys.exit()
        current_user = getpass.getuser()
        data = {
            'user': current_user,
            'activation_key': insert
        }
        with open('config.pkl', 'wb') as f:
            pickle.dump(data, f)

    def start_program(self):
        buttons = self.get_buttons_with_macros()
        scenario = self.write_buttons_scenaries(buttons)
        QMessageBox.information(
            self,
            "Внимание",
            "ПОСЛЕ клика кнопки 'OK' будут запущены макросы, а управление передано клавиатуре."
            "Для оптимизации ресурсов текущая программа будет скрыта. для остановки нажмите f8"
        )
        self.hide()
        exec(scenario)
        self.show()

    def on_key_pressed(self):
        button = self.sender()
        data = self.read_scripts()
        r = RedactorWindow(parent=self, button=button, data=data.get('scripts'))
        r.show()

    def set_button_script(self, button, script):
        button.script = script
        if script:
            button.setStyleSheet('background-color: blue')
        else:
            button.setStyleSheet('background-color: gray')

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
                        if item.widget().script:
                            buttons.append(item.widget())
                    except Exception as exc:
                        pass
        return buttons

    def write_buttons_scenaries(self, buttons):
        key_buttons = []
        keycode_buttons = []

        scenario = '''
class Executor:
    def __init__(self):
        self.keyboard = Controller()\n
'''

        for button in buttons:
            scenario += f'''
    def {button.func_name.lower()}(self):
'''
            if button.text().lower() in self.key_class_buttons.keys():
                key_buttons.append(button)
            else:
                keycode_buttons.append(button)

            for command in button.script.split(';'):
                scenario += f'''
        {command}
'''
        scenario += f'''
    def on_press(self, key):
        print(key)
'''
        if keycode_buttons:
            scenario += f'''
        if isinstance(key,KeyCode):
'''
            for button in keycode_buttons:
                scenario += f'''
            if key.char == {self.keycode_class_buttons.get(button.text().lower())}:
                self.{button.text().lower()}()
'''
        if key_buttons:
            scenario += f'''
        if isinstance(key,Key):
'''
            for button in key_buttons:
                scenario += f'''
            if key == {self.key_class_buttons.get(button.text().lower())}:
                self.{button.text().lower()}()
'''

        scenario += '''
    def on_release(self, key):
        return key != Key.f8
        
    def listen(self):
        with Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()
            
a = Executor()
a.listen()
    '''
        return scenario

    def remember_keyboard(self):
        buttons = self.get_buttons_with_macros()
        buttons_scripts = {}
        for button in buttons:
            buttons_scripts[button.text()] = button.script
        data = self.read_presets()

        data['last_keyboard'] = buttons_scripts
        self.write_presets(data)

    def load_previous_keyboard(self):
        data = self.read_presets()
        last_keyboard = data.get('last_keyboard', {})

        buttons_dict = self.get_all_buttons_dict()
        for key, value in last_keyboard.items():
            buttons_dict.get(key).script = value
            buttons_dict.get(key).setStyleSheet('background-color: blue')

    def show(self) -> None:
        self.load_previous_keyboard()
        super().show()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.remember_keyboard()
        super().closeEvent(event)
