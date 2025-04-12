'''
Object and environment management utility
'''

from OpenGL.GL import *
from OpenGL.GLU import *
from pywavefront import Wavefront
from enum import Enum
import numpy as np

class RotationAxis(Enum):
    X=1
    Y=2
    Z=3

class Object3D:
    def __init__(self, path, outline_only: False):
        self.info = Wavefront(path, collect_faces=True) # path - path to the .obj file of the object
        self.transform = np.identity(4, dtype=np.float32)

    def translate(self, x, y, z):
        translation = np.array([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        self.transform = translation @ self.transform

    def scale(self, sx, sy, sz):
        scaling = np.array([
            [sx, 0,  0,  0],
            [0, sy,  0,  0],
            [0,  0, sz, 0],
            [0,  0,  0, 1]
        ], dtype=np.float32)
        self.transform = scaling @ self.transform

    def rotate(self, axis: RotationAxis, angle):
        pass
    def render(self):
        pass
class Chunk:
    def __init__(self):
        pass
