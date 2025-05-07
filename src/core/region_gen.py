from core.enums import Region
def init_regions(seed,n_rings):
    '''
    initializes regions for each block in a 3^n_rings sized world
    returns them as a dictionary where for (x,z) => Region
    '''
    border = (1 + ((n_rings-1)*3))*2
    rg_data = {}
    for x in range(-border,border+1,1):
        for z in range(-border,border+1,1):
            rg_data[(x,z)]=get_region((x,z),seed)
    return rg_data
def get_region(coordinates, seed):
    # TODO
    return Region.STEPPE
