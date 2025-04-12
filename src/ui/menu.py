'''
App window and GUI manager
'''

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QPushButton

from enum import Enum

class WindowState(Enum):
    '''
    Current state of the app window
    '''
    MAIN_MENU = 1
    # this state occurs right before the world generation
    GENERATOR_CONFIG = 2
    GENERATOR_VIEW = 3

#TODO
class MainMenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        self.setLayout(layout)

#TODO
class GenerationViewWidget(QOpenGLWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

#TODO
class GenerationConfigWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        self.setLayout(layout)

class Window(QMainWindow):
    '''
    App window object
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Generator")
        self.setGeometry(100, 100, 800, 600)
        self.widgets = QStackedWidget()
        self.setCentralWidget(self.widgets)

        self.window_state = WindowState.MAIN_MENU # the window will always start in main menu
        # initializing widgets
        self.main_menu = MainMenuWidget(self)
        self.widgets.addWidget(self.main_menu)
        self.widgets.setCurrentWidget(self.main_menu)

        self.generator_config = GenerationConfigWidget(self)
        self.widgets.addWidget(self.generator_config)
        self.generator_view = GenerationViewWidget(self)
        self.widgets.addWidget(self.generator_view)
    def switch_state(self):
        '''
        Changes the current window state
        '''
        match self.window_state:
            case WindowState.MAIN_MENU:
                pass
            case WindowState.GENERATOR_CONFIG:
                pass
            case WindowState.GENERATOR_VIEW:
                pass
