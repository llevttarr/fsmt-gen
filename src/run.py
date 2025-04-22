from PyQt5.QtWidgets import QApplication
import ui.menu
import sys

def app_run():
    app = QApplication(sys.argv)
    window = ui.menu.Window()
    window.show()
    sys.exit(app.exec_())
