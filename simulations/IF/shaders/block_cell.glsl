// block_cell.glsl
// Este shader se utiliza para bloquear una célula específica en la cuadrícula. 
// Cuando el usuario hace clic en una célula, esta se bloquea (se vuelve negra)
// y se mantiene su estado en la textura de estado. Este shader se ejecuta como 
// parte del proceso de renderizado, y solo modifica el color de la célula
// seleccionada, dejando el resto de la cuadrícula sin cambios.

#version 330 core

out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D u_state_texture;
uniform vec2 u_grid_size;
uniform ivec2 u_cell_coord;

void main() {
    ivec2 frag = ivec2(floor(TexCoords * u_grid_size));
    vec4 current = texture(u_state_texture, TexCoords);

    if (all(equal(frag, u_cell_coord))) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    FragColor = current;
}
