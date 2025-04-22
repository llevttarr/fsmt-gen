'''
App window and GUI manager
'''

from PyQt5.QtWidgets import QOpenGLWidget, QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from OpenGL.GL import *
from OpenGL.GLU import *

from core.camera import Camera
from core.enums import WindowState
from render.world_manager import World
from ui.interactable import MenuToConfigButton


class MainMenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        start_button = MenuToConfigButton(main_window)
        layout.addWidget(start_button)
        self.setLayout(layout)

class GenerationViewWidget(QOpenGLWidget):
    def __init__(self, main_window, seed=1):
        super().__init__()
        self.main_window = main_window
        self.world = World(seed)
        self.camera = Camera()
    def initializeGL(self):
        glClearColor(0.4, 0.7, 1.0, 1.0) #temp color
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        self.camera.apply(w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.camera.apply(self.width(), self.height())

        for chunk in self.world.chunk_list:
            for block in chunk.blocks:
                self.draw_block(block)

    def draw_block(self, block):
        size = 2
        half = size / 2
        x, y, z = block.center_x, block.y, block.center_z

        vertices = [
            # bottom
            (x - half, 0, z - half),
            (x + half, 0, z - half),
            (x + half, 0, z + half),
            (x - half, 0, z + half),
            #up
            (x - half, y, z - half),
            (x + half, y, z - half),
            (x + half, y, z + half),
            (x - half, y, z + half),
        ]

        faces = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ]

        glColor3f(0.4, 0.8, 0.2) #temp color
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()

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
                self.widgets.setCurrentWidget(self.generator_view) #temp
            case WindowState.GENERATOR_CONFIG:
                pass
            case WindowState.GENERATOR_VIEW:
                pass
