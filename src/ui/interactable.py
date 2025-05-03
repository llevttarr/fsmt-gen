from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QPushButton, QSlider
from PyQt5.QtCore import Qt

class Button(QPushButton):
    def __init__(self, text, callback):
        super().__init__(text=text)
        self.clicked.connect(callback)

class MenuToConfigButton(Button):
    def __init__(self, main_window):
        super().__init__("Start", main_window.switch_state)

class ConfigToViewButton(Button):
    def __init__(self, main_window):
        super().__init__("Change to View", main_window.switch_state)

class ObjIntensitySlider(QSlider):
    def __init__(self, min_max_values: tuple[int]):
        super().__init__(orientation=Qt.Horizontal)
        self.setMaximum(min_max_values[1])
        self.setMinimum(min_max_values[0])

class InteractableSlider(QWidget):
    """
    display types:
    decimal, 
    percentage, 
    decimal-percentage, 
    none (default)
    """
    def __init__(self, main_window, label: str, min_max_values: tuple[int], display_type=None):
        super().__init__()
        self.setFixedSize(150, 110)  # Set a fixed size for better rendering
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.display_type = display_type

        self.label = QLabel(label)

        self.slider = ObjIntensitySlider(min_max_values)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.setFixedWidth(self.width() - 50)
        self.slider.setCursor(Qt.PointingHandCursor) 

        self.display = QTextBrowser()
        self.display.setText(str(min_max_values[0]))
        self.display.setReadOnly(True)
        self.display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.display.setFixedSize(100, 20)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.display)
        self.layout.addWidget(self.slider)


    def slider_changed(self, value):
        c = 1 if self.display_type not in  {"decimal", "decimal-percentage"} else 0.01
        res = str(round(value * c, 2)) + "%" if self.display_type in {"decimal-percentage", "percentage"} else str(round(value * c, 2))
        self.display.setText(res)



    def handlechange(self, value):
        print(value)
