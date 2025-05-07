'''
App window and GUI manager
'''
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QPixmap
from OpenGL.GL import *
from OpenGL.GLU import *

from core.camera import Camera
from core.enums import WindowState, CameraState
from core.matrix_util import Vector3D,Vector4D,Matrix3D,Matrix4D
from core.region_gen import init_regions
from core.object_gen import init_objects
from core.terrain_gen import init_heights
from render.shader import Shader
from render.world_manager import World
from ui.interactable import MenuToConfigButton, Button, InteractableSlider

import random
import time
import os
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSplitter

class MainMenuWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

        self.title_label = QLabel("Terrain Generator")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            font-family: 'Courier New';
        """)

        self.image_label = QLabel(self)
        pixmap = QPixmap(
            os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            "..","..",
                            "static","assets","logo_fill_transparent.png"
                        )
            )
            )
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 400)

        self.start_button = MenuToConfigButton(main_window)
        self.start_button.setFixedSize(400, 50)
        self.start_button.setCursor(Qt.PointingHandCursor) 
        self.start_button.setStyleSheet("""
            font-size: 16px;
            padding: 10px;
        """)

        self.layout.addWidget(self.title_label)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.image_label)
        self.layout.addSpacing(30)
        self.layout.addWidget(self.start_button)


class GenerationViewWidget(QOpenGLWidget):
    gen_complete_signal = pyqtSignal(
        bool
    )
    def __init__(self, main_window, seed=1, fps=144):
        super().__init__()
        self.main_window = main_window
        self.camera = Camera()
        self.seed = seed

        # mouse cursor management
        self.setMouseTracking(False)
        self.mouse_locked = False
        self.last_mouse_pos = QCursor.pos()
        self.last_time = time.time()
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.log_fps)
        self.fps_timer.start(1000)
        self.frame_count=0

        self.shader = None


        apply_styles(self)

    def log_fps(self):
        current_time = time.time()
        elapsed = current_time - self.last_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        print(f"fps: {fps:.2f}")
        self.frame_count = 0
        self.last_time = current_time
    
    def trigger_generation(self,seed=1,obj_intensity=0.05,rings=6,generation_rate=5,height_intensity=0.3):
        self.world = None
        self.seed=seed
        print('generation triggered')
        
        rg_info=init_regions(seed,rings)
        y_info=init_heights(seed,rings,height_intensity,rg_info)
        obj_info=init_objects(seed,rings,obj_intensity,rg_info,y_info)

        self.world = World(
            y_info,rg_info,obj_info,seed,self.shader,n_rings=rings,obj_intensity=obj_intensity,height_intensity=height_intensity,generation_rate=generation_rate
        )
        self.world.generate_mesh()

        self.gen_complete_signal.emit(False) # false enables widget, true disables it

    def initializeGL(self):
        glClearColor(0.4, 0.7, 1.0, 1.0) #temp color
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glFrontFace(GL_CCW)
        glCullFace(GL_BACK)
        glEnable(GL_DEPTH_TEST)
        print('starting to generate world')
        try:
            self.shader = Shader(
                            os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            "..", 
                            "shaders","world_v.vert"
                        )
                        ),
                            os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            "..", 
                            "shaders","world_f.frag"
                        )
                        ))
            self.shader.use()
            self.shader.set_mat4('projection',self.camera.proj_matr(self.width(),self.height()))
            self.shader.set_mat4('view',self.camera.view_matr())
            self.shader.set_float('time',time.perf_counter())
        except Exception as e:
            print('shader init went wrong: ',e)
        try:
            self.trigger_generation()
        except Exception as e:
            print('world generation went wrong: ',e)
    # def resizeGL(self, w, h):
        # self.camera.apply(w, h)

    def paintGL(self):
        self.frame_count+=1
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # glLoadIdentity()
        # self.camera.apply(self.width(), self.height())
        try:
            self.shader.use()
            self.shader.set_mat4('projection',self.camera.proj_matr(self.width(),self.height()))
            self.shader.set_mat4('view',self.camera.view_matr())
            self.world.render()
            self.world.perf_tick()
        except Exception as e:
            print('OpenGL render error: ',e)
    # Input events
    def mousePressEvent(self, event):
        if self.mouse_locked:
            return
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
            self.setMouseTracking(True)
            self.mouse_locked = True
            self.setCursor(Qt.BlankCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setMouseTracking(False)
            self.mouse_locked = False
            self.setCursor(Qt.ArrowCursor)
    def resizeGL(self, w, h):
        self.camera.aspect_ratio = w / h
        # self.camera.apply(w, h)
    def normalize_mouse_pos(self,x,y):
        w,h= self.width(), self.height()
        x=(2.0 * x) / w - 1.0
        y=1.0-(2.0*y)/h
        return x,y
    def mouseMoveEvent(self, event):
        if not self.mouse_locked:
            return
        center = self.mapToGlobal(self.rect().center())
        dx = event.globalX() - center.x()
        dy = event.globalY() - center.y()
        self.camera.rotate(dx, -dy)
        QCursor.setPos(center)

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

class GenerationSidebar(QWidget):
    gen_signal = pyqtSignal(
        int,float,int,int,float
    )

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.title = QLabel("Terrain Generator", )
        self.title.setStyleSheet("font-size: 20px; font-family: Courier New; font-weight: bold;")


        self.input_field = QLabel("Enter Seed:")
        self.seed_input = QLineEdit()
        self.generate_button = Button("Generate", self.generate_action)
        self.generate_button.setCursor(Qt.PointingHandCursor) 
        self.parameters_widget = QWidget()
        self.parameters_layout = QVBoxLayout(self.parameters_widget)

        self.generate_widget = QWidget()
        self.seed_generate = QVBoxLayout(self.generate_widget)

        self.obj_intensity = InteractableSlider(self, "Object Intensity", (0, 15), "decimal")
        self.rings = InteractableSlider(self, "Rings", (1, 10))
        self.generation_rate = InteractableSlider(self, "Generation Rate", (1, 10))
        self.height_intensity = InteractableSlider(self, "Height Intensity", (0, 100), "decimal")

        self.parameters_layout.addWidget(self.obj_intensity)
        self.parameters_layout.addWidget(self.rings)
        self.parameters_layout.addWidget(self.generation_rate)
        self.parameters_layout.addWidget(self.height_intensity)
        self.parameters_layout.setAlignment(Qt.AlignCenter)
        self.seed_generate.addWidget(self.input_field)
        self.seed_generate.addWidget(self.seed_input)
        self.seed_generate.addWidget(self.generate_button)

        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(self.parameters_widget)
        self.main_layout.addWidget(self.generate_widget)


        #cosmetichka
        apply_styles(self)
    def set_generating(self,flag):
        self.generate_button.setEnabled(not flag)
    def generate_action(self):
        try:
            seed_inp = self.seed_input.text()
            seed = int(seed_inp) if seed_inp else 1
            obj_intensity = float(self.obj_intensity.display.toPlainText())
            rings = int(self.rings.display.toPlainText())
            generation_rate = int(self.generation_rate.display.toPlainText())
            height_intensity = float(self.height_intensity.display.toPlainText())
            self.set_generating(True)
            self.gen_signal.emit(
                seed,obj_intensity,rings,generation_rate,height_intensity
            )
            print(f"generation started;\nseed: {seed}\nsize:{3^rings}\no_i:{obj_intensity}\ng_r:{generation_rate}\nh_i:{height_intensity}")
        except ValueError:
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle("Incorrect Seed")
            msg_box.setText("The Seed Must Contain Only Numbers")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.exec_()
            print("Invalid seed value.")

class MainInterface(QWidget):
    def __init__(self, main_window, fps=144):
        super().__init__()
        self.main_window = main_window
        self.main_layout = QVBoxLayout(self)
        self.sidebar = GenerationSidebar(self)
        self.generator_view = GenerationViewWidget(self)

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Horizontal)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.generator_view)
        self.splitter.setSizes([300, 1100])

        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_w)
        self.timer.start(1000//fps)

        self.sidebar.gen_signal.connect(self.generator_view.trigger_generation)
        self.generator_view.gen_complete_signal.connect(self.sidebar.set_generating)

    def update_w(self):
        if Qt.Key_C in self.generator_view.camera.active_keys:
            # FIXME - after you zoom in once, this function gets called indefinitely
            self.generator_view.camera.zoom()
        if self.generator_view.camera.state==CameraState.DEFAULT:
            self.generator_view.camera.move()
        self.generator_view.update()

   
    def keyPressEvent(self, event):
        self.generator_view.camera.set_key(event.key(), True)
        match event.key():
            # case Qt.Key_Escape:
            #     self.generator_view.mouse_locked = not self.generator_view.mouse_locked
            #     self.setCursor(Qt.BlankCursor if self.generator_view.mouse_locked else Qt.ArrowCursor)
            #     self.generator_view.setCursor(Qt.BlankCursor if self.generator_view.mouse_locked else Qt.ArrowCursor)
            #     if self.generator_view.mouse_locked:
            #         QCursor.setPos(self.mapToGlobal(self.rect().center()))
            case Qt.Key_C:
                self.generator_view.camera.state = CameraState.ZOOM
            case _:
                return
    
    def keyReleaseEvent(self, event):
        self.generator_view.camera.set_key(event.key(), False)
        if event.key()==Qt.Key_C:
            self.generator_view.camera.state = CameraState.DEFAULT

  
class Window(QMainWindow):
    '''
    App window object
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Generator")
        self.setGeometry(100, 100, 1400, 860)
        self.setWindowIcon(QIcon(
            os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            "..","..",
                            "static","logo.png"
                        )
            ))
            )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        self.widgets = QStackedWidget()
        self.main_menu = MainMenuWidget(self)
        self.main_interface = MainInterface(self)

        self.widgets.addWidget(self.main_interface)
        self.widgets.addWidget(self.main_menu)
        self.widgets.setCurrentWidget(self.main_menu)

        self.main_layout.addWidget(self.widgets)
        self.window_state = WindowState.MAIN_MENU

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        apply_styles(self)


    def switch_state(self):
        '''
        Changes the current window state
        '''
        match self.window_state:
            case WindowState.MAIN_MENU:
                self.widgets.setCurrentWidget(self.main_interface)  # temp
            case WindowState.GENERATOR_CONFIG:
                pass
            case WindowState.GENERATOR_VIEW:
                pass

def apply_styles(self):
    self.setStyleSheet("""
        QWidget {
            background-color: #181820;
            color: #f0f0f0;
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
            font-size: 13px;
        }

        QLabel {
            font-weight: bold;
            margin-bottom: 4px;
        }

        QLineEdit {
            padding: 6px 8px;
            border: 1px solid #3a3a4f;
            border-radius: 6px;
            background-color: #2a2a3d;
            color: #f0f0f0;
        }

        QLineEdit:focus {
            border: 1px solid #F39237;
            background-color: #2f2f4a;
        }

        QPushButton {
            background-color: #F39237;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
            color: white;
        }

        QPushButton:hover {
            background-color: #E5AE62;
        }

        QPushButton:pressed {
            background-color: #E68339;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background: #3a3a4f;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background: #F39237;
            border: 1px solid #2f2f4a;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 3px;
        }

        QSlider::sub-page:horizontal {
            background: #F39237;
            border-radius: 3px;
        }

        QSlider::add-page:horizontal {
            background: #2a2a3d;
            border-radius: 3px;
        }
    """)
