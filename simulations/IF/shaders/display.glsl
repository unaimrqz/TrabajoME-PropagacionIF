// display.glsl
// Este shader es el encargado de renderizar la cuadrícula en la pantalla. Toma el
// estado de cada célula (fuego, elevación, combustible) y lo convierte en un color 
// que se muestra en la pantalla. El color de cada célula se determina por su estado: 
// si está ardiendo, se muestra en tonos de rojo; si no está ardiendo pero tiene 
// combustible, se muestra en tonos de verde que varían según la elevación; y si no 
// tiene combustible, se muestra en un gris oscuro. Además, el shader incluye diferentes
// modos de visualización para mostrar solo la elevación o solo el combustible, lo que 
// puede ser útil para analizar la simulación. Este shader se ejecuta en cada frame de 
// la simulación para actualizar la visualización de la cuadrícula en función del estado
// actual de cada célula.

#version 330 core

out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D u_state_texture;
uniform int u_view_mode;

void main() {
    vec4 state = texture(u_state_texture, TexCoords);
    float fire = state.r;
    float elev = state.g;
    float fuel = state.b;

    if (u_view_mode == 1) {
        FragColor = vec4(elev, elev, elev, 1.0);
        return;
    }

    if (u_view_mode == 2) {
        FragColor = vec4(0.0, 0.0, fuel, 1.0);
        return;
    }

    if (fire > 0.0) {
        vec3 low_fire = vec3(0.85, 0.12, 0.02);
        vec3 high_fire = vec3(1.0, 0.95, 0.20);
        vec3 fire_color = mix(low_fire, high_fire, clamp(fire, 0.0, 1.0));
        FragColor = vec4(fire_color, 1.0);
        return;
    }

    if (fuel > 0.0) {
        vec3 dry_grass = vec3(0.45, 0.63, 0.22);
        vec3 dense_green = vec3(0.20, 0.74, 0.32);

        float fuel_t = clamp(fuel, 0.0, 1.0);
        vec3 color = mix(dry_grass, dense_green, fuel_t);

        // Modulación suave por elevación (solo un toque visual)
        float elev_light = 0.95 + 0.10 * elev;
        color *= elev_light;

        // Curvas de nivel muy sutiles
        float contour = smoothstep(0.42, 0.58, fract(elev * 12.0));
        color *= mix(0.97, 1.05, contour);

        FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
        return;
    }

    FragColor = vec4(0.04, 0.04, 0.04, 1.0);
}
