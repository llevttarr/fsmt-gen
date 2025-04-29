'''
App window and GUI manager
'''

from PyQt5.QtWidgets import QOpenGLWidget, QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor
from OpenGL.GL import *
from OpenGL.GLU import *

from core.camera import Camera
from core.enums import WindowState, CameraState
from core.matrix_util import Vector3D,Vector4D,Matrix3D,Matrix4D
from render.world_manager import World
from ui.interactable import MenuToConfigButton

import random as rand
import time
import os

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
        # glEnable(GL_CULL_FACE)
        # glFrontFace(GL_CCW)
        # glCullFace(GL_BACK)
        glEnable(GL_DEPTH_TEST)
        print('starting to generate world')
        try:
            self.world = World(self.seed,n_rings=4)
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
            self.world.perf_tick()
        except Exception as e:
            print('OpenGL render error: ',e)
    # Input events
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # ray casting to check for selection
            ray_origin=Vector3D(
                self.camera.pos[0],
                self.camera.pos[1],
                self.camera.pos[2],
            )
            x,y=self.normalize_mouse_pos(event.x(),event.y())
            print(f'normalized coords: {x}, {y}')
            ray_clip = Vector4D(x, y, -1.0, 1.0)
            inv_proj = self.camera.proj_matr(self.width(),self.height()).inverse()
            ray_eye = inv_proj @ ray_clip
            ray_eye = Vector4D(ray_eye[0], ray_eye[1], -1.0, 0.0)

            inv_view = self.camera.view_matr().inverse()
            ray_world = inv_view @ ray_eye
            ray_dir = Vector3D(ray_world[0], ray_world[1], ray_world[2]).normalize()
            self.world.select_block(ray_origin.data,ray_dir.data)
        if event.button() == Qt.RightButton:
            pass # 

    def mouseReleaseEvent(self, event):
        pass
    def resizeGL(self, w, h):
        self.camera.aspect_ratio = w / h
        self.camera.apply(w, h)
    def normalize_mouse_pos(self,x,y):
        w,h= self.width(), self.height()
        x=(2.0 * x) / w - 1.0
        y=1.0-(2.0*y)/h
        return -x,-y
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
    # # # # #
    def get_mouse_ray(self, x, y):
        pass

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
