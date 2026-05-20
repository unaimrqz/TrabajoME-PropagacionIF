#version 330 core

// step.glsl
// Kernel de cálculo en GPU para el autómata celular de propagación del fuego.
// Implementa un modelo SIR espacialmente distribuido con efectos de viento,
// pendiente del terreno e ignición de focos secundarios (pavesas).

out vec4 FragColor;        
in vec2 TexCoords;

uniform sampler2D u_texture;
uniform vec2 u_grid_size;
uniform vec2 u_wind;
uniform float u_time;
uniform float u_pavesas_prob;
uniform float u_beta;
uniform float u_gamma;

// Generador de números pseudoaleatorios basado en funciones trigonométricas y fract.
float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233)) + u_time) * 43758.5453);
}

void main() {
    // Tamaño del paso en coordenadas de textura normalizadas [0.0, 1.0]
    vec2 px = 1.0 / u_grid_size;
    vec2 uv_coords = TexCoords;

    // Estado actual de la celda:
    // r (Fuego / Intensidad térmica [0, 1])
    // g (Elevación topográfica normalizada)
    // b (Combustible / Biomasa restante [0, 1])
    vec4 color = texture(u_texture, uv_coords);
    float fire = color.r;
    float fuel = color.b;
    float my_elev = color.g;

    // Estado I (Infected) -> Decremento de combustible (consumo por calor de llama)
    if (fire > 0.0) {
        fuel -= u_gamma;
        if (fuel <= 0.0) {
            fuel = 0.0;
            fire -= 0.1; // Extinción paulatina al agotarse la biomasa
        }
    }

    // Estado S (Susceptible) -> Análisis de contagio por vecindad física de Moore (z = 8)
    if (fire == 0.0 && fuel > 0.0) {
        float heat = 0.0;

        for (int y = -1; y <= 1; y++) {
            for (int x = -1; x <= 1; x++) {
                if (x == 0 && y == 0) {
                    continue;
                }

                vec2 offset = vec2(float(x), float(y));
                vec2 neighbor_uv = uv_coords - offset * px;
                vec4 neighbor = texture(u_texture, neighbor_uv);
                float neighbor_fire = neighbor.r;
                
                // Efecto de pendiente (convección ascendente del calor)
                float nb_elev = neighbor.g;
                float slope = my_elev - nb_elev;
                float slope_factor = max(0.0, (slope / px.x) * 2.0);

                // Efecto de la velocidad y dirección del viento (advección térmica)
                float wind_factor = max(0.0, dot(normalize(offset), u_wind));
                
                // Factor de escala espacial de Moore para corregir anisotropía geométrica
                float w_k = (x != 0 && y != 0) ? 0.70710678 : 1.0;

                // Suma acumulativa de calor recibido
                heat += neighbor_fire * w_k * (1.0 + wind_factor) * (1.0 + slope_factor);
            }
        }

        // Probabilidad microscópica de ignición con factor de escala de acoplamiento (0.1)
        float ignition_prob = clamp(heat * 0.1 * u_beta, 0.0, 1.0);
        float random_val = rand(uv_coords + fract(u_time * 0.123));
        if (random_val < ignition_prob) {
            fire = 1.0;
        }

        // Cálculo de focos secundarios no locales (pavesas) transportados a sotavento
        if (u_pavesas_prob > 1e-5) {
            float w_len = length(u_wind);
            
            if (w_len > 0.1) {
                vec2 wind_dir = normalize(u_wind);
                
                // Semillas aleatorias diferenciadas por desplazamiento
                float r1 = rand(uv_coords + vec2(1.23, 4.56)); // Ángulo disperso
                float r2 = rand(uv_coords + vec2(7.89, 1.23)); // Distancia de salto
                float r3 = rand(uv_coords + vec2(3.45, 6.78)); // Probabilidad de ignición
                
                // Cono de dispersión angular de pavesas de ±30 grados
                float angle_noise = (r1 - 0.5) * 1.05;
                float cos_a = cos(angle_noise);
                float sin_a = sin(angle_noise);
                vec2 scatter_dir = vec2(
                    wind_dir.x * cos_a - wind_dir.y * sin_a,
                    wind_dir.x * sin_a + wind_dir.y * cos_a
                );
                
                // Salto aleatorio de la pavesa entre el 15% y el 55% de la dimensión lineal de la red
                float dist_noise = 0.15 + (r2 * 0.4); 
                vec2 upwind_uv = uv_coords - (scatter_dir * dist_noise);
                
                if (upwind_uv.x >= 0.0 && upwind_uv.x <= 1.0 && upwind_uv.y >= 0.0 && upwind_uv.y <= 1.0) {
                    vec4 upwind_cell = texture(u_texture, upwind_uv);
                    
                    // Condición física: celda a barlovento con fuego activo y suficiente biomasa disponible
                    if (upwind_cell.r > 0.98 && upwind_cell.b > 0.15) {
                        if (r3 < u_pavesas_prob) {
                            fire = 0.1; // Inicio de foco secundario
                        }
                    }
                }
            }
        }
    }

    fire = clamp(fire, 0.0, 1.0);
    fuel = clamp(fuel, 0.0, 1.0);

    FragColor = vec4(fire, my_elev, fuel, 1.0);
}
