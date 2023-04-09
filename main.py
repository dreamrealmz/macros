import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        app.exec()
        sys.exit()
    except Exception as error:
        print(error)
        s = input('send your error text to ad.azarov17k@gmail.com')


