'''
Environment management utility
'''
import sys
import os

from core.enums import Region
from core.terrain_gen import get_y
from core.region_gen import get_region
from core.object_gen import can_place
from render.object_manager import Object3D

from OpenGL.GL import *
from OpenGL.GLU import *

import random as rand
import numpy as np
import time

# sys.path.append(os.path.abspath(os.path.dirname(__file__)))

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
        diff = 0.003*((time.perf_counter()- self.time_created)**4)
        self.curr_y += s * diff
        if self.curr_y >= self.y:
            self.curr_y = self.y
            self.is_final = True

class Chunk:
    def __init__(self, seed, center_x=0, center_z=0):
        self.blocks = []
        self.blocks_q = []
        #block size
        size = BLOCK_SIZE

        self.vao = None
        # dynamic
        self.dyn_vbo = None
        self.dyn_ebo = None
        self.dyn_vlist = []
        self.dyn_ilist=[]
        self.dyn_v_count = 0
        # static
        self.st_vbo = None
        self.st_ebo = None
        self.st_vlist = []
        self.st_ilist=[]
        self.st_v_count = 0
        #every chunk has 9 blocks
        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                x = center_x + dx * size
                z = center_z + dz * size
                y = get_y((x, z), seed)
                rg = get_region((x,z),seed)
                obj = None
                if can_place((x,y,z),seed):
                    obj = Object3D(os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            "..","..", 
                            "static","assets","test_obj.obj"
                        )
                        ))
                    obj.translate(x,y,z)
                block = Block(x, y, z, rg, obj)
                self.blocks.append(block)
                self.blocks_q.append(block)
        self.rebuild()

    def get_v_color(self, y):
        return [0.5, (y/30), 0.5] #temp
    def render_block(self,block:Block,is_dynamic):
        x,z = block.center_x,block.center_z
        if is_dynamic:
            y = block.curr_y
        else:
            y = block.y
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
            (0, 1, 2, 3),  
            (7, 6, 5, 4),  
            (4, 5, 1, 0),  
            (5, 6, 2, 1),  
            (6, 7, 3, 2),  
            (7, 4, 0, 3)   
        ]

        v_c = self.get_v_color(y)
        for v in v_list:
            if is_dynamic:
                self.dyn_vlist.extend(v+v_c)
            else:
                self.st_vlist.extend(v+v_c)
        for f in f_list:
            if is_dynamic:
                self.dyn_ilist.extend(
                    [
                        self.dyn_v_count + f[0],
                        self.dyn_v_count + f[1],
                        self.dyn_v_count + f[2],
                        self.dyn_v_count + f[0],
                        self.dyn_v_count + f[2],
                        self.dyn_v_count + f[3],
                    ]
                )
            else:
                self.st_ilist.extend(
                    [
                        self.st_v_count + f[0],
                        self.st_v_count + f[1],
                        self.st_v_count + f[2],
                        self.st_v_count + f[0],
                        self.st_v_count + f[2],
                        self.st_v_count + f[3],
                    ]
                )

        if is_dynamic:
            self.dyn_v_count+=8
        else:
            self.st_v_count+=8
        if block.obj is not None:
            if is_dynamic:
                dy = y - block.obj.y
                block.obj.translate(0,dy,0)
                o_v,o_vlist,o_ilist = block.obj.get_mesh(self.dyn_v_count,[0.3, 0.1, 0.3])
                self.dyn_v_count+=o_v
                self.dyn_ilist.extend(o_ilist)
                self.dyn_vlist.extend(o_vlist)
            else:
                o_v,o_vlist,o_ilist = block.obj.get_mesh(self.st_v_count,[0.3, 0.1, 0.3])
                self.st_v_count+=o_v
                self.st_ilist.extend(o_ilist)
                self.st_vlist.extend(o_vlist)
    def update(self):
        flag = False
        finalized_blocks = []
        for block in self.blocks_q:
            if not block.is_final:
                block.update()
                if block.is_final:
                    finalized_blocks.append(block)
                flag = True
        for block in finalized_blocks:
            self.render_block(block,False)
            self.blocks_q.remove(block)
        if flag:
            self.rebuild()
    def rebuild(self):
        self.dyn_ilist = []
        self.dyn_vlist = []
        self.dyn_v_count = 0
        for block in self.blocks_q:
            self.render_block(block, True)    
        self.send_gpu()

    def send_gpu(self):
        if self.vao is None:
            self.vao = glGenVertexArrays(1)
            self.dyn_vbo = glGenBuffers(1)
            self.dyn_ebo = glGenBuffers(1)
            self.st_vbo = glGenBuffers(1)
            self.st_ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.st_vbo)
        st_vlist_np = np.array(self.st_vlist, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, st_vlist_np.nbytes, st_vlist_np, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.st_ebo)
        st_ilist_np = np.array(self.st_ilist, dtype=np.uint32)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, st_ilist_np.nbytes, st_ilist_np, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.dyn_vbo)
        dyn_vlist_np = np.array(self.dyn_vlist, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, dyn_vlist_np.nbytes, dyn_vlist_np, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.dyn_ebo)
        dyn_ilist_np = np.array(self.dyn_ilist, dtype=np.uint32)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, dyn_ilist_np.nbytes, dyn_ilist_np, GL_DYNAMIC_DRAW)

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 24, ctypes.c_void_p(0))
        glEnableClientState(GL_COLOR_ARRAY)
        glColorPointer(3, GL_FLOAT, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def render(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.st_vbo)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.st_ebo)
        glDrawElements(GL_TRIANGLES, len(self.st_ilist), GL_UNSIGNED_INT, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.dyn_vbo)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.dyn_ebo)
        glDrawElements(GL_TRIANGLES, len(self.dyn_ilist), GL_UNSIGNED_INT, None)

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

        self.selected_block = None
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
        if time.perf_counter() - self.last_tick< (1/20):
            return
        self.update()
        self.ticks_elapsed+=1
        self.last_tick = time.perf_counter()
        if self.ticks_elapsed%self.rate==0 and len(self.chunk_scheduled)!=0:
            self.generate_chunk()
    def render(self):
        for chunk in self.chunk_list:
            chunk.render()
# # # # # # # # #
    def ray_intersect(self,ray_origin,ray_dir):
        pass
    def select_block(self, ray_origin,ray_dir):
        pass
