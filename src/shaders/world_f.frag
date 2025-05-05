#version 450 core

in float yLevel;
in float vRegion;
in float isSelected;
in float dTime;
in float cTime;

out vec4 FragColor;

vec3 steppeGradient(float y) {
    vec3 color0 = vec3(0.72, 1, 0.55);
    vec3 color1 = vec3(1, 0.9, 0.71);
    vec3 color2 = vec3(0.92, 0.69, 0.44);
    vec3 color3 = vec3(0.93, 0.58, 0.39);
    vec3 color4 = vec3(0.68, 0.39, 0.27);
    vec3 color5 = vec3(0.57, 0.19, 0.11);
    
    if (y < 0.2) {
        return mix(color0, color1, y * 2.0);
    }else if (y < 0.4){
        return mix(color1, color2, (y-0.2) * 2.0);
    }else if (y < 0.6){
        return mix(color2, color3, (y-0.4) * 2.0);
    }else if (y < 0.8){
        return mix(color3, color4, (y-0.6) * 2.0);
    }
     else {
        return mix(color4, color5, (y - 0.8) * 2.0);
    }
}

vec3 forestGradient(float y) {
    vec3 color1 = vec3(0.27, 1, 0.51);
    vec3 color2 = vec3(0.19, 1, 0.15);
    vec3 color3 = vec3(0.18, 0.71, 0.03);
    
    if (y < 0.5) {
        return mix(color1, color2, y * 2.0);
    } else {
        return mix(color2, color3, (y - 0.5) * 2.0);
    }
}

vec3 snowPlainsGradient(float y) {
    vec3 color1 = vec3(0.48, 0.6, 0.58);
    vec3 color2 = vec3(0.62, 0.84, 0.81);
    vec3 color3 = vec3(0.94, 1, 0.99);
    
    if (y < 0.5) {
        return mix(color1, color2, y * 2.0);
    } else {
        return mix(color2, color3, (y - 0.5) * 2.0);
    }
}

void main() {
    float normalizedY = clamp(yLevel / 30.0, 0.0, 1.0);
    vec3 baseColor;
    if (vRegion < 1.1) {
        baseColor = steppeGradient(normalizedY);
    } else if (vRegion < 2.1) {
        baseColor = forestGradient(normalizedY);
    } else if (vRegion < 3.1){
        baseColor = snowPlainsGradient(normalizedY);
    }else if (vRegion < 4.1){ // tree
        baseColor=vec3(0.1, 0.6, 0.5);
    }else if (vRegion< 5.1){ // rock
        baseColor=vec3(0.4, 0.4, 0.4);
    }else{ // spruce
        baseColor=vec3(0.1, 0.8, 0.5);
    }
    float alpha = clamp(dTime / 1.5, 0.0, 1.0);
    if (isSelected > 0.9) {
        float pulse = 0.5 * (1.0 + abs(sin((cTime)*2)));
        baseColor = mix(baseColor, vec3(1.0), pulse);
    }
    FragColor = vec4(baseColor, alpha);
}
