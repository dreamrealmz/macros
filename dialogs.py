from PySide6.QtWidgets import QLabel, QPushButton, QDialog, QVBoxLayout, QFileDialog, QMessageBox
from keyboard import KeyboardListener


class ScriptDialog(QDialog):

    def __init__(self, button_text, script_address, fernet, parent=None):
        super().__init__(parent)
        self.fernet = fernet
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
        listener = KeyboardListener(binding_key=self.button_text)
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
