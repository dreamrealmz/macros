import os
import sys
import pickle
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QDialog, \
    QVBoxLayout, QFileDialog, QMessageBox, QInputDialog
from pynput.keyboard import Key, Listener, Controller
from pynput.keyboard._win32 import KeyCode  # noqa
from multiprocessing import Process
from cryptography.fernet import Fernet

key = Fernet.generate_key()
fernet = Fernet(key)


class ScriptDialog(QDialog):

    def __init__(self, button_text, script_address, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Скрипт для {button_text}: {script_address}')
        self.setFixedSize(360, 140)

        create_button = QPushButton("Создать скрипт", self)
        create_button.clicked.connect(self.create_script)

        open_button = QPushButton("Открыть скрипт", self)
        open_button.clicked.connect(self.open_script)

        cancel_button = QPushButton("Отменить бинд", self)
        cancel_button.clicked.connect(self.cancel_script)

        self.file_label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(create_button)
        layout.addWidget(open_button)
        layout.addWidget(cancel_button)
        layout.addWidget(self.file_label)
        self.setLayout(layout)

        self.button_text = button_text
        self.file_name = None

    def cancel_script(self):
        QMessageBox.information(self, "Внимание", "бинд с кнопки будет убран")
        self.file_name = None
        self.accept()
        self.file_label.setText(f"Выбран файл: {self.file_name}")

    def open_script(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбрать скрипт", "", "Text Files (*.txt)", options=options)
        if file_name:
            self.file_name = file_name
            self.accept()
            self.file_label.setText(f"Выбран файл: {self.file_name}")

    def create_script(self):
        QMessageBox.information(
            self,
            "Внимание",
            "Все комбинации клавиш, что вы нажмете ПОСЛЕ клика кнопки 'OK' будут записаны в скрипт,"
            " который будет использоваться для этой клавиши. для завершения написания комбинации клавиш нажмите f8"
        )
        listener = KeyboardListener()
        script_text = listener.write_script()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Создать скрипт", "script.txt", "Text Files (*.txt)",
                                                   options=options)
        if file_name:
            with open(file_name, 'w') as f:
                f.write(script_text)
        self.file_name = file_name
        self.accept()
        self.file_label.setText(f"Выбран файл: {self.file_name}")

    def get_file_name(self):
        return self.file_name


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
            ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["Caps Lock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "enter"],
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
        listener = KeyboardListener(buttons)
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
        print(f'script_address is {script_address}')
        button_text = self.sender().text()
        dialog = ScriptDialog(button_text, script_address)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            file_name = dialog.get_file_name()
            if file_name:
                self.sender().setStyleSheet('background-color: blue')
            else:
                self.sender().setStyleSheet('background-color: gray')
            self.sender().script_address = file_name

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


class KeyboardListener:
    def __init__(self, keyboard_mapping=None):
        self.button_comparison = {
            'esc': 'Key.esc', 'f1': 'Key.f1', 'f2': 'Key.f2', 'f3': 'Key.f3', 'f4': 'Key.f4', 'f5': 'Key.f5',
            'f6': 'Key.f6', 'f7': 'Key.f7', 'f8': 'Key.f8', 'f9': 'Key.f9', 'f10': 'Key.f10', 'f11': 'Key.f11',
            'f12': 'Key.f12', '`': '"`"', '1': '"1"', '2': '"2"', '3': '"3"', '4': '"4"', '5': '"5"', '6': '"6"',
            '7': '"7"', '8': '"8"', '9': '"9"', '0': '"0"', '-': '"-"', '=': '"="', 'backspace': 'Key.backspace',
            'Tab': 'Key.tab', 'Q': '"Q"', 'q': '"q"', 'W': '"W"', 'w': '"w"', 'E': '"E"', 'e': '"e"', 'R': '"R"',
            'r': '"r"', 'T': '"T"', 't': '"t"', 'Y': '"Y"', 'y': '"y"', 'U': '"U"', 'u': '"u"', 'I': '"I"', 'i': '"i"',
            'O': '"O"', 'o': '"o"', 'P': '"P"', 'p': '"p"', '[': '"["', ']': '"]"', '\\': '"\\"',
            'Caps Lock': 'Key.caps_lock', 'A': '"A"', 'a': '"a"', 'S': '"S"', 's': '"s"', 'D': '"D"', 'd': '"d"',
            'F': '"F"', 'f': '"f"', 'G': '"G"', 'g': '"g"', 'H': '"H"', 'h': '"h"', 'J': '"J"', 'j': '"j"', 'K': '"K"',
            'k': '"k"', 'L': '"L"', 'l': '"l"', ';': '";"', "'": "'", 'enter': 'Key.enter', 'shift': 'Key.shift',
            'Z': '"Z"', 'z': '"z"', 'X': '"X"', 'x': '"x"', 'C': '"C"', 'c': '"c"', 'V': '"V"', 'v': '"v"', 'B': '"B"',
            'b': '"b"', 'N': '"N"', 'n': '"n"', 'M': '"M"', 'm': '"m"', ',': '","', '.': '"."', '/': '"/"',
            'shift_r': 'Key.shift_r', 'ctrl_l': 'Key.ctrl_l', 'cmd': 'Key.cmd', 'alt_l': 'Key.alt_l',
            'space': 'Key.space', 'alt_gr': 'Key.alt_gr', 'cmd_r': 'Key.cmd_r', 'ctrl_r': 'Key.ctrl_r',
            '!': '"1"', '@': '"2"', '#': '"3"', '$': '"4"', '%': '"5"', '^': '"6"', '&': '"7"', '*': '"8"', '(': '"9"',
            ')': '"0"', '_': '"-"', '+': '"="',
        }
        self.keyboard_mapping = keyboard_mapping
        self.macros_mapping = {}
        self.keyboard = Controller()
        self.written_script = ''

    def execute_script(self, script):
        try:
            exec(script)
        except Exception as exc:
            pass
        yield

    def on_press(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        Process(target=self.execute_script(self.macros_mapping.get(char))).start()

    def on_release(self, key):
        return key != Key.f8

    def listen_keyboard(self):
        for item in self.keyboard_mapping:
            with open(f'{item.script_address}', 'r') as script:
                script_text = script.read()
            self.macros_mapping[item.text()] = script_text
            self.macros_mapping[item.text().lower()] = script_text

        with Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

    def write_press(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        command = f'self.keyboard.press({self.button_comparison.get(char)});'
        release_command = f'self.keyboard.press({self.button_comparison.get(char)});'
        if key != Key.f8 and command not in self.written_script \
                or self.written_script.count(command) <= self.written_script.count(release_command):
            self.written_script += f'self.keyboard.press({self.button_comparison.get(char)});'

    def write_release(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        if key != Key.f8:
            self.written_script += f'self.keyboard.release({self.button_comparison.get(char)});'
        return key != Key.f8

    def write_script(self):
        with Listener(
                on_press=self.write_press,
                on_release=self.write_release) as listener:
            listener.join()
        return self.written_script.replace('self.keyboard.release(Key.f8);', '')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
