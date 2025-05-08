from core.region_gen import Region
from core.perlin_noise import PerlinNoise
def init_heights(seed,n_rings,intensity,rg_data):
    '''
    initializes y-levels for each block in a 3^n_rings sized world
    returns them as a dictionary where for (x,z) => y
    '''
    border = (1 + ((n_rings-1)*3))*2
    y_data = {}
    for x in range(-border,border+1,1):
        for z in range(-border,border+1,1):
            rg = rg_data[(x,z)]
            y_data[(x,z)]=get_y((x,z),seed,rg,intensity)
    return y_data

#BASE_AMPLITUDE - визначає висоту гір, пагорбів чи горбів 
# BASE_FREQUENCY - частота появ гір, пагорбів чи горбів
# PERSISTENCE - зменшення амплітуди появи гір(чим менше поставити, тим більше буде
# використовуватися стовпців для створення гір, пагорбів чи горбів).
# intensity - модифікатор для всіх параметрів.
def get_y(coordinates, seed, region, intensity=0.7):
    MIN_HEIGHT = 20.0
    BASE_AMPLITUDE = 35
    BASE_FREQUENCY = 0.2
    PERSISTENCE = 0.5
    if region == Region.STEPPE or region == Region.SNOW_PLAINS:
        intensity = 0.5 
        BASE_AMPLITUDE = 20.0
        BASE_FREQUENCY = 0.01
        PERSISTENCE = 0.5
    elif region == Region.MOUNTAINS:
        MIN_HEIGHT = 25.0
        BASE_AMPLITUDE = 28.0
        BASE_FREQUENCY = 0.06
        PERSISTENCE = 0.2
    elif region == Region.FOREST:
        BASE_AMPLITUDE = 20.0
        BASE_FREQUENCY = 0.01
        PERSISTENCE = 0.5
    elif region == Region.HILLS:
        MIN_HEIGHT = 22.0
        BASE_AMPLITUDE = 22.0
        BASE_FREQUENCY = 0.06
        PERSISTENCE = 1.5


    
    


         
    noise_gen = PerlinNoise(seed)
    x, z = coordinates
    y = noise_gen.noise(x * BASE_FREQUENCY, z * BASE_FREQUENCY) * BASE_AMPLITUDE
    y += noise_gen.noise(x * BASE_FREQUENCY * 2, z * BASE_FREQUENCY * 2) * (BASE_AMPLITUDE * PERSISTENCE)
    y += noise_gen.noise(x * BASE_FREQUENCY * 4, z * BASE_FREQUENCY * 4) * (BASE_AMPLITUDE * PERSISTENCE * PERSISTENCE)
    
    y *= intensity
    y += MIN_HEIGHT
    
    return y
