'''
Object and matrix management utility
'''
from OpenGL.GL import *
from OpenGL.GLU import *
from pywavefront import Wavefront
from math import cos, sin
from core.matrix_util import Matrix4D
from core.enums import ObjectViewType,RotationAxis

class Object3D:
    def __init__(self, path):
        self.info = Wavefront(path, collect_faces=True) # path - path to the .obj file of the object
        self.transform = Matrix4D(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )
    def translate(self, x, y, z):
        tr_matrix = Matrix4D(
            1, 0, 0, x,
            0, 1, 0, y,
            0, 0, 1, z,
            0, 0, 0, 1
        )
        self.transform = tr_matrix * self.transform
    def scale(self, x, y, z):
        sc_matrix = Matrix4D(
            x, 0, 0, 0,
            0, y, 0, 0,
            0, 0, z, 0,
            0, 0, 0, 1
        )
        self.transform = sc_matrix * self.transform
    def rotate(self, axis: RotationAxis, angle):
        ca = cos(angle)
        sa = sin(angle)
        match axis:
            case RotationAxis.X:
                r_matrix = Matrix4D(
                    1, 0, 0, 0,
                    0, ca, -sa, 0,
                    0, sa,  ca, 0,
                    0, 0, 0, 1
                )
            case RotationAxis.Y:
                r_matrix = Matrix4D(
                    ca, 0, sa, 0,
                    0, 1, 0, 0,
                    -sa, 0, ca, 0,
                    0, 0, 0, 1
                )
            case RotationAxis.Z:
                r_matrix = Matrix4D(
                    ca, -sa, 0, 0,
                    sa,  ca, 0, 0,
                    0,  0, 1, 0,
                    0,  0, 0, 1
                )
        self.transform = r_matrix * self.transform
    def render(self, view_type= ObjectViewType.DEFAULT):
        pass
