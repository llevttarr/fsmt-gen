'''
Environment management utility
'''
import sys
import os

from core.enums import Region
from core.terrain_gen import get_y
from core.region_gen import get_region
from core.object_gen import can_place
from core.matrix_util import Vector3D,Vector4D,Matrix3D,Matrix4D

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
        self.model_matrix = Matrix4D(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )
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
        #block size
        size = BLOCK_SIZE
        self.state = GL_DYNAMIC_DRAW

        self.k = 5 # Block.y_0 = Block.y - k
        self.time_created = time.perf_counter()

        self.vao = None
        self.vbo = None
        self.ebo = None
        self.v_list = []
        self.i_list = []
        self.v_count = 0

        # obj
        self.o_vao = None
        self.o_vbo = None
        self.o_ebo = None
        self.o_v_list = []
        self.o_i_list = []
        self.o_v_count = 0

        self.world = None
        self.not_final = True
        self.selected = False
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
                            "static","assets","spruce.obj"
                        )
                        ))
                    obj.translate(x,y,z)
                block = Block(x, y, z, rg, obj)
                self.blocks.append(block)
        self.rebuild()

    def get_v_color(self, y):
        return [0.5, (y/30), 0.5] #temp
    def render_block(self,block:Block):
        x,z = block.center_x,block.center_z
        y = block.y - self.k
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
        is_selected=0.1
        if self.world is not None \
        and self.world.selected_block is not None \
        and (self.world.selected_block.center_x==block.center_x and self.world.selected_block.center_z==block.center_z):
            is_selected=1.0
        info = [block.time_created,block.region.value,is_selected,y+0.1]
        for v in v_list:
            self.v_list.extend(v+info)
            # self.v_list.extend(v+v_c)
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
        if block.obj is not None:
            if not block.is_final:
                dy = y - block.obj.y
                block.obj.translate(0,dy,0)
            o_v,o_vlist,o_ilist = block.obj.get_mesh(self.o_v_count,info)
            self.o_v_count+=o_v
            self.o_i_list.extend(o_ilist)
            self.o_v_list.extend(o_vlist)
    def rebuild(self):
        if self.k>0:
            diff = 0.003*((time.perf_counter()- self.time_created)**4)
            self.k-=diff
            if self.k < 0:
                self.k = 0
        self.v_list = []
        self.i_list = []
        self.v_count = 0

        self.o_v_list = []
        self.o_i_list = []
        self.o_v_count = 0
        for block in self.blocks:
            self.render_block(block)
            if block.is_final and self.not_final:
                self.not_final = False
        self.send_gpu()
    def send_gpu(self):
        if self.vao is None:
            self.vao = glGenVertexArrays(1)
            self.vbo = glGenBuffers(1)
            self.ebo = glGenBuffers(1)

            self.o_vao = glGenVertexArrays(1)
            self.o_vbo = glGenBuffers(1)
            self.o_ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        vlist_np = np.array(self.v_list, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, vlist_np.nbytes, vlist_np, self.state)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        ilist_np = np.array(self.i_list, dtype=np.uint32)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, ilist_np.nbytes, ilist_np, self.state)

        # koroche
        # 4:x,4:y,4:z,4:time_created,4:region,4:is_selected
        # xyz for position,
        # time_created for alpha, region for color scheme, is_selected for pulsating glow (if needed)

        # it's probably not necesarry to give so much space for is_selected and region
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(16))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(20))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(24))
        glEnableVertexAttribArray(4)
        # obj
        glBindVertexArray(self.o_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.o_vbo)
        vlist_np = np.array(self.o_v_list, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, vlist_np.nbytes, vlist_np, self.state)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.o_ebo)
        ilist_np = np.array(self.o_i_list, dtype=np.uint32)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, ilist_np.nbytes, ilist_np, self.state)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(16))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(20))
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(24))
        glEnableVertexAttribArray(4)

        glBindVertexArray(0)
    
    def render(self, shader):
        model_matrix = Matrix4D(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )
        shader.set_mat4("model", model_matrix)
        shader.set_float("time", time.perf_counter())
        glBindVertexArray(self.vao)
        # glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glDrawElements(GL_TRIANGLES, len(self.i_list), GL_UNSIGNED_INT, None)
        
        glBindVertexArray(self.o_vao)
        # glBindBuffer(GL_ARRAY_BUFFER, self.o_vbo)
        # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.o_ebo)
        glDrawElements(GL_TRIANGLES, len(self.o_i_list), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)


class World:
    def __init__(self, y_info,rg_info,obj_info, seed=1,shader=None, n_rings=10, generation_rate=2, obj_intensity=0.5, height_intensity=0.5): #generation_rate is measured in ticks
        self.seed = seed
        self.shader = shader
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
        self.dynamic_chunks = []
        self.chunk_list = []
        # self.view_type = ObjectViewType.DEFAULT

        self.y_info = y_info
        self.rg_info = rg_info
        self.obj_info = obj_info

        self.selected_block = None
        self.selected_chunk = None
        self.prev_selected_chunk = None # saving it so deselection is possible
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
        to_remove = []
        for chunk in self.dynamic_chunks:
            if chunk.k<=0.1:
                chunk.state = GL_STATIC_DRAW
                to_remove.append(chunk)
            chunk.rebuild()
        for chunk in to_remove:
            self.dynamic_chunks.remove(chunk)
    def generate_chunk(self):
        if not self.chunk_scheduled:
            return
        x,z=self.chunk_scheduled.pop(0)
        # print(f'generating chunk at {x}, {z}')
        chunk = Chunk(self.seed, center_x=x, center_z=z)
        chunk.world = self
        self.chunk_list.append(chunk)
        self.dynamic_chunks.append(chunk)
    def perf_tick(self):
        if time.perf_counter() - self.last_tick< (1/20):
            return
        self.update()
        self.ticks_elapsed+=1
        self.last_tick = time.perf_counter()
        if self.ticks_elapsed%self.rate==0 and len(self.chunk_scheduled)!=0:
            self.generate_chunk()
    def render(self):
        if not self.shader:
            return
            
        self.shader.use()
        if self.selected_chunk:
            self.selected_chunk.state = GL_DYNAMIC_DRAW
            self.selected_chunk.rebuild()
        if self.prev_selected_chunk:
            self.prev_selected_chunk.state = GL_STATIC_DRAW
            self.prev_selected_chunk.rebuild()
        for chunk in self.dynamic_chunks:
            chunk.rebuild()
        for chunk in self.chunk_list:
            chunk.render(self.shader)
        self.shader.stop()
# # # # # # #
    def intersect_check(self, ray_origin, ray_dir, bound_0, bound_max):
        t_0=(bound_0.data-ray_origin)/ray_dir
        t_1=(bound_max.data-ray_origin)/ray_dir
        t_0=Vector3D(t_0[0], t_0[1],t_0[2])
        t_1=Vector3D(t_1[0], t_1[1],t_1[2])

        t_min = np.minimum(t_0.data, t_1.data)
        t_max = np.maximum(t_0.data, t_1.data)

        t_enter = np.max(t_min)
        t_exit = np.min(t_max)
        if t_enter > t_exit or t_exit < 0:
            return False, None
        return True,t_enter
    def select_block(self, ray_origin, ray_dir):
        temp = None
        if self.selected_chunk:
            temp = self.selected_chunk
        print(f"casting ray <{ray_origin} in dir: {ray_dir}>")
        closest_b,closest_c,closest_t=None,None,float('inf')
        for chunk in self.chunk_list:
            k = chunk.k
            for block in chunk.blocks:
                bound_0=Vector3D(block.center_x-1,0,block.center_z-1)
                bound_max=Vector3D(block.center_x+1,block.y-k,block.center_z+1)
                hit_occured,t_hit=self.intersect_check(ray_origin,ray_dir,bound_0,bound_max)
                if hit_occured and t_hit<closest_t:
                    closest_t,closest_b=t_hit,block
                    closest_c = chunk
        if closest_b is not None:
            print(f'selected block at {closest_b.center_x}, {closest_b.curr_y}, {closest_b.center_z}')
            print(f'region of the block: {closest_b.region}')
            print(f'has object: {closest_b.obj is not None}')
            self.selected_chunk = closest_c
            self.selected_block = closest_b
            if temp:
                self.prev_selected_chunk = temp
        else:
            print('removing selection')
            if self.selected_chunk is not None:
                self.prev_selected_chunk = self.selected_chunk
                self.selected_chunk = None
                self.selected_block = None
                if temp:
                    self.prev_selected_chunk = temp
