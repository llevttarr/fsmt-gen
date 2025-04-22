'''
Environment management utility
'''
from core.enums import Region
from core.terrain_gen import get_y
from core.region_gen import get_region
from core.object_gen import can_place
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
    def __init__(self, seed):
        self.seed = seed
        self.chunk_list = self.generate()
    def generate(self):
        '''
        Generates a list of chunks to implement
        '''
        seed = self.seed
        return [Chunk(seed)]
