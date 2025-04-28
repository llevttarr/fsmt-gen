'''
App window and GUI manager
'''
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor
from OpenGL.GL import *
from OpenGL.GLU import *

from core.camera import Camera
from core.enums import WindowState, CameraState
from render.world_manager import World
from ui.interactable import MenuToConfigButton, Button, InteractableSlider, ObjIntensitySlider


import random as rand
import time
import os
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSplitter

class MainMenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        start_button = MenuToConfigButton(main_window)
        layout.addWidget(start_button)
        self.setLayout(layout)

class GenerationViewWidget(QOpenGLWidget):
    def __init__(self, main_window, seed=1, fps=144):
        super().__init__()
        self.main_window = main_window
        self.camera = Camera()
        self.seed = seed

        # mouse cursor management
        self.setMouseTracking(True)
        self.mouse_locked = True
        self.last_mouse_pos = QCursor.pos()
        self.last_time = time.time()
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.log_fps)
        self.fps_timer.start(1000)
        self.frame_count=0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_w)
        self.timer.start(1000//fps)

    def log_fps(self):
        current_time = time.time()
        elapsed = current_time - self.last_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        print(f"fps: {fps:.2f}")
        self.frame_count = 0
        self.last_time = current_time
        
    def update_w(self):
        if Qt.Key_C in self.camera.active_keys:
            # FIXME - after you zoom in once, this function gets called indefinitely
            self.camera.zoom()
        if self.camera.state==CameraState.DEFAULT:
            self.camera.move()
        self.update()

    def initializeGL(self):
        glClearColor(0.4, 0.7, 1.0, 1.0) #temp color
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glCullFace(GL_FRONT)
        glEnable(GL_DEPTH_TEST)
        print('starting to generate world')
        try:
            self.world = World(self.seed,4)
            self.world.generate_mesh()
        except Exception as e:
            print('world generation went wrong: ',e)


    def resizeGL(self, w, h):
        self.camera.apply(w, h)

    def paintGL(self):
        self.frame_count+=1
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.camera.apply(self.width(), self.height())
        try:
            self.world.render()
        except Exception as e:
            print('OpenGL render error: ',e)

    # Input events
    def mousePressEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        if not self.mouse_locked:
            return
        center = self.mapToGlobal(self.rect().center())
        dx = event.globalX() - center.x()
        dy = event.globalY() - center.y()
        self.camera.rotate(dx, -dy)
        QCursor.setPos(center)

    def keyPressEvent(self, event):
        self.camera.set_key(event.key(), True)
        match event.key():
            case Qt.Key_Escape:
                self.mouse_locked = not self.mouse_locked
                self.setCursor(Qt.BlankCursor if self.mouse_locked else Qt.ArrowCursor)
                if self.mouse_locked:
                    QCursor.setPos(self.mapToGlobal(self.rect().center()))
            case Qt.Key_C:
                self.camera.state = CameraState.ZOOM
            case _:
                return

    def keyReleaseEvent(self, event):
        self.camera.set_key(event.key(), False)
        if event.key()==Qt.Key_C:
            self.camera.state = CameraState.DEFAULT

    def showEvent(self, event):
        if self.mouse_locked:
            self.setCursor(Qt.BlankCursor)
            QCursor.setPos(self.mapToGlobal(self.rect().center()))

class GenerationConfigWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        self.setLayout(layout)

class GenerationSidebar(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.setMaximumHeight(200)
        self.main_window = main_window
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.input_field = QLabel("Enter Seed:")
        self.seed_input = QLineEdit()
        self.generate_button = Button("Generate", self.generate_action)

        self.parameters_widget = QWidget()
        self.parameters_layout = QHBoxLayout(self.parameters_widget)
        
        self.generate_widget = QWidget()
        self.seed_generate = QVBoxLayout(self.generate_widget)
        self.generate_widget.setFixedWidth(220)

        self.obj_intensity = InteractableSlider(self, "Object Intensity", (0, 100), "decimal")
        self.rings = InteractableSlider(self, "Rings", (1, 10))
        self.generation_rate = InteractableSlider(self, "Generation Rate", (1, 10))
        self.height_intensity = InteractableSlider(self, "Height Intensity", (0, 100), "decimal")

        self.parameters_layout.addWidget(self.obj_intensity)
        self.parameters_layout.addWidget(self.rings)
        self.parameters_layout.addWidget(self.generation_rate)
        self.parameters_layout.addWidget(self.height_intensity)

        self.seed_generate.addWidget(self.input_field)
        self.seed_generate.addWidget(self.seed_input)
        self.seed_generate.addWidget(self.generate_button)


        self.main_layout.addWidget(self.generate_widget)
        self.main_layout.addWidget(self.parameters_widget)

    def generate_action(self):
        try:
            seed = self.seed_input.text()
            if seed:
                print(f"generated {int(seed)}")
            else:
                values = [
                    self.obj_intensity.display.toPlainText(),
                    self.rings.display.toPlainText(),
                    self.generation_rate.display.toPlainText(),
                    self.height_intensity.display.toPlainText()
                ]
                print(values)
        except ValueError:
            print("Invalid seed value.")


class Window(QMainWindow):
    '''
    App window object
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Generator")
        self.setGeometry(100, 100, 1000, 760)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        self.widgets = QStackedWidget()
        self.main_menu = MainMenuWidget(self)
        self.generator_config = GenerationConfigWidget(self)
        self.generator_view = GenerationViewWidget(self)

        self.widgets.addWidget(self.main_menu)
        self.widgets.addWidget(self.generator_config)
        self.widgets.addWidget(self.generator_view)
        self.widgets.setCurrentWidget(self.main_menu)
        self.sidebar = GenerationSidebar(self)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setSizes([560, 200])
        self.main_layout.addWidget(self.splitter)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.widgets)

        self.window_state = WindowState.MAIN_MENU


    def switch_state(self):
        '''
        Changes the current window state
        '''
        match self.window_state:
            case WindowState.MAIN_MENU:
                self.widgets.setCurrentWidget(self.generator_view)  # temp
            case WindowState.GENERATOR_CONFIG:
                pass
            case WindowState.GENERATOR_VIEW:
                pass
