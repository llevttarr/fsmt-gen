import numpy as np

class Vector:
    def __init__(self, *args):
        self.data = np.array(args, dtype=float)

    def __add__(self, other):
        return Vector(*(self.data + other.data))

    def __sub__(self, other):
        return Vector(*(self.data - other.data))

    def __mul__(self, scalar): 
        return Vector(*(self.data * scalar))

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __matmul__(self, other):
        return np.dot(self.data, other.data)

    def __getitem__(self, index):
        return self.data[index]

    def __eq__(self, other):
        return np.allclose(self.data, other.data)

    def __repr__(self):
        return f"Vector{len(self.data)}D({', '.join(map(str, self.data))})"

    def __len__(self):
        return np.linalg.norm(self.data)

    def normalize(self):
        norm = self.length()
        return Vector(*(self.data / norm)) if norm != 0 else self

class Vector3D(Vector):
    def __init__(self, vx, vy, vz):
        super().__init__(vx, vy, vz)

class Vector4D(Vector):
    def __init__(self, x, y, z, w):
        super().__init__(x, y, z, w)
# # #
class Matrix:
    def __init__(self, *args):
        self.data = np.array(args, dtype = float).reshape((self.size, self.size))
    def __matmul__(self, other):
        if isinstance(other, Matrix):
            return self.__class__((self.data @ other.data).flatten())
        elif isinstance(other, Vector):
            result = self.data @ other.data
            return Vector(*result)
        raise TypeError

    def __repr__(self):
        return f"{self.__class__.__name__}(\n{self.data}\n)"

    def transpose(self):
        return self.__class__(self.data.T.flatten())

class Matrix3D(Matrix):
    size = 3
    def __init__(self, *args):
        super().__init__(args)

class Matrix4D(Matrix):
    size = 4
    def __init__(self, *args):
        super().__init__(args)
