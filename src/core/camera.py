from OpenGL.GL import *
from OpenGL.GLU import *
class Camera:
    def __init__(self):
        self.pos = [25, 25, 25]
        self.yaw,self.pitch = 0.1,0.1
        self.fov=60.0
        self.speed=0.05
    def apply(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width / height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(*self.pos, 0, 0, 0, 0, 1, 0)
