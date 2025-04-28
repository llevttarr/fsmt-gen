from core.enums import Region

import random as rand
def can_place(coordinates, seed,region=Region.STEPPE,intensity=0.03):
    #TODO
    if rand.random()>intensity:
        return False
    return True
