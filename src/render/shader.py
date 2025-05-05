from OpenGL.GL import *

from core.matrix_util import Matrix3D,Matrix4D
import numpy as np
class Shader:
    def __init__(self, vertex_path, fragment_path):
        self.program = self.create_shader_program(vertex_path, fragment_path)

    def create_shader_program(self, vertex_path, fragment_path):
        with open(vertex_path, 'r') as f:
            vertex_src = f.read()
        with open(fragment_path, 'r') as f:
            fragment_src = f.read()

        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_src)
        glCompileShader(vertex_shader)
        self.check_compile_errors(vertex_shader, "VERTEX")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_src)
        glCompileShader(fragment_shader)
        self.check_compile_errors(fragment_shader, "FRAGMENT")

        shader_program = glCreateProgram()
        glAttachShader(shader_program, vertex_shader)
        glAttachShader(shader_program, fragment_shader)
        glLinkProgram(shader_program)
        self.check_compile_errors(shader_program, "PROGRAM")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        return shader_program

    def use(self):
        glUseProgram(self.program)

    def stop(self):
        glUseProgram(0)

    def set_mat4(self, name, matrix:Matrix4D):
        loc = glGetUniformLocation(self.program, name)
        matrix_flattened = np.array(matrix.data, dtype=np.float32).flatten('F')
        glUniformMatrix4fv(loc, 1, GL_FALSE, matrix_flattened)
    def set_mat3(self, name, matrix: Matrix3D):
        loc = glGetUniformLocation(self.program, name)
        matrix_flattened = np.array(matrix.data, dtype=np.float32).flatten('F')
        glUniformMatrix3fv(loc, 1, GL_FALSE, matrix_flattened)
    def set_vec3(self, name, x, y, z):
        loc = glGetUniformLocation(self.program, name)
        glUniform3f(loc, x, y, z)
    def set_vec4(self, name, x, y, z, w):
        loc = glGetUniformLocation(self.program, name)
        glUniform4f(loc, x, y, z, w)
    def set_float(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        glUniform1f(loc, value)
    def set_int(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        glUniform1i(loc, value)
    def check_compile_errors(self, shader, t):
        if t == "PROGRAM":
            success = glGetProgramiv(shader, GL_LINK_STATUS)
            if not success:
                info = glGetProgramInfoLog(shader)
                print(f"ERROR::SHADER::PROGRAM::LINKING_FAILED\n{info.decode()}")
        else:
            success = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if not success:
                info = glGetShaderInfoLog(shader)
                print(f"ERROR::SHADER::{t}::COMPILATION_FAILED\n{info.decode()}")
