from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtCore import Qt, QTimer, QPoint

from core.enums import CameraState
from core.matrix_util import Matrix3D, Matrix4D, Vector3D, Vector4D

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
        # self.aspect_ratio = 1.0
        self.near_plane = 0.1
        self.far_plane = 1000.0
    @property
    def right_vec(self):
        return Vector3D(
            math.sin(math.radians(self.yaw-90)),
            0,
            -math.cos(math.radians(self.yaw-90))
        )
    @property
    def up_vec(self):
        dir_vec = self.get_dir()
        right = self.right_vec
        cross = Vector3D(
            right[1] * dir_vec[2] - right[2] * dir_vec[1],
            right[2] * dir_vec[0] - right[0] * dir_vec[2],
            right[0] * dir_vec[1] - right[1] * dir_vec[0]
        )
        
        length = cross.length
        if length <= 0:
            return Vector3D(0, 1, 0)
        
        return cross.normalize()
    def proj_matr(self, width, height):
        # FIXME: flip_y is not a good solution
        aspect = width / height
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2)
        return Matrix4D(
            f / aspect, 0, 0, 0,
            0, -f, 0, 0,
            0, 0, (self.far_plane + self.near_plane) / (self.near_plane - self.far_plane), (2 * self.far_plane * self.near_plane) / (self.near_plane - self.far_plane),
            0, 0, -1.0, 0
        )
    
    def view_matr(self):
        dir,right,up=self.get_dir(),self.right_vec,self.up_vec
        rotate_matr=Matrix4D(
            right[0], right[1], right[2],0,
            up[0], up[1], up[2],0,
            -dir[0], -dir[1], -dir[2],0,
            0,0,0,1
        )
        translate_matr=Matrix4D(
            1,0,0,-self.pos[0],
            0,1,0,-self.pos[1],
            0,0,1,-self.pos[2],
            0,0,0,1
        )
        return rotate_matr @ translate_matr
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
        '''
        DEPRECATED
        '''
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
        up_vec=Vector3D(0,1,0)
        # forwards/backwards
        frw_vec=self.get_dir()
        # right/left
        rgt_vec=self.right_vec

        # if a few keys are pressed, some cancel out
        # forwards
        if 87 in self.active_keys and self.active_keys[87]:
            dir_matr=[dir_matr[i]+frw_vec[i] for i in range(3)]
        # backwards
        if 83 in self.active_keys and self.active_keys[83]:
            dir_matr=[dir_matr[i]-frw_vec[i] for i in range(3)]
        # right
        if 68 in self.active_keys and self.active_keys[68]:
            dir_matr=[dir_matr[i]+rgt_vec[i] for i in range(3)]
        # left
        if 65 in self.active_keys and self.active_keys[65]:
            dir_matr=[dir_matr[i]-rgt_vec[i] for i in range(3)]
        # up
        if 17 in self.active_keys and self.active_keys[17]:
            dir_matr=[dir_matr[i]+up_vec[i] for i in range(3)]
        # down
        if 16 in self.active_keys and self.active_keys[16]:
            dir_matr=[dir_matr[i]-up_vec[i] for i in range(3)]
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
        self.yaw-=dx*self.sensitivity
        if self.yaw>360 or self.yaw <-360:
            self.yaw = 0
        self.pitch+=dy*self.sensitivity
        self.pitch=max(-89.9, min(89.9, self.pitch))

    def zoom(self):
        target_fov = self.state.value
        diff = target_fov-self.fov
        if abs(diff)>0.05:
            self.fov += diff * 0.05
