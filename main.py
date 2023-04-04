import sys
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QGridLayout, QDialog, \
    QVBoxLayout, QFileDialog, QMessageBox
from pynput.keyboard import Key, Listener, Controller
from pynput.keyboard._win32 import KeyCode  # noqa
from multiprocessing import Process


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
            ["Caps Lock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
            ["L_shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "R_shift"],
            ["L_ctrl", "L_win", "L_alt", "Space", "R_alt", "R_win", "R_ctrl"]
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
            'esc': 'Key.esc',
            'f1': 'Key.f1',
            'f2': 'Key.f2',
            'f3': 'Key.f3',
            'f4': 'Key.f4',
            'f5': 'Key.f5',
            'f6': 'Key.f6',
            'f7': 'Key.f7',
            'f8': 'Key.f8',
            'f9': 'Key.f9',
            'f10': 'Key.f10',
            'f11': 'Key.f11',
            'f12': 'Key.f12',
            '`': '"`"',
            '1': '"1"',
            '2': '"2"',
            '3': '"3"',
            '4': '"4"',
            '5': '"5"',
            '6': '"6"',
            '7': '"7"',
            '8': '"8"',
            '9': '"9"',
            '0': '"0"',
            '-': '"-"',
            '=': '"="',
            'backspace': 'Key.backspace',
            'Tab': 'Key.tab',
            'Q': '"Q"',
            'q': '"q"',
            'W': '"W"',
            'w': '"w"',
            'E': '"E"',
            'e': '"e"',
            'R': '"R"',
            'r': '"r"',
            'T': '"T"',
            't': '"t"',
            'Y': '"Y"',
            'y': '"y"',
            'U': '"U"',
            'u': '"u"',
            'I': '"I"',
            'i': '"i"',
            'O': '"O"',
            'o': '"o"',
            'P': '"P"',
            'p': '"p"',
            '[': '"["',
            ']': '"]"',
            '\\': '"\\"',
            'Caps Lock': 'Key.caps_lock',
            'A': '"A"',
            'a': '"a"',
            'S': '"S"',
            's': '"s"',
            'D': '"D"',
            'd': '"d"',
            'F': '"F"',
            'f': '"f"',
            'G': '"G"',
            'g': '"g"',
            'H': '"H"',
            'h': '"h"',
            'J': '"J"',
            'j': '"j"',
            'K': '"K"',
            'k': '"k"',
            'L': '"L"',
            'l': '"l"',
            ';': '";"',
            "'": "'",
            'Enter': 'Key.enter',
            'enter': 'Key.enter',
            'L_shift': 'Key.shift',
            'shift': 'Key.shift',
            'Z': '"Z"',
            'z': '"z"',
            'X': '"X"',
            'x': '"x"',
            'C': '"C"',
            'c': '"c"',
            'V': '"V"',
            'v': '"v"',
            'B': '"B"',
            'b': '"b"',
            'N': '"N"',
            'n': '"n"',
            'M': '"M"',
            'm': '"m"',
            ',': '","',
            '.': '"."',
            '/': '"/"',
            'R_shift': 'Key.shift_r',
            'shift_r': 'Key.shift_r',
            'L_ctrl': 'Key.ctrl_l',
            'ctrl_l': 'Key.ctrl_l',
            'L_win': 'Key.cmd',
            'cmd': 'Key.cmd',
            'L_alt': 'Key.alt_l',
            'alt_l': 'Key.alt_l',
            'Space': 'Key.space',
            'space': 'Key.space',
            'R_alt': 'Key.alt_gr',
            'alt_gr': 'Key.alt_gr',
            'R_win': 'Key.cmd_r',
            'R_ctrl': 'Key.ctrl_r',
            'ctrl_r': 'Key.ctrl_r',
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
        self.written_script += f'self.keyboard.press({self.button_comparison.get(char)});'

    def write_release(self, key):
        if isinstance(key, Key):
            char = key._name_
        elif isinstance(key, KeyCode):
            char = key.char
        else:
            char = key
        self.written_script += f'self.keyboard.release({self.button_comparison.get(char)});'
        return key != Key.f8

    def write_script(self):
        with Listener(
                on_press=self.write_press,
                on_release=self.write_release) as listener:
            listener.join()
        return self.written_script.replace('self.keyboard.release(Key.f8);','')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
