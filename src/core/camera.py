from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtCore import Qt, QTimer, QPoint
from core.enums import CameraState
import math
import time
class Camera:
    def __init__(self, fps = 60):
        self.pos = [25, 25, 25]
        self.yaw,self.pitch = 0.1,0.1
        self.fov = CameraState.DEFAULT.value
        self.state = CameraState.DEFAULT
        self.speed=0.05
        self.fps = fps
        self.sensitivity=0.1
        self.active_keys={}
        self.key_press_time={}
        self.last_moved = time.time()
        self.move_ticks = 0
    def toggle_mode(self, state):
        if self.state == state:
            self.state = CameraState.DEFAULT
        else:
            self.state = state
    def get_dir(self):
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        # spherical coords
        dx = math.cos(pitch_rad) * math.sin(yaw_rad)
        dy = math.sin(pitch_rad)
        dz = -math.cos(pitch_rad) * math.cos(yaw_rad)
        return [dx, dy, dz]
    def set_key(self, key, is_pressed):
        self.active_keys[key] = is_pressed
        if is_pressed:
            self.key_press_time[key] = time.time()
    def apply(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width / height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        dir = self.get_dir()
        target = [self.pos[i] + dir[i] for i in range(3)]
        gluLookAt(*self.pos, *target, 0, 1, 0)

    def move(self):
        dir_matr=[0,0,0]
        # up/down
        up_matr=[0,1,0]
        # forwards/backwards
        frw_matr=self.get_dir()
        # right/left
        rgt_matr=[-math.sin(math.radians(self.yaw)-math.pi/2),0,math.cos(math.radians(self.yaw)-math.pi/2)]

        # if a few keys are pressed, some cancel out
        # forwards
        if Qt.Key_W in self.active_keys and self.active_keys[Qt.Key_W]:
            dir_matr=[dir_matr[i]+frw_matr[i] for i in range(3)]
        # backwards
        if Qt.Key_S in self.active_keys and self.active_keys[Qt.Key_S]:
            dir_matr=[dir_matr[i]-frw_matr[i] for i in range(3)]
        # right
        if Qt.Key_D in self.active_keys and self.active_keys[Qt.Key_D]:
            dir_matr=[dir_matr[i]+rgt_matr[i] for i in range(3)]
        # left
        if Qt.Key_A in self.active_keys and self.active_keys[Qt.Key_A]:
            dir_matr=[dir_matr[i]-rgt_matr[i] for i in range(3)]
        # up
        if Qt.Key_Space in self.active_keys and self.active_keys[Qt.Key_Space]:
            dir_matr=[dir_matr[i]+up_matr[i] for i in range(3)]
        # down
        if Qt.Key_Shift in self.active_keys and self.active_keys[Qt.Key_Shift]:
            dir_matr=[dir_matr[i]-up_matr[i] for i in range(3)]
        # Acceleration function
        # FIXME - could be improved
        t = time.time()-self.last_moved
        if t > 2:
            self.move_ticks = 0
            self.last_moved = time.time()
        elif t>=1:
            self.move_ticks+=1
            if self.move_ticks>30:
                self.move_ticks=30
            self.last_moved = time.time()
        speed = 0.01+(0.01*pow(self.move_ticks,2))
        if speed > 0.5: # speed cap
            speed = 0.5
        self.pos=[self.pos[i]+(dir_matr[i]*speed) for i in range(3)]

    def rotate(self, dx, dy):
        self.yaw+=dx*self.sensitivity
        self.pitch+=dy*self.sensitivity
        self.pitch=max(-89.9, min(89.9, self.pitch))

    def zoom(self):
        target_fov = self.state.value
        diff = target_fov-self.fov
        if abs(diff)>0.05:
            self.fov += diff * 0.05
