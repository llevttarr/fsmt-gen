import math
import random
def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(t, a, b):
    return a + t * (b - a)

class PerlinNoise:
    def __init__(self, seed=None):
        random.seed(seed)
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p += self.p

    def grad(self, hash, x, y, z):
        h = hash & 15
        u = x if h < 8 else y
        v = y if h < 4 else z if h == 12 or h == 14 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def noise(self, x, y, z=0):
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255

        x -= math.floor(x)
        y -= math.floor(y)
        z -= math.floor(z)

        u = fade(x)
        v = fade(y)
        w = fade(z)

        A = self.p[X] + Y
        AA = self.p[A] + Z
        AB = self.p[A + 1] + Z
        B = self.p[X + 1] + Y
        BA = self.p[B] + Z
        BB = self.p[B + 1] + Z

        return lerp(w,
            lerp(v,
                lerp(u,
                    self.grad(self.p[AA], x, y, z),
                    self.grad(self.p[BA], x-1, y, z)),
                lerp(u,
                    self.grad(self.p[AB], x, y-1, z),
                    self.grad(self.p[BB], x-1, y-1, z))),
            lerp(v,
                lerp(u,
                    self.grad(self.p[AA+1], x, y, z-1),
                    self.grad(self.p[BA+1], x-1, y, z-1)),
                lerp(u,
                    self.grad(self.p[AB+1], x, y-1, z-1),
                    self.grad(self.p[BB+1], x-1, y-1, z-1))))