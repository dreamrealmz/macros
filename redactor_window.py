from PySide6.QtWidgets import QApplication, QMainWindow, QListWidget, QTextEdit, QDockWidget, QListWidgetItem, \
    QPushButton, QInputDialog, QWidget, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt

from base_window import BaseWindow
from keyboard import KeyboardListener


class RedactorWindow(BaseWindow):
    def __init__(self, parent, button, data):
        super().__init__(parent)
        self.button = button
        self.data_dict = data
        self.setFixedSize(800, 400)
        self.setWindowTitle("Редактор скриптов")
        self.list_widget = None
        self.dock_widget = None
        self.buttons_dock_widget = None
        self.text_edit = None
        self.render_window()
        self.chosen_key = None

    def show_value(self):
        sender = self.sender()
        self.chosen_key = sender
        text = self.get_text_transcription(sender.script_text)
        self.text_edit.setText(text)
        self.text_edit.setReadOnly(True)
        self.dock_widget.show()
        self.buttons_dock_widget.show()

    def add_item(self):
        key, ok = QInputDialog.getText(self, "Добавление нового скрипта", "Введите название:")
        if key and ok:
            self.data_dict[key] = ''
            item = QListWidgetItem(key)
            self.list_widget.addItem(item)
            data = self.read_scripts()
            data['scripts'].update({key: ''})
            self.write_scripts(data)
            self.dock_widget.close()
            self.buttons_dock_widget.close()
            self.render_window()

    def render_window(self):
        self.list_widget = QListWidget(self)
        self.list_widget.setFixedSize(200, 400)

        if self.data_dict:
            for key, value in self.data_dict.items():
                button_item = QListWidgetItem(self.list_widget)
                button_widget = QPushButton(key)
                button_widget.script_text = value
                button_item.setSizeHint(button_widget.sizeHint())
                self.list_widget.setItemWidget(button_item, button_widget)
                button_widget.clicked.connect(self.show_value)

        self.dock_widget = QDockWidget(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.dock_widget.setWidget(self.text_edit)

        self.setCentralWidget(self.list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        self.dock_widget.setAllowedAreas(self.dock_widget.allowedAreas() | Qt.RightDockWidgetArea)
        self.dock_widget.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable
        )
        self.dock_widget.hide()

        button_item = QListWidgetItem(self.list_widget)
        add_button = QPushButton("+")
        self.list_widget.setItemWidget(button_item, add_button)
        add_button.clicked.connect(self.add_item)

        self.buttons_dock_widget = QDockWidget(self)
        buttons_widget = QWidget()
        change_script = QPushButton("Изменить")
        change_script.clicked.connect(self.change_script)
        accept_script = QPushButton("Применить")
        accept_script.clicked.connect(self.accept_script)
        cancel_script = QPushButton("Снять")
        cancel_script.clicked.connect(self.cancel_script)
        delete_script = QPushButton("Удалить")
        delete_script.clicked.connect(self.delete_script)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(change_script)
        buttons_layout.addWidget(accept_script)
        buttons_layout.addWidget(cancel_script)
        buttons_layout.addWidget(delete_script)
        buttons_widget.setLayout(buttons_layout)

        self.buttons_dock_widget.setWidget(buttons_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.buttons_dock_widget)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        self.buttons_dock_widget.hide()

    def get_text_transcription(self, text):
        return '\n'.join(
            i.replace(
                'self.keyboard.press', 'нажать'
            ).replace(
                'self.keyboard.release', 'отпустить'
            ).replace('time.sleep', 'ожидать')
            for i in text.split(';')
        )

    def change_script(self):
        sender = self.chosen_key
        QMessageBox.information(
            self,
            "Внимание",
            "Все комбинации клавиш, что вы нажмете ПОСЛЕ клика кнопки 'OK' будут записаны в скрипт,"
            " который будет использоваться для этой клавиши. для завершения написания комбинации клавиш нажмите f8"
        )
        listener = KeyboardListener(binding_key=self.button.text())
        script_text = listener.write_script()

        data = self.read_scripts()
        scripts = data.get('scripts', {})
        if scripts:
            scripts.update({sender.text(): script_text})
        else:
            scripts = {sender.text(): script_text}

        data['scripts'] = scripts
        self.write_scripts(data)
        self.data_dict = data['scripts']
        self.dock_widget.close()
        self.buttons_dock_widget.close()
        self.render_window()

    def accept_script(self):
        sender = self.chosen_key
        self.parent().set_button_script(button=self.button, script=sender.script_text)

    def delete_script(self):
        sender = self.chosen_key
        data = self.read_scripts()

        data['scripts'].pop(sender.text())
        self.write_scripts(data)
        self.parent().set_button_script(button=self.button, script=None)
        self.data_dict = data['scripts']
        self.dock_widget.close()
        self.buttons_dock_widget.close()
        self.render_window()

    def cancel_script(self):
        self.parent().set_button_script(button=self.button, script=None)
