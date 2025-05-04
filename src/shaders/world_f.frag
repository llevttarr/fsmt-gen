#version 450 core

in float yLevel;
flat in int vRegion;
flat in int isSelected;
in float dTime;

out vec4 FragColor;

vec3 steppeGradient(float y) {
    vec3 color1 = vec3(0.84, 1.0, 0.35);
    vec3 color2 = vec3(1.0, 0.85, 0.27);
    vec3 color3 = vec3(1.0, 0.53, 0.27);
    
    if (y < 0.5) {
        return mix(color1, color2, y * 2.0);
    } else {
        return mix(color2, color3, (y - 0.5) * 2.0);
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
    float normalizedY = clamp(yLevel / 60.0, 0.0, 1.0);
    vec3 baseColor;
    if (vRegion == 1) {
        baseColor = steppeGradient(normalizedY);
    } else if (vRegion == 2) {
        baseColor = forestGradient(normalizedY);
    } else {
        baseColor = snowPlainsGradient(normalizedY);
    }
    float alpha = clamp(dTime / 100.0, 0.0, 1.0);
    if (isSelected == 1) {
        float pulse = 0.5 * (1.0 + sin(dTime * 0.02));
        baseColor = mix(baseColor, vec3(1.0), pulse);
    }
    FragColor = vec4(baseColor, alpha);
}
