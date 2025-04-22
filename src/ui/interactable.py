from PyQt5.QtWidgets import QPushButton

class Button(QPushButton):
    def __init__(self, callback):
        super().__init__()
        self.clicked.connect(callback)

class MenuToConfigButton(Button):
    def __init__(self, main_window):
        super().__init__(main_window.switch_state)

class ConfigToViewButton(Button):
    def __init__(self, main_window):
        super().__init__(main_window.switch_state)
