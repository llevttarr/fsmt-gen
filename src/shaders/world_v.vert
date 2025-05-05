#version 450 core

layout(location = 0) in vec3 aPos;
layout(location = 1) in float aTimeCreated;
layout(location = 2) in float aRegion;
layout(location = 3) in float aSelected;
out float vRegion;
out float isSelected;
out float yLevel;
out float dTime;
out float cTime;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float time;

void main() {
    yLevel = aPos.y;
    vRegion = aRegion;
    isSelected = aSelected;
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    dTime = time - aTimeCreated;
    cTime = time;
}
