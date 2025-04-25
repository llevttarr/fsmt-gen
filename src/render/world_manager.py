'''
Environment management utility
'''
from core.enums import Region
from core.terrain_gen import get_y
from core.region_gen import get_region
from core.object_gen import can_place

from OpenGL.GL import *
from OpenGL.GLU import *

import random as rand
import numpy as np
import time
class Block:
    def __init__(self, center_x, y, center_z, region: Region, obj=None):
        self.center_x = center_x
        self.y = y
        self.center_z = center_z
        self.region = region
        self.obj = obj

class Chunk:
    def __init__(self, seed, center_x=0, center_z=0):
        self.blocks = []
        #block size
        size = 2
        #every chunk has 9 blocks
        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                x = center_x + dx * size
                z = center_z + dz * size
                y = get_y((x, z), seed)
                rg = get_region((x,z),seed)
                obj = None
                if can_place((x,y,z),seed):
                    obj = None #temp
                self.blocks.append(Block(x, y, z, rg))

class World:
    def __init__(self, seed,shader, n_rings=2):
        self.seed = seed
        self.n_rings = n_rings
        self.shader = shader
        self.chunk_list = []

        self.vertex_list = []
        self.v_count = 0
        self.i_list = []
        self.vertex_buffer = None
        self.element_buffer = None
        self.vertex_array = None

        # self.view_type = ObjectViewType.DEFAULT
    def get_v_color(self, y):
        return [0.5, (y/30), 0.5] #temp
    def generate_mesh(self):
        '''
        Generates a list of chunks to implement
        '''
        self.generate_chunk(0,0)
        # TODO: smooth generation
        # curr_ring = 1
        # while curr_ring < self.n_rings:
        #     # edges of the ring (w/o corners)
        #     for j in range(- (2*(curr_ring-1) + 1), (2*(curr_ring-1))+1):    
        #         self.generate_chunk( 6*j, 6*j)
        #         self.generate_chunk(6*j, -6*j)
        #         self.generate_chunk(-6*j, 6*j)
        #         self.generate_chunk(-6*j, -6*j)

        #     # corners of the ring
        #     self.generate_chunk(6*curr_ring, 6*curr_ring)
        #     self.generate_chunk(-6*curr_ring, 6*curr_ring)
        #     self.generate_chunk(-6*curr_ring, -6*curr_ring)
        #     self.generate_chunk(6*curr_ring, -6*curr_ring)
        #     curr_ring+=1
        for x in range(-6*5,6*5,6):
            for z in range(-6*5,6*5,6):
                self.generate_chunk(x,z)

        self.vertex_list=np.array(self.vertex_list, dtype=np.float32)
        self.i_list=np.array(self.i_list, dtype=np.uint32)
        self.send_gpu()

    def generate_chunk(self, center_x, center_z):
        # TODO: smooth generation
        chunk = Chunk(self.seed, center_x=center_x, center_z=center_z)
        self.chunk_list.append(chunk)
        for block in chunk.blocks:
            self.render_block(block)

    def render_block(self,block:Block):
        x,y,z = block.center_x,block.y,block.center_z
        v_list = [
            [x-1,0,z-1],
            [x+1,0,z-1],
            [x+1,0,z+1],
            [x-1,0,z+1],
            
            [x-1,y,z-1],
            [x+1,y,z-1],
            [x+1,y,z+1],
            [x-1,y,z+1],
        ]
        f_list = [
            (3, 2, 1, 0), 
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7)
        ]

        v_c = self.get_v_color(y)
        for v in v_list:
            self.vertex_list.extend(v+v_c)
        for f in f_list:
            self.i_list.extend(
                [
                    self.v_count + f[0],
                    self.v_count + f[1],
                    self.v_count + f[2],
                    self.v_count + f[0],
                    self.v_count + f[2],
                    self.v_count + f[3],
                ]
            )
        self.v_count+=8

    def send_gpu(self):
        self.vertex_array = glGenVertexArrays(1)
        self.vertex_buffer = glGenBuffers(1)
        self.element_buffer = glGenBuffers(1)

        glBindVertexArray(self.vertex_array)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_list.nbytes, self.vertex_list, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.element_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.i_list.nbytes, self.i_list, GL_STATIC_DRAW)

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 24, ctypes.c_void_p(0))
        glEnableClientState(GL_COLOR_ARRAY)
        glColorPointer(3, GL_FLOAT, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)
    def render(self):
        glBindVertexArray(self.vertex_array)
        glUseProgram(0)
        glDrawElements(GL_TRIANGLES, len(self.i_list), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
