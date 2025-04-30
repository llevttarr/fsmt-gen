'''
Object and matrix management utility
'''
from OpenGL.GL import *
from OpenGL.GLU import *
from pywavefront import Wavefront
from math import cos, sin

from core.matrix_util import Matrix4D,Vector3D,Vector4D,Matrix3D
from core.enums import ObjectViewType,RotationAxis

import random as rand

class Object3D:
    def __init__(self, path):
        self.info = Wavefront(path, collect_faces=True,create_materials=False) # path - path to the .obj file of the object
        self.m_list = self.info.mesh_list
        self.vi_list = self.info.vertices
        self.transform = Matrix4D(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )
    @property
    def y(self):
        return self.transform.data[1][3]
    def translate(self, x, y, z):
        tr_matrix = Matrix4D(
            1, 0, 0, x,
            0, 1, 0, y,
            0, 0, 1, z,
            0, 0, 0, 1
        )
        self.transform = tr_matrix @ self.transform
    def scale(self, x, y, z):
        sc_matrix = Matrix4D(
            x, 0, 0, 0,
            0, y, 0, 0,
            0, 0, z, 0,
            0, 0, 0, 1
        )
        self.transform = sc_matrix @ self.transform
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
        self.transform = r_matrix @ self.transform
    def generate_mesh(self):
        v_list = []
        i_list = []
        for x, y, z in self.vi_list:
            vec = self.transform @ Vector4D(x, y, z, 1)
            r=rand.randint(1,10)/10
            v_list.extend([vec[0], vec[1], vec[2]] + [0.3,r,0.3])
        for mesh in self.m_list:
            for face in mesh.faces:
                if len(face) == 3:
                    i_list.extend([face[0], 
                                face[1], 
                                face[2]])

        self.v_list,self.i_list=v_list, i_list
    def render(self):
        pass
