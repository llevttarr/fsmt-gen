from core.region_gen import Region
from core.perlin_noise import PerlinNoise


MIN_HEIGHT = 20.0
#BASE_AMPLITUDE - визначає висоту гір, пагорбів чи горбів 
# BASE_FREQUENCY - частота появ гір, пагорбів чи горбів
# PERSISTENCE - зменшення амплітуди появи гір(чим менше поставити, тим більше буде
# використовуватися стовпців для створення гір, пагорбів чи горбів).
# intensity - модифікатор для всіх параметрів.
def get_y(coordinates, seed, region=Region.STEPPE, intensity=0.7):
    BASE_AMPLITUDE = 35
    BASE_FREQUENCY = 0.2
    PERSISTENCE = 0.5
    if region == Region.STEPPE: # можна конфігурувати.
        intensity = 0.5 
        BASE_AMPLITUDE = 35.0
        BASE_FREQUENCY = 0.01
        PERSISTENCE = 0.5
    noise_gen = PerlinNoise(seed)
    x, z = coordinates
    y = noise_gen.noise(x * BASE_FREQUENCY, z * BASE_FREQUENCY) * BASE_AMPLITUDE
    y += noise_gen.noise(x * BASE_FREQUENCY * 2, z * BASE_FREQUENCY * 2) * (BASE_AMPLITUDE * PERSISTENCE)
    y += noise_gen.noise(x * BASE_FREQUENCY * 4, z * BASE_FREQUENCY * 4) * (BASE_AMPLITUDE * PERSISTENCE * PERSISTENCE)
    
    y *= intensity
    y += MIN_HEIGHT
    
    return y
