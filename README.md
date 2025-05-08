# Terrain generator
<h3> UCU.CS: Discrete Math II - Computer project</h3>

![Project logo](static/logo.png)
## Requirements
```
PyOpenGL==3.1.9
PyQT5==5.15.11
PyWavefront==1.3.3
numpy==2.2.5
matplotlib==3.10.1
```
![Project preview](static/prj_preview.gif)
# Run project
To launch the project, clone the repo and run ```src/__main__.py```
```
git clone https://github.com/llevttarr/fsmt-gen.git
py fsmt-gen/src/__main__.py
```
# Task distribution
<table>
  <tr>
    <td>
      <a href="https://github.com/llevttarr">
        <img src="https://avatars.githubusercontent.com/llevttarr" width="100px;" alt="llevttarr"/><br />
        <sub><b>Taras Levytskyi</b></sub>
      </a>
      <br/>3D visualisation
    </td>
    <td>
      <a href="https://github.com/ArseniiStratiuk">
        <img src="https://avatars.githubusercontent.com/ArseniiStratiuk" width="100px;" alt="ArseniiStratiuk"/><br />
        <sub><b>Arsenii Stratiuk</b></sub>
      </a>
      <br/>Object gen.
    </td>
    <td>
      <a href="https://github.com/rasthpop">
        <img src="https://avatars.githubusercontent.com/rasthpop" width="100px;" alt="rasthpop"/><br />
        <sub><b>Taras Kopach</b></sub>
      </a>
      <br/>UI, Region gen.
    </td>
    <td>
      <a href="https://github.com/Sneezyan123">
        <img src="https://avatars.githubusercontent.com/Sneezyan123" width="100px;" alt="Sneezyan123"/><br />
        <sub><b>Artem Onyschuk</b></sub>
      </a>
      <br/>Height gen.
    </td>
  </tr>
</table>

# About
**fsmt-gen** is a Python OpenGL app that is made for visualising terrain-generating algorithms made with using Finite State Machines. It implements algorithms such as Perlin-noise, Simplex-noise and some custom ones to pseudorandomly generate a world with unique terrain, regions and custom objects.
## Generation process
<p align="center">
  <code>input[seed; args]</code>
  ->
  <code>region generation</code>
  ->
  <code>height generation</code>
  ->
  <code>object generation</code>
  ->
  <code>3D render</code>
</p>

> Звіт до проєкту в репозиторії
