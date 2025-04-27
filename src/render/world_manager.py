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
BLOCK_SIZE = 2

class Block:
    def __init__(self, center_x, y, center_z, region: Region, obj=None):
        self.center_x = center_x
        self.y = y
        self.k = 5 # change rate
        self.curr_y = y-self.k
        self.center_z = center_z
        self.a = 0.1 # alpha
        self.time_created = time.perf_counter()

        self.region = region
        self.obj = obj
        
        self.is_final = False
    def update(self):
        if self.is_final:
            return
        s = self.k
        diff = 0.001*((time.perf_counter()- self.time_created)**4)
        self.curr_y += s * diff
        if self.curr_y >= self.y:
            self.curr_y = self.y
            self.appearing = False

class Chunk:
    def __init__(self, seed, center_x=0, center_z=0):
        self.blocks = []
        #block size
        size = BLOCK_SIZE

        self.vertex_buffer = None
        self.element_buffer = None
        self.vertex_array = None
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
        self.rebuild()

    def get_v_color(self, y):
        return [0.5, (y/30), 0.5] #temp
    def render_block(self,block:Block):
        x,y,z = block.center_x,block.curr_y,block.center_z
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
    def update(self):
        flag = False
        for block in self.blocks:
            if not block.is_final:
                block.update()
                flag = True
        if flag:
            self.rebuild()
    def send_gpu(self):
        if self.vertex_array is None:
            self.vertex_array = glGenVertexArrays(1)
            self.vertex_buffer = glGenBuffers(1)
            self.element_buffer = glGenBuffers(1)
        glBindVertexArray(self.vertex_array)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, np.array(self.vertex_list, dtype=np.float32).nbytes, np.array(self.vertex_list, dtype=np.float32), GL_DYNAMIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.element_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array(self.i_list, dtype=np.uint32).nbytes, np.array(self.i_list, dtype=np.uint32), GL_DYNAMIC_DRAW)
    
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 24, ctypes.c_void_p(0))

        glEnableClientState(GL_COLOR_ARRAY)
        glColorPointer(3, GL_FLOAT, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def rebuild(self):
        self.vertex_list=[]
        self.i_list=[]
        self.v_count = 0
        for block in self.blocks:
            self.render_block(block)
        self.send_gpu()

    def render(self):
        glBindVertexArray(self.vertex_array)
        glDrawElements(GL_TRIANGLES, len(self.i_list), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)


class World:
    def __init__(self, seed,shader=None, n_rings=10, generation_rate=2, obj_intensity=0.5, height_intensity=0.5): #generation_rate is measured in ticks
        self.seed = seed
        if n_rings < 1:
            raise ValueError("Number of rings cannot be less than 1")
        self.n_rings = n_rings
        # self.shader = shader
        self.last_tick = time.perf_counter()
        self.ticks_elapsed = 1
        self.rate = generation_rate
        if generation_rate < 1:
            raise ValueError("Generation rate cannot be less than 1")

        self.chunk_scheduled = []
        self.chunk_list = []
        # self.view_type = ObjectViewType.DEFAULT

    def generate_mesh(self):
        '''
        Generates a list of chunks to implement
        '''
        self.chunk_scheduled.append((0,0))
        curr_ring = 1
        while curr_ring < self.n_rings:
            r = 6*curr_ring
            for x in range(-r,r+1,6):
                self.chunk_scheduled.append((x, r))
                self.chunk_scheduled.append((x, -r))
            for z in range(-r+6,r-5,6):
                self.chunk_scheduled.append((r, z))
                self.chunk_scheduled.append((-r, z))
            curr_ring+=1
    def update(self):
        for chunk in self.chunk_list:
            chunk.update()
    def generate_chunk(self):
        if not self.chunk_scheduled:
            return
        x,z=self.chunk_scheduled.pop(0)
        print(f'generating chunk at {x}, {z}')
        chunk = Chunk(self.seed, center_x=x, center_z=z)
        self.chunk_list.append(chunk)
    def perf_tick(self):
        if time.perf_counter() - self.last_tick< (1/15):
            return
        self.ticks_elapsed+=1
        self.last_tick = time.perf_counter()
        if self.ticks_elapsed%self.rate==0 and len(self.chunk_scheduled)!=0:
            self.generate_chunk()
    def render(self):
        for chunk in self.chunk_list:
            chunk.render()
