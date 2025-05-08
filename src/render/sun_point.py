from core.matrix_util import Vector3D

class SunFSM:
    def __init__(self,seed):
        self.seed = seed
        self.point=Vector3D(0,0,0)
        self.angle=0
        self.start=None
        self.end_states=[]
        self.handlers={}
        # TODO
    def get_next(self):
        pass
