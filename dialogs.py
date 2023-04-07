from PySide6.QtWidgets import QLabel, QPushButton, QDialog, QVBoxLayout, QComboBox, QMessageBox, QInputDialog
from keyboard import KeyboardListener
import pickle


class ScriptDialog(QDialog):

    def __init__(self, button_text, fernet, parent=None):
        super().__init__(parent)
        self.fernet = fernet
        self.setWindowTitle(f'Скрипт для {button_text}')
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
        self.script = None

    def cancel_script(self):
        QMessageBox.information(self, "Внимание", "бинд с кнопки будет убран")
        self.script = None
        self.accept()
        self.file_label.setText(f"Выбран скрипт: {self.script}")

    def open_script(self):
        data = self.read_config()
        scripts = data.get('scripts', {})
        if scripts:
            item, ok = QInputDialog.getItem(self, 'Выберите скрипт', 'Выберите скрипт из списка:', scripts.keys(), 0, False)
            if ok and item:
                self.script = scripts.get(item)
                self.accept()
                self.file_label.setText(f"Выбран скрипт: {self.script}")
        else:
            QMessageBox.information(
                self,
                "Внимание",
                "Вы еще не писали скриптов, чтобы их использовать"
            )

    def create_script(self):
        QMessageBox.information(
            self,
            "Внимание",
            "Все комбинации клавиш, что вы нажмете ПОСЛЕ клика кнопки 'OK' будут записаны в скрипт,"
            " который будет использоваться для этой клавиши. для завершения написания комбинации клавиш нажмите f8"
        )
        listener = KeyboardListener(binding_key=self.button_text)
        script_text = listener.write_script()

        insert, _ = QInputDialog.getText(self, 'Cохранение скрипта', 'Введите название:')

        data = self.read_config()
        scripts = data.get('scripts', {})
        if scripts:
            scripts.update({insert: script_text})
        else:
            scripts = {insert: script_text}

        data['scripts'] = scripts
        self.write_config(data)

        self.script = script_text
        self.accept()
        self.file_label.setText(f"Выбран скрипт: {self.script}")

    def get_script(self):
        return self.script

    def read_config(self):
        with open('config.pkl', 'rb') as f:
            data = pickle.load(f)
            return data

    def write_config(self, data):
        with open('config.pkl', 'wb') as f:
            pickle.dump(data, f)
