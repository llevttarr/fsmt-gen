from math import floor
import random
from core.enums import Region
from core.perlin_noise import PerlinNoise

def init_regions(seed,n_rings):
    '''
    initializes regions for each block in a 3^n_rings sized world
    returns them as a dictionary where for (x,z) => Region
    '''
    random.seed(seed)
    border = (1 + ((n_rings-1)*3))*2
    directions = [
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),
        (0, -1),
        (-1, -1)
        ]

    n_regions = 4 #random.randint(1, 4)
    rg_data = {}
    q = []
    
    for _ in range(n_regions):
        x, z = random.randint(-border, border), random.randint(-border, border)
        rg_data[(x, z)] = Region(random.randint(0, 3))  
        q.append((x, z))

    while q:
        cur_block = random.choice(q)
        q.remove(cur_block)
        cur_region = rg_data[cur_block]
        for direction in directions:
            nx = cur_block[0] + direction[0]
            nz = cur_block[1] + direction[1]

            if (-border <= nx <= border) and\
               (-border <= nz <= border) and\
               ((nx, nz) not in rg_data):
                q.append((nx, nz))
                rg_data[(nx, nz)] = cur_region
    for (x, z) in rg_data: 
        has_steppe = False
        has_mountains = False

        for direction in directions:
            nx = x + direction[0]
            nz = z + direction[1]

            if (-border <= nx <= border) and (-border <= nz <= border):
                neighbor_region = rg_data[(nx, nz)]

                if neighbor_region == Region.STEPPE or neighbor_region == Region.SNOW_PLAINS:
                    has_steppe = True
                if neighbor_region == Region.MOUNTAINS:
                    has_mountains = True

                if has_steppe and has_mountains:
                    rg_data[(x, z)] = Region.HILLS
                    for direction2 in directions:
                        nnx = x + direction2[0]
                        nnz = z + direction2[1]
                        if (-border <= nnx <= border) and (-border <= nnz <= border):
                            rg_data[(nnx, nnz)] = Region.HILLS
                    break
    return rg_data

